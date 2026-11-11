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
OFFICIAL_OVERRIDES = {
    (2025, 'texas am'): {'url': 'https://12thman.com/documents/download/2025/3/21/TAMU_Stat_Pack.pdf', 'pts': ('Wade Taylor IV', 'espn:4683833', 15.7), 'reb': ('Andersson Garcia', 'espn:4702431', 6.2), 'ast': ('Wade Taylor IV', 'espn:4683833', 4.3)},
    (2025, 'michigan'): {'url': 'https://mgoblue.com/sports/mens-basketball/stats/2024-25', 'pts': ('Vladislav Goldin', 'espn:4700818', 16.6), 'reb': ('Danny Wolf', 'espn:5107173', 9.7), 'ast': ('Tre Donaldson', 'espn:4837356', 4.1)},
    (2025, 'louisville'): {'url': 'https://gocards.com/sports/mens-basketball/stats/2024-25', 'pts': ('Terrence Edwards Jr.', 'espn:4702766', 16.7), 'reb': ("J'Vonne Hadley", 'espn:4702784', 7.3), 'ast': ('Chucky Hepburn', 'espn:4590360', 5.8)},
    (2025, 'duke'): {'url': 'https://goduke.com/sports/mens-basketball/stats/2024-25', 'pts': ('Cooper Flagg', 'espn:5041939', 19.2), 'reb': ('Cooper Flagg', 'espn:5041939', 7.5), 'ast': ('Cooper Flagg', 'espn:5041939', 4.2)},
    (2025, 'auburn'): {'url': 'https://auburntigers.com/sports/mens-basketball/stats/season/2024-25', 'pts': ('Johni Broome', 'espn:4433569', 18.6), 'reb': ('Johni Broome', 'espn:4433569', 10.8), 'ast': ('Tahaad Pettiford', 'espn:4873089', 3.0)},
    (2025, 'arkansas'): {'url': 'https://arkansasrazorbacks.com/stats/mbb/2024-25/teamcume.htm', 'pts': ('Adou Thiero', 'espn:5060631', 15.1), 'reb': ('Adou Thiero', 'espn:5060631', 5.8), 'ast': ('Boogie Fland', 'official:arkansas:boogie-fland', 5.1)},
    (2024, 'san diego state'): {'url': 'https://goaztecs.com/mens-basketball-archives', 'pts': ('Jaedon LeDee', 'espn:4397237', 21.4), 'reb': ('Jaedon LeDee', 'espn:4397237', 8.4), 'ast': ('Darrion Trammell', 'espn:4702011', 3.2)},
    (2024, 'north carolina state'): {'url': 'https://gopack.com/sports/mens-basketball/stats/2023-24', 'pts': ('DJ Horne', 'espn:4431993', 16.9), 'reb': ('Mohamed Diarra', 'espn:5105541', 7.8), 'ast': ("Michael O'Connell", 'espn:4683635', 3.2)},
    (2024, 'north carolina'): {'url': 'https://goheels.com/sports/mens-basketball/stats/2023-24', 'pts': ('RJ Davis', 'espn:4433176', 21.2), 'reb': ('Armando Bacot', 'espn:4431674', 10.3), 'ast': ('Elliot Cadeau', 'espn:4869764', 4.1)},
    (2024, 'mississippi state'): {'url': 'https://hailstate.com/sports/mens-basketball/stats/2023-24', 'pts': ('Josh Hubbard', 'espn:4895740', 17.1), 'reb': ('Tolu Smith', 'espn:4397882', 8.1), 'ast': ('Cameron Matthews', 'espn:4432394', 2.9)},
    (2024, 'michigan state'): {'url': 'https://msuspartans.com/sports/mens-basketball/stats/2023-24', 'pts': ('Tyson Walker', 'espn:4432129', 18.4), 'reb': ('Malik Hall', 'espn:4592693', 5.7), 'ast': ('AJ Hoggard', 'espn:4432206', 5.2)},
    (2023, 'utah state'): {'url': 'https://utahstateaggies.com/sports/mens-basketball/roster/steven-ashworth/9316', 'pts': ('Steven Ashworth', 'espn:4701991', 16.2), 'reb': ('Daniel Akin', 'official:utah-state:daniel-akin', 6.8), 'ast': ('Steven Ashworth', 'espn:4701991', 4.5)},
    (2023, 'ucla'): {'url': 'https://uclabruins.com/sports/mens-basketball/stats/season/2022-23', 'pts': ('Jaime Jaquez Jr.', 'espn:4432848', 17.8), 'reb': ('Jaime Jaquez Jr.', 'espn:4432848', 8.2), 'ast': ('Tyger Campbell', 'espn:4397128', 5.0)},
    (2023, 'san diego state'): {'url': 'https://goaztecs.com/sports/mens-basketball/roster/player/darrion-trammell', 'pts': ('Matt Bradley', 'espn:4397049', 12.6), 'reb': ('Nate Mensah', 'espn:4397371', 5.9), 'ast': ('Lamont Butler', 'espn:4433183', 3.2)},
    (2022, 'san diego state'): {'url': 'https://goaztecs.com/sports/mens-basketball/stats/season/2021-22', 'pts': ('Matt Bradley', 'espn:4397049', 16.9), 'reb': ('Nate Mensah', 'espn:4397371', 6.9), 'ast': ('Trey Pulliam', 'espn:4593083', 3.4)},
    (2022, 'gonzaga'): {'url': 'https://gozags.com/sports/mens-basketball/stats/2021-22', 'pts': ('Drew Timme', 'espn:4431695', 18.4), 'reb': ('Chet Holmgren', 'espn:4433255', 9.9), 'ast': ('Andrew Nembhard', 'espn:4395712', 5.8)},
    (2022, 'colorado state'): {'url': 'https://csurams.com/sports/mens-basketball/stats/2021-22', 'pts': ('David Roddy', 'espn:4593041', 19.2), 'reb': ('David Roddy', 'espn:4593041', 7.6), 'ast': ('Isaiah Stevens', 'espn:4432117', 4.7)},
    (2022, 'cal state fullerton'): {'url': 'https://fullertontitans.com/sports/mens-basketball/stats/2021-22', 'pts': ('E.J. Anosike', 'espn:4279647', 16.4), 'reb': ('E.J. Anosike', 'espn:4279647', 8.9), 'ast': ('Damari Milstead', 'espn:4280171', 3.2)},
    (2019, 'nevada'): {'url': 'https://nevadawolfpack.com/sports/mens-basketball/stats/2018-19', 'pts': ('Caleb Martin', 'espn:3138160', 19.2), 'reb': ('Jordan Caroline', 'espn:3148992', 9.6), 'ast': ('Cody Martin', 'espn:3138161', 4.9)},
    (2019, 'gonzaga'): {'url': 'https://gozags.com/sports/mens-basketball/stats/2018-19', 'pts': ('Rui Hachimura', 'espn:4066648', 19.7), 'reb': ('Brandon Clarke', 'espn:3906665', 8.6), 'ast': ('Josh Perkins', 'espn:3155941', 6.3)},
    (2018, 'san diego state'): {'url': 'https://goaztecs.com/mens-basketball-archives', 'pts': ('Malik Pope', 'espn:3137714', 12.8), 'reb': ('Jalen McDaniels', 'espn:4066731', 7.5), 'ast': ('Trey Kell', 'espn:3137712', 4.1)},
    (2018, 'gonzaga'): {'url': 'https://gozags.com/sports/mens-basketball/stats/2017-18', 'pts': ('Johnathan Williams', 'espn:66260', 13.4), 'reb': ('Johnathan Williams', 'espn:66260', 8.5), 'ast': ('Josh Perkins', 'espn:3155941', 5.3)},
    (2025, 'unc wilmington'): {
        'url': 'https://uncwsports.com/sports/mens-basketball/stats/2024-25',
        'pts': ('Donovan Newby', 'espn:4702932', 14.4),
        'reb': ('Sean Moore', 'espn:5106587', 6.5),
        'ast': ('Donovan Newby', 'espn:4702932', 3.5),
    },
    (2025, 'north carolina'): {
        'url': 'https://goheels.com/sports/mens-basketball/stats/2024-25',
        'pts': ('RJ Davis', 'espn:4433176', 17.2),
        'reb': ('Ven-Allen Lubin', 'espn:4684799', 5.5),
        'ast': ('Elliot Cadeau', 'espn:4869764', 6.2),
    },
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
        futures = {pool.submit(season_leaders, r['season'], r['team_id'], r['_witnessed_ids']): r for r in records if (r['season'], r['school']) not in OFFICIAL_OVERRIDES}
        for future in as_completed(futures):
            record = futures[future]
            record['leaders'] = future.result()
            record['leaders_verified'] = False
    for record in records:
        override = OFFICIAL_OVERRIDES.get((record['season'], record['school']))
        if override:
            record['leaders'] = {
                stat: {'name': name, 'id': player_id, 'average': value,
                       'in_archive': player_id in record['_witnessed_ids'],
                       'source_url': override['url']}
                for stat, (name, player_id, value) in ((k, v) for k, v in override.items() if k != 'url')
            }
            record['leaders_verified'] = True
    for record in records:
        del record['_witnessed_ids']
    output = {'source': 'mattgennarelli/bracket-brain historical results (Wikipedia/Sports Reference derived)',
              'coverage': '2008–2026 seasons with source game results; 2020 had no tournament',
              'region_status': 'verified where provided by bracket data',
              'leader_source': 'Audited final full-season school cumulative statistics and player season records', 'teams': records}
    destination = ROOT / 'data/ncaa_tournament.json'
    destination.write_text(json.dumps(output, indent=2) + '\n')
    print(f'{len(records)} qualifying team-seasons, {sum(len(r["games"]) for r in records)} attended team-games')

if __name__ == '__main__':
    main()
