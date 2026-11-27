"""Match four schools' attended players to ESPN historical game/roster identities."""
from audit_player_portraits import load,save,api,espn_image,probe,probe_many
from collections import defaultdict,Counter
import re,unicodedata

SCHOOLS={'NCS':'NC State','WFU':'Wake Forest','DEL':'Delaware','WKU':'Western Kentucky'}
BASE='https://site.api.espn.com/apis/site/v2/sports/football/college-football'
REG='cfb/data/player_portraits.json'
REPORT='cfb/data/espn_portrait_audit.json'
def norm(s):
    s=unicodedata.normalize('NFKD',str(s)).encode('ascii','ignore').decode().lower().strip()
    # School gamebooks sometimes put the suffix before the name.
    s=re.sub(r'^(jr\.?|sr\.?|ii|iii|iv),\s*(.+)$',r'\2 \1',s)
    s=s.replace('"duke"','duke')
    return re.sub(r'[^a-z0-9]','',s)
def names(s):
    n=norm(s)
    # Removing suffix is allowed only if team+game/roster still identifies exactly one athlete.
    return {n,re.sub(r'(?:iii|ii|iv|jr|sr)$','',n)}
def teammatch(team,full):
    return norm(team.get('displayName',''))==norm(full) or norm(team.get('location',''))==norm(full.rsplit(' ',1)[0])
rows=load('cfb/data/player_stats.json',[])
games=load('cfb/data/games.json',[])
reg=load(REG,{})
people={str(r['athlete_id']):{'name':r['player'],'school':r['team']} for r in rows if r['team'] in SCHOOLS}
hits=defaultdict(list);notes=[]
def ingest(athletes,school,source,priority,allowed):
    candidates=defaultdict(set)
    for a in athletes:
        aid=str(a.get('id',''))
        if not aid.isdigit():continue
        for name in (a.get('displayName'),a.get('fullName'),a.get('shortName')):
            if name:
                for n in names(name):candidates[n].add(aid)
    for cid in allowed:
        p=people[cid]
        if p['school']!=school:continue
        ids=set().union(*(candidates.get(n,set()) for n in names(p['name'])))
        if len(ids)==1:hits[cid].append((priority,next(iter(ids)),source))
        elif len(ids)>1:notes.append({'id':cid,'source':source,'ambiguous_ids':sorted(ids)})
def walk_athletes(obj):
    if isinstance(obj,dict):
        if 'athlete' in obj and isinstance(obj['athlete'],dict):yield obj['athlete']
        if str(obj.get('id','')).isdigit() and ('fullName' in obj or 'displayName' in obj) and ('position' in obj or 'headshot' in obj or 'jersey' in obj):yield obj
        for k,v in obj.items():
            if k!='athlete':yield from walk_athletes(v)
    elif isinstance(obj,list):
        for v in obj:yield from walk_athletes(v)
for g in games:
    schools=[g.get(side+'_abbr') for side in ('away','home')]
    if not any(s in SCHOOLS for s in schools):continue
    allowed={str(r['athlete_id']) for r in rows if r['game_id']==g['id'] and r['team'] in SCHOOLS}
    try:
        event=str(g.get('espn_event_id') or '')
        if not event:
            board=api(BASE+'/scoreboard',params={'dates':g['date'].replace('-',''),'groups':80,'limit':1000})
            matches=[]
            for e in board.get('events',[]):
                sides={x['homeAway']:x for x in e.get('competitions',[{}])[0].get('competitors',[])}
                if all(norm(sides.get(side,{}).get('team',{}).get('displayName',''))==norm(g[side]) and str(sides[side].get('score'))==str(g[side+'_score']) for side in ('home','away')):matches.append(str(e['id']))
            if len(matches)!=1:raise ValueError('No unique matching ESPN scoreboard event')
            event=matches[0]
        source=BASE+'/summary?event='+event
        summary=api(source)
        sides={x['homeAway']:x for x in summary['header']['competitions'][0]['competitors']}
        if not all(norm(sides[side]['team']['displayName'])==norm(g[side]) and str(sides[side].get('score'))==str(g[side+'_score']) for side in ('home','away')):raise ValueError('ESPN event identity or final score mismatch')
        for side in ('home','away'):
            school=g[side+'_abbr']
            if school not in SCHOOLS:continue
            teamid=str(sides[side]['team']['id'])
            blocks=[]
            for key in ('boxscore','rosters'):
                block=summary.get(key,{})
                candidates=block.get('players',[]) if isinstance(block,dict) else block
                for entry in candidates:
                    if str(entry.get('team',{}).get('id'))==teamid:blocks.append(entry)
            ingest(list(walk_athletes(blocks)),school,source,0,allowed)
            roster_url=BASE+'/teams/'+teamid+'/roster?season='+str(g['season'])
            try:
                roster=api(roster_url)
                # Endpoint is anchored to the verified game team and season.
                ingest(list(walk_athletes(roster.get('athletes',[]))),school,roster_url,1,allowed)
            except Exception as e:notes.append({'school':school,'source':roster_url,'error':str(e)})
    except Exception as e:notes.append({'game':g['id'],'error':str(e)})
resolved={};missing=[]
for cid,p in people.items():
    if cid in reg:continue
    choices=hits[cid]
    if not choices:missing.append({'id':cid,**p,'reason':'No verified ESPN identity'});continue
    best=min(c[0] for c in choices);choices=[c for c in choices if c[0]==best]
    if len({c[1] for c in choices})!=1:
        missing.append({'id':cid,**p,'reason':'Conflicting ESPN identities'});continue
    resolved[cid]=sorted(choices)[0]
# Prevent an ESPN athlete ID from matching two distinct archive IDs in this audit.
id_counts=Counter(v[1] for v in resolved.values())
urls={cid:espn_image('cfb',v[1]) for cid,v in resolved.items() if id_counts[v[1]]==1}
sentinels={probe(espn_image('cfb',x))[1] for x in ('0','999999999')}
results=probe_many(list(set(urls.values())))
hashcounts=Counter(h for status,h in results.values() if status=='image')
added=[]
for cid,(priority,aid,source) in resolved.items():
    if cid not in urls:
        missing.append({'id':cid,**people[cid],'espn_id':aid,'reason':'Shared ESPN ID needs identity review'});continue
    u=urls[cid];status,h=results[u]
    if status=='image' and h not in sentinels and hashcounts[h]==1:
        reg[cid]={'url':u,'espn_id':aid,'name':people[cid]['name'],'school':people[cid]['school'],'source':source,'provider':'espn'}
        added.append(cid)
    else:missing.append({'id':cid,**people[cid],'espn_id':aid,'source':source,'reason':'Unavailable or generic ESPN image','probe_status':status})
by_school={}
for school,name in SCHOOLS.items():
    ids={cid for cid,p in people.items() if p['school']==school}
    by_school[name]={'targeted':len(ids),'registered':len(ids&set(reg)),'missing':len(ids-set(reg))}
save(REG,reg)
save(REPORT,{'targeted':len(people),'registered':len(set(people)&set(reg)),'added':added,'missing':missing,'schools':by_school,'notes':notes})
print(by_school)
