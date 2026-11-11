"""Build attended NCAA Tournament team-seasons from verified game and bracket CSVs.

Usage: python college/scripts/build_tournament.py /path/to/bracket-brain/data/results_all.json
The upstream result collection covers 2008–2026 excluding the canceled 2020 tournament.
"""
import csv
import json
import re
import sys
from collections import defaultdict
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

def main():
    bracket_file = Path(sys.argv[1])
    with (ROOT / 'data/games.csv').open(newline='') as f:
        games = list(csv.DictReader(f))
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
        records.append({'season': year, 'school': school, 'name': next((g[side] for g in games for side in ('away','home') if norm(g[side]) == school), school.title()),
                        'team_id': seen[0]['team_id'], 'seed': bracket['seed'], 'region': bracket['region'],
                        'result': result, 'games': sorted(seen, key=lambda x: (x['date'], int(x['id'])))})
    output = {'source': 'mattgennarelli/bracket-brain historical results (Wikipedia/Sports Reference derived)',
              'coverage': '2008–2026 seasons with source game results; 2020 had no tournament',
              'region_status': 'verified where provided by bracket data', 'teams': records}
    destination = ROOT / 'data/ncaa_tournament.json'
    destination.write_text(json.dumps(output, indent=2) + '\n')
    print(f'{len(records)} qualifying team-seasons, {sum(len(r["games"]) for r in records)} attended team-games')

if __name__ == '__main__':
    main()
