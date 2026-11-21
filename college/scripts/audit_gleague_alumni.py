import csv, json, re, unicodedata
from pathlib import Path
from collections import defaultdict, Counter
import requests
from bs4 import BeautifulSoup

ROOT=Path(__file__).resolve().parents[1]
URL='https://basketball.realgm.com/gleague/players/Historical'
def norm(s):
    return re.sub(r'[^a-z0-9]', '', unicodedata.normalize('NFKD',s).encode('ascii','ignore').decode().lower())
def loose(s):
    return norm(re.sub(r'\b(?:jr|sr|ii|iii|iv|v)\.?$', '', s, flags=re.I).strip())
def school(s):
    return norm(s.replace('State University','State').replace('University of ','').replace(' University',''))
rows=json.loads((ROOT/'data/player_boxscores_espn.json').read_text())
nba={x['player_id'] for x in json.loads((ROOT/'data/nba_crosswalk.json').read_text()) if x['category']=='nba'}
players={}
for r in rows:
    p=players.setdefault(r['player_id'],dict(player_id=r['player_id'],name=r['player'],schools=set(),dates=set()))
    p['schools'].add(r['team']);p['dates'].add(r['date'])
response=requests.get(URL,headers={'User-Agent':'Mozilla/5.0'},timeout=60)
response.raise_for_status()
soup=BeautifulSoup(response.text,'html.parser')
index=defaultdict(list)
total=0
for tr in soup.select('table tr'):
    t=tr.find_all('td')
    if len(t)<8: continue
    a=t[0].find('a',href=True)
    if not a: continue
    try: gp=int(t[5].get_text(strip=True).replace(',',''))
    except ValueError: continue
    if gp<1: continue
    name=a.get_text(strip=True)
    from urllib.parse import urljoin
    e=dict(name=name,gp=gp,teams=t[4].get_text(' ',strip=True),school=t[6].get_text(' ',strip=True),draft=t[7].get_text(' ',strip=True),source=urljoin(URL,a['href']))
    index[loose(name)].append(e);total+=1
if total<2000: raise RuntimeError(f'Incomplete historical table: {total} rows')
out=[]
for pid,p in sorted(players.items(),key=lambda a:a[1]['name'].lower()):
    candidates=index[loose(p['name'])]
    exact=[c for c in candidates if norm(c['name'])==norm(p['name'])]
    same=[c for c in exact if school(c['school']) in {school(s) for s in p['schools']}]
    status='school_and_name_match' if len(same)==1 and len(exact)==1 else 'identity_review' if candidates else 'not_found'
    out.append(dict(player_id=pid,name=p['name'],schools=sorted(p['schools']),first_seen=min(p['dates']),last_seen=max(p['dates']),existing_nba=pid in nba,status=status,candidates=candidates))
dest=ROOT/'reports/gleague-audit'
dest.mkdir(parents=True,exist_ok=True)
summary=dict(archive_players=len(players),archive_games=len({r['game_id'] for r in rows}),source_rows=total,status_counts=dict(Counter(p['status'] for p in out)),source=URL)
(dest/'audit.json').write_text(json.dumps(dict(summary=summary,players=out),indent=2))
with (dest/'matches.csv').open('w',newline='') as f:
    w=csv.writer(f);w.writerow(['player_id','name','schools','existing_nba','status','candidate_name','games','teams','source_school','draft','source'])
    for p in out:
        for c in p['candidates']:
            w.writerow([p['player_id'],p['name'],'; '.join(p['schools']),p['existing_nba'],p['status'],c['name'],c['gp'],c['teams'],c['school'],c['draft'],c['source']])
print(json.dumps(summary))
for p in out:
    if p['candidates']: print(p['name'],p['status'],p['existing_nba'],[(c['name'],c['gp'],c['school']) for c in p['candidates']])
