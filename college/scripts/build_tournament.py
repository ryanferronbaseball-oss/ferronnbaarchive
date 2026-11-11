"""Build attended NCAA Tournament team-seasons from verified game and bracket CSVs.

Usage: python college/scripts/build_tournament.py /path/to/bracket-brain/data/results_all.json
The upstream result collection covers 2008–2026 excluding the canceled 2020 tournament.
"""
import csv
import json
import re
import sys
import urllib.request
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ALIASES = {
    'uconn': 'connecticut', 'unc': 'north carolina', 'nc state': 'north carolina state',
    'ole miss': 'mississippi', 'pitt': 'pittsburgh', 'saint marys': 'saint marys',
    'st marys': 'saint marys', 'st marys ca': 'saint marys',
    'miami fl': 'miami', 'miami florida': 'miami', 'southern california': 'usc',
    'uc irvine': 'uc irvine', 'california irvine': 'uc irvine',
    'brigham young': 'byu', 'virginia commonwealth': 'vcu',
    'florida atlantic': 'fau', 'loyola chicago': 'loyola chicago',
    'saint peters': 'saint peters', 'st peters': 'saint peters',
    'college of charleston': 'charleston', 'charleston cofc': 'charleston',
    'texas a m': 'texas am', 'texas a and m': 'texas am',
}

def norm(value):
    value = re.sub(r'[^a-z0-9 ]+', ' ', value.lower().replace('&', ' and '))
    value = ' '.join(value.split()).replace('saint ', 'st ')
    return ALIASES.get(value, value)

def slug(value):
    return re.sub(r'[^a-z0-9]+', '-', value.lower()).strip('-')

def season_leaders(year, team_id, witnessed_ids):
    url = (f'https://site.web.api.espn.com/apis/common/v3/sports/basketball/'
           f'mens-college-basketball/teams/{team_id}/roster?season={year}')
    request = urllib.request.Request(url, headers={'User-Agent': 'CourtsideArchive/1.0'})
    with urllib.request.urlopen(request, timeout=25) as response:
        roster = json.load(response)
    if int(roster.get('season', {}).get('year', 0)) != year:
        raise ValueError(f'Wrong roster year: {year}, team {team_id}')
    athletes = []
    for group in roster.get('positionGroups', []):
        for athlete in group.get('athletes', []):
            # ESPN's historical roster feed can contain transferred players whose
            # season averages belong to a different school (e.g. 2025 Jaylen Blakes).
            if str(team_id) not in {str(t.get('id')) for t in athlete.get('teams', [])}:
                continue
            values = {s['name']: s.get('value') for c in athlete.get('statistics', {}).get('splits', {}).get('categories', []) for s in c.get('stats', [])}
            if all(isinstance(values.get(key), (float, int)) for key in ('avgPoints', 'avgRebounds', 'avgAssists')):
                athletes.append((athlete, values))
    if not athletes:
        raise ValueError(f'No season player averages: {year}, team {team_id}')
    leaders = {}
    for stat, key in [('pts', 'avgPoints'), ('reb', 'avgRebounds'), ('ast', 'avgAssists')]:
        athlete, values = max(athletes, key=lambda a: float(a[1][key]))
        player_id = 'espn:' + str(athlete['id'])
        leaders[stat] = {'name': athlete['displayName'], 'id': player_id,
                         'average': round(float(values[key]), 1),
                         'in_archive': player_id in witnessed_ids,
                         'source_url': url}
    return leaders

