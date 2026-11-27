"""Match four schools' attended players to ESPN historical game/roster identities."""
from audit_player_portraits import load,save,api,espn_image,probe,probe_many
from collections import defaultdict,Counter
import re,unicodedata

SCHOOLS={'NCS':'NC State','WFU':'Wake Forest','DEL':'Delaware','WKU':'Western Kentucky'}
BASE='https://site.api.espn.com/apis/site/v2/sports/football/college-football'
REG='cfb/data/player_portraits.json'
REPORT='cfb/data/espn_portrait_recovery.json'
def norm(s):
    s=unicodedata.normalize('NFKD',str(s)).encode('ascii','ignore').decode().lower().strip()
    # School gamebooks sometimes put the suffix before the name.
    s=re.sub(r'^(jr\.?|sr\.?|ii|iii|iv),\s*(.+)$',r'\2 \1',s)
    s=s.replace('"duke"','duke')
    return re.sub(r'[^a-z0-9]','',s)
def names(s):
    n=norm(s)
    # Removing suffix is allowed only if team+game/roster still identifies exactly one athlete.
    result={n,re.sub(r'(?:iii|ii|iv|jr|sr)
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
        if not all(norm(sides[side]['team']['displayName'])==norm(g[side]) and str(sides[side].get('score'))==str(g[side+'_score']) for side in ('home','away')):
            notes.append({'game':g['id'],'espn_sides':{side:{'name':sides[side]['team'].get('displayName'),'score':sides[side].get('score')} for side in ('home','away')}})
            raise ValueError('ESPN event identity or final score mismatch')
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
# Independently verify each school identity and query the attended-season roster,
# even if the historical scoreboard event cannot be matched.
team_ids={'NCS':'152','WFU':'154','DEL':'48','WKU':'98'}
for school,teamid in team_ids.items():
    school_games=[g for g in games if school in (g.get('home_abbr'),g.get('away_abbr'))]
    for g in school_games:
        side='home' if g.get('home_abbr')==school else 'away'
        allowed={str(r['athlete_id']) for r in rows if r['game_id']==g['id'] and r['team']==school}
        try:
            team=api(BASE+'/teams/'+teamid).get('team',{})
            # Require the ESPN school location, not a mascot-only or approximate match.
            expected={'NCS':{'ncstate','northcarolinastate'},'WFU':{'wakeforest'},'DEL':{'delaware'},'WKU':{'westernkentucky','wku'}}[school]
            if norm(team.get('location','')) not in expected and norm(team.get('displayName',''))!=norm(g[side]):
                raise ValueError('Team identity mismatch: '+str(team.get('displayName')))
            roster_url=BASE+'/teams/'+teamid+'/roster?season='+str(g['season'])
            roster=api(roster_url)
            athletes=list(walk_athletes(roster.get('athletes',[])))
            ingest(athletes,school,roster_url,1,allowed)
            notes.append({'school':school,'season':g['season'],'roster_athletes':len({a.get('id') for a in athletes})})
        except Exception as e:notes.append({'school':school,'error':str(e)})
# Reuse previously verified game identities, rather than discarding successful matching.
for record in load('cfb/data/espn_portrait_audit.json',{}).get('missing',[]):
    cid=record.get('id');aid=str(record.get('espn_id',''));source=record.get('source','')
    if cid in people and aid.isdigit() and source.startswith(BASE+'/summary?event='):
        hits[cid].append((0,aid,source))
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
from concurrent.futures import ThreadPoolExecutor
def get_candidates(item):
    cid,(priority,aid,source)=item
    u=espn_image('college-football',aid)
    candidates=[(u,source)]
    athlete_url='https://site.web.api.espn.com/apis/common/v3/sports/football/college-football/athletes/'+aid
    try:
        payload=api(athlete_url)
        a=payload.get('athlete',payload)
        if str(a.get('id',''))==aid and names(a.get('displayName') or a.get('fullName') or '')&names(people[cid]['name']):
            h=a.get('headshot',{})
            href=h.get('href') if isinstance(h,dict) else h
            if isinstance(href,str) and re.fullmatch(r'https://a\.espncdn\.com/i/headshots/(?:college-football|nfl)/players/full/'+aid+r'\.png',href):
                candidates.insert(0,(href,athlete_url))
    except Exception:pass
    return cid,list(dict.fromkeys(candidates))
with ThreadPoolExecutor(max_workers=8) as pool:
    urls=dict(pool.map(get_candidates,[(cid,v) for cid,v in resolved.items() if id_counts[v[1]]==1]))
sentinels={probe(espn_image('college-football',x))[1] for x in ('0','999999999')}
results=probe_many(list({u for cs in urls.values() for u,_ in cs}))
# A repeated image across different identities is a generic silhouette.
hash_owners=defaultdict(set)
for cid,cs in urls.items():
    for u,_ in cs:
        status,h=results[u]
        if status=='image':hash_owners[h].add(cid)
added=[]
for cid,(priority,aid,source) in resolved.items():
    if cid not in urls:
        missing.append({'id':cid,**people[cid],'espn_id':aid,'reason':'Shared ESPN ID needs identity review'});continue
    for u,photo_source in urls[cid]:
        status,h=results[u]
        if status=='image' and h not in sentinels and len(hash_owners[h])==1:
            reg[cid]={'url':u,'espn_id':aid,'name':people[cid]['name'],'school':people[cid]['school'],'source':source,'photo_source':photo_source,'provider':'espn'}
            added.append(cid);break
    else:missing.append({'id':cid,**people[cid],'espn_id':aid,'source':source,'reason':'Unavailable or generic ESPN image','attempts':[{'url':u,'status':results[u][0]} for u,_ in urls[cid]]})
by_school={}
for school,name in SCHOOLS.items():
    ids={cid for cid,p in people.items() if p['school']==school}
    by_school[name]={'targeted':len(ids),'registered':len(ids&set(reg)),'missing':len(ids-set(reg))}
save(REG,reg)
save(REPORT,{'targeted':len(people),'registered':len(set(people)&set(reg)),'added':added,'missing':missing,'schools':by_school,'notes':notes})
print(by_school)
,'',n)}
    if n in {'jaydendukescott','du kescott'.replace(' ','')} :result.update({'jaydendukescott','dukescott'})
    return result
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
urls={cid:espn_image('college-football',v[1]) for cid,v in resolved.items() if id_counts[v[1]]==1}
sentinels={probe(espn_image('college-football',x))[1] for x in ('0','999999999')}
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
