"""Verify NFL alumni portrait identities and use college images only as fallback."""
from audit_player_portraits import load,save,api,espn_image,probe,probe_many
from collections import defaultdict
import re,unicodedata,csv,io
from audit_player_portraits import get
REG='cfb/data/nfl_alumni_portraits.json'
cross=load('cfb/data/nfl_crosswalk.json',[])
rows=load('cfb/data/player_stats.json',[])
college=load('cfb/data/player_portraits.json',{})
people={str(r['athlete_id']):r['player'] for r in rows}
reg=load(REG,{})
def norm(s):
    return re.sub(r'[^a-z0-9]','',unicodedata.normalize('NFKD',str(s)).encode('ascii','ignore').decode().lower())
# Roster IDs are candidates only, verified against ESPN athlete metadata before use.
manual={'cfb-usd-michael-bandy':'4034704','cfb-ucd-daniel-whelan':'4248789','cfb-usd-dalton-kincaid':'4385690'}
ids=defaultdict(set)
for r in cross:
    cid=r['athlete_id']
    if cid in college:ids[cid].add(str(college[cid].get('espn_id','')))
    if cid in manual:ids[cid].add(manual[cid])
# NFLverse retains historical NFL roster identifiers, including former players.
for season in (2026,2025,2024,2023,2022,2021,2019,2018):
    if all(ids[r['athlete_id']] for r in cross):break
    try:
        url=f'https://github.com/nflverse/nflverse-data/releases/download/rosters/roster_{season}.csv'
        response=get(url);response.raise_for_status()
        for row in csv.DictReader(io.StringIO(response.text)):
            name=norm(row.get('full_name') or row.get('football_name') or '')
            aid=str(row.get('espn_id') or '').split('.')[0]
            if not aid.isdigit():continue
            for r in cross:
                cid=r['athlete_id']
                if name==norm(people.get(cid,'')):ids[cid].add(aid)
    except Exception as e:print('Roster lookup:',season,str(e))
# Also use IDs from the archive's own NFL stat records when an exact name agrees.
for row in load('nfl/data/player_stats.json',[]):
    aid=str(row.get('athlete_id') or row.get('player_id') or '')
    if not aid.isdigit():continue
    for r in cross:
        cid=r['athlete_id']
        if norm(row.get('player') or row.get('name') or '')==norm(people.get(cid,'')):ids[cid].add(aid)
candidates={};notes=[]
for r in cross:
    cid=r['athlete_id'];name=people.get(cid,'')
    if not name:continue
    valid=[]
    for aid in ids[cid]:
        if not aid.isdigit():continue
        source='https://site.web.api.espn.com/apis/common/v3/sports/football/nfl/athletes/'+aid
        try:
            d=api(source);a=d.get('athlete',d)
            if str(a.get('id',''))==aid and norm(name) in {norm(a.get(k,'')) for k in ('displayName','fullName','shortName')}:
                valid.append((aid,source))
        except Exception as e:notes.append({'id':cid,'espn_id':aid,'error':str(e)})
    if len(set(a for a,_ in valid))==1:
        aid,source=valid[0];candidates[cid]=(aid,source,espn_image('nfl',aid))
    elif len(valid)>1:notes.append({'id':cid,'reason':'Multiple ESPN identities'})
sentinels={probe(espn_image('nfl',i))[1] for i in ('0','999999999')}
results=probe_many(list({v[2] for v in candidates.values()}))
owners=defaultdict(set)
for cid,(_,_,u) in candidates.items():
    status,h=results[u]
    if status=='image':owners[h].add(cid)
for cid,(aid,source,u) in candidates.items():
    status,h=results[u]
    if status=='image' and h not in sentinels and owners[h]=={cid}:reg[cid]={'url':u,'espn_id':aid,'name':people[cid],'source':source,'provider':'espn-nfl'}
missing=[{'id':r['athlete_id'],'name':people.get(r['athlete_id']),'college_fallback':r['athlete_id'] in college} for r in cross if r['athlete_id'] not in reg]
save(REG,reg)
save('cfb/data/nfl_alumni_portrait_audit.json',{'targeted':len(cross),'registered':len(set(reg)&{r['athlete_id'] for r in cross}),'missing':missing,'notes':notes})
print('NFL portraits:',len(reg),'missing:',missing)