def main():
    bracket_file = Path(sys.argv[1])
    with (ROOT / 'data/games.csv').open(newline='') as f:
        games = list(csv.DictReader(f))
    player_logs = json.loads((ROOT / 'data/player_boxscores_espn.json').read_text())
    logs_by_game_team = defaultdict(list)
    for log in player_logs:
        logs_by_game_team[(str(log['game_id']), str(log['team_id']))].append(log)
    coach_rules = json.loads((ROOT.parent / 'coach-history/data/verified-assignments.json').read_text())['rules']
    coach_rules += json.loads((ROOT.parent / 'coach-history/data/college-basketball-coach-assignments.json').read_text())['rules']
    coach_rules = [r for r in coach_rules if r['sport'] == 'College Basketball']
    grouped = defaultdict(list)
    for game in games:
        season = int(game['date'][:4]) + (int(game['date'][5:7]) >= 7)
        for side in ('away', 'home'):
            grouped[(season, norm(game[side]))].append({
                'id': game['id'], 'date': game['date'], 'opponent': game['home' if side == 'away' else 'away'],
                'team_id': game.get(side + '_team_id', ''),
            })
    winners = defaultdict(dict)
    entrants = defaultdict(dict)
    source = json.loads(bracket_file.read_text())
    # This source stores exactly the 63 main-bracket games per season, in season order.
    assert len(source['games']) == len(source['years']) * 63, 'Unexpected source year grouping'
    for index, year in enumerate(source['years']):
        for row in source['games'][index*63:(index+1)*63]:
            rnd = int(row['round'])
            for side in ('a', 'b'):
                name = norm(row['team_' + side])
                entry = entrants[year].setdefault(name, {'seed': int(row['seed_' + side]), 'max_round': 64, 'region': None})
                entry['max_round'] = min(entry['max_round'], rnd)
                # Historical result rows can carry incorrect region labels; do not trust them.
            winner = norm(row['winner'])
            winners[year][winner] = min(winners[year].get(winner, 64), rnd)
    for year in source['years']:
        bracket_path = bracket_file.parent / f'bracket_{year}.json'
        if not bracket_path.exists():
            continue
        bracket = json.loads(bracket_path.read_text())
        for region, teams in bracket.get('regions', {}).items():
            for team in teams:
                entry = entrants[year].get(norm(team['team']))
                if entry and entry['seed'] == int(team['seed']):
                    entry['region'] = region
    records = []
    for (year, school), seen in sorted(grouped.items(), reverse=True):
        bracket = entrants.get(year, {}).get(school)
        if not bracket:
            continue
        last = bracket['max_round']
        result = ('National Champion' if last == 2 and winners[year].get(school) == 2 else
                  'National Finalist' if last == 2 else 'Final Four' if last == 4 else
                  'Elite Eight' if last == 8 else 'Sweet 16' if last == 16 else
                  'Round of 32' if last == 32 else 'First Round')
        team_name = next((g[side] for g in games for side in ('away','home') if norm(g[side]) == school), school.title())
        candidate_coaches = []
        for seen_game in seen:
            rule_matches = {r['coach'] for r in coach_rules if norm(r['team']) == school and r['from'] <= seen_game['date'] <= r['to']}
            if len(rule_matches) == 1:
                candidate_coaches.extend(rule_matches)
        coach = max(set(candidate_coaches), key=candidate_coaches.count) if candidate_coaches else None
        witnessed_ids = set()
        for seen_game in seen:
            for log in logs_by_game_team[(str(seen_game['id']), str(seen_game['team_id']))]:
                if log.get('minutes') in (None, '', '--'):
                    continue
                witnessed_ids.add(str(log['player_id']))
        records.append({'season': year, 'school': school, 'name': team_name,
                        'team_id': seen[0]['team_id'], 'seed': bracket['seed'], 'region': bracket['region'],
                        'result': result, 'coach': {'name': coach, 'id': slug(coach)} if coach else None,
                        'leaders': {}, '_witnessed_ids': witnessed_ids,
                        'games': sorted(seen, key=lambda x: (x['date'], int(x['id'])))})
    with ThreadPoolExecutor(max_workers=7) as pool:
        futures = {pool.submit(season_leaders, r['season'], r['team_id'], r['_witnessed_ids']): r for r in records}
        for future in as_completed(futures):
            record = futures[future]
            record['leaders'] = future.result()
    for record in records:
        del record['_witnessed_ids']
    output = {'source': 'mattgennarelli/bracket-brain historical results (Wikipedia/Sports Reference derived)',
              'coverage': '2008–2026 seasons with source game results; 2020 had no tournament',
              'region_status': 'verified where provided by bracket data',
              'leader_source': 'ESPN historical team roster season per-game averages', 'teams': records}
    destination = ROOT / 'data/ncaa_tournament.json'
    destination.write_text(json.dumps(output, indent=2) + '\n')
    print(f'{len(records)} qualifying team-seasons, {sum(len(r["games"]) for r in records)} attended team-games')

if __name__ == '__main__':
    main()
