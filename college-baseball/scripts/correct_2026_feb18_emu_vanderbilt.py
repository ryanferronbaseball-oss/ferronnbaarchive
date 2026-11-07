#!/usr/bin/env python3
"""Replace mistaken attended Feb 17 EMU–Vanderbilt with official Feb 18 gamebook."""
import csv
import io
import json
from pathlib import Path
from import_sidearm_pilot import scrape, slug

DATA = Path(__file__).resolve().parents[1] / 'data'
ROOT = DATA.parents[1]
OLD = 'cb-2026-02-17-eastern-michigan-vanderbilt-att0379'
NEW = 'cb-2026-02-18-eastern-michigan-vanderbilt-att0379'
URL = 'https://emueagles.com/sports/baseball/stats/2026/vanderbilt/boxscore/19392'

def read(path): return json.loads(path.read_text())
def write(path, value): path.write_text(json.dumps(value, indent=2, ensure_ascii=False) + '\n')

def main():
    games = read(DATA / 'games.json')
    stats = read(DATA / 'player_stats.json')
    game, = [g for g in games if g['id'] == OLD]
    assert game['date'] == '2026-02-17' and game['home_score'] == 13
    oldrows = [s for s in stats if s['game_id'] == OLD]
    assert len(oldrows) >= 20
    game.update(id=NEW, date='2026-02-18', home_score=16, away_score=2,
                away_hits=0, home_hits=13, away_errors=0, home_errors=0,
                source_url=URL, source_attendance=3000, first_pitch_local='16:32',
                notes='Attended date corrected from February 17 to February 18 by Ryan; official seven-inning combined Vanderbilt no-hitter.',
                innings=[{'inning':i+1,'away':a,'home':h} for i,(a,h) in enumerate(zip([0,1,0,0,0,0,1],[9,4,0,0,0,3,None]))],
                pitching_decisions={'win':'Brennan Seiber','loss':'Landon Mueller','save':None})
    rows, audit = scrape(game)
    assert len(rows) >= 30
    assert {x['team'] for x in rows} == {'Eastern Michigan','Vanderbilt'}
    assert sum(x['batting']['hits'] for x in rows if x['team']=='Eastern Michigan' and 'batting' in x)==0
    for team in ('Eastern Michigan','Vanderbilt'):
        # The official batting table preserves batting-order slots and substitutions.
        batters = [r for r in rows if r['team']==team and 'batting' in r]
        slots = ([1,2,3,4,5,6,6,7,8,8,9] if team=='Eastern Michigan' else
                 [1,1,2,2,2,3,3,4,4,5,6,7,8,9,9])
        if len(batters)!=len(slots):
            raise ValueError(f'Unexpected {team} batting order: {[(r["player"],r.get("position")) for r in batters]}')
        seen={}
        for idx,(r,slot) in enumerate(zip(batters,slots)):
            r['batting_slot']=slot
            r['batting_sub_index']=seen.get(slot,0)
            r['batting_appearance_index']=idx
            seen[slot]=seen.get(slot,0)+1
        for idx,r in enumerate(x for x in rows if x['team']==team and 'pitching'):
            r['pitching_appearance_index']=idx
    for r in rows:
        if 'pitching' in r:
            for key,col in [('win','wins'),('loss','losses'),('save','saves')]:
                r['pitching'][col]=int(game['pitching_decisions'][key]==r['player'])
    assert sum(r['pitching']['wins'] for r in rows if 'pitching' in r)==1
    assert sum(r['pitching']['losses'] for r in rows if 'pitching' in r)==1
    stats=[r for r in stats if r['game_id']!=OLD]+rows
    stats.sort(key=lambda r:(r['game_id'],r['team'],r.get('batting_slot',99),r.get('batting_sub_index',99),r.get('pitching_appearance_index',99),r['player_id']))
    write(DATA/'games.json',games)
    write(DATA/'player_stats.json',stats)
    venuepath=ROOT/'venues/data/venues.json'
    venues=read(venuepath)
    def replace_in_tree(obj):
        if isinstance(obj,dict):
            for k,v in obj.items():
                if isinstance(v,str):obj[k]=v.replace(OLD,NEW)
                else:replace_in_tree(v)
            if obj.get('id')==NEW and obj.get('away')=='Eastern Michigan':
                obj.update(date='2026-02-18',awayScore=2,homeScore=16)
        elif isinstance(obj,list):
            for v in obj:replace_in_tree(v)
    replace_in_tree(venues)
    write(venuepath,venues)
    queuepath=DATA/'2026_february_january_official_source_queue.json'
    queue=read(queuepath)
    replace_in_tree(queue)
    def fix_queue(obj):
        if isinstance(obj,dict):
            if obj.get('game_id')==NEW:
                obj.update(date='2026-02-18',source=URL,result='Eastern Michigan 2, Vanderbilt 16',notes='Seven-inning run rule; Vanderbilt combined no-hitter')
            for v in obj.values():fix_queue(v)
        elif isinstance(obj,list):
            for v in obj:fix_queue(v)
    fix_queue(queue)
    write(queuepath,queue)
    decisionspath=DATA/'2026_feb_march_pitching_decisions_audit.json'
    decisions=read(decisionspath)
    replace_in_tree(decisions)
    for entry in decisions['checks']:
        if entry['game_id']==NEW:
            entry.update(source_url=URL, official_decisions={'win':'Brennan Seiber','loss':'Mueller, Landon','save':None},
                         reconciled_player_decisions=game['pitching_decisions'],source_pitchers=13)
    write(decisionspath,decisions)
    csvpath=DATA/'attendance_master_444.csv'
    content=csvpath.read_text()
    assert 'cb-attended-0379,380,2026-02-17,Eastern Michigan,Vanderbilt' in content
    csvpath.write_text(content.replace('cb-attended-0379,380,2026-02-17,Eastern Michigan,Vanderbilt',
                                       'cb-attended-0379,380,2026-02-18,Eastern Michigan,Vanderbilt'))
    script=Path(__file__).with_name('reconcile_2026_official_pitching_decisions.py')
    src=script.read_text()
    assert OLD in src
    script.write_text(src.replace(OLD,NEW))
    write(DATA/'2026_feb18_emu_vanderbilt_correction_audit.json', audit)
    print('PASS replaced Feb17 with Feb18',len(oldrows),'old rows ->',len(rows),'official rows')

if __name__=='__main__':main()
