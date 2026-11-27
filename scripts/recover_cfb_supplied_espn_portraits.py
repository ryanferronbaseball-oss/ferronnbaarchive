"""Verify owner-supplied ESPN identities without changing archive IDs."""
from audit_player_portraits import load,save,api,espn_image,probe,probe_many
from collections import Counter
import re,unicodedata
REG='cfb/data/player_portraits.json'
REPORT='cfb/data/espn_portrait_final_recovery.json'
SCHOOLS={'NCS':'NC State','WFU':'Wake Forest','DEL':'Delaware','WKU':'Western Kentucky'}
TARGETS={
 'cfb-ncs-jayden-duke-scott':('5126513','jayden-scott',{'jaydendukescott','jaydenscott','dukescott'},'college-football'),
 'cfb-ncs-brandon-cleveland':('4685305','brandon-cleveland',{'brandoncleveland'},'nfl'),
 'cfb-wfu-ty-clark-iii':('5186586','ty-clark-iii',{'tyclark','tyclarkiii'},'college-football'),
 'cfb-wfu-kamrean-johnson':('5086448','kamrean-johnson',{'kamreanjohnson'},'college-football'),
}
def norm(s):
    return re.sub(r'[^a-z0-9]','',unicodedata.normalize('NFKD',str(s)).encode('ascii','ignore').decode().lower())
rows=load('cfb/data/player_stats.json',[])
people={str(r['athlete_id']):{'name':r['player'],'school':r['team']} for r in rows if r['team'] in SCHOOLS}
reg=load(REG,{})
prior=load('cfb/data/espn_portrait_supplied_recovery.json',{})
prior_missing={r['id']:r for r in prior.get('missing',[])}
notes=[];added=[];attempts={};candidates={}
for cid,(aid,slug,names,league) in TARGETS.items():
    if cid in reg:continue
    if cid not in people or cid not in prior_missing:
        notes.append({'id':cid,'reason':'Not in prior missing cohort'});continue
    if any(str(r.get('espn_id'))==aid for r in reg.values()):
        notes.append({'id':cid,'reason':'ESPN ID already assigned to another archive player'});continue
    source='https://www.espn.com/'+league+'/player/_/id/'+aid+'/'+slug
    verified=[]
    errors=[]
    for sport in dict.fromkeys((league,'college-football')):
        meta='https://site.web.api.espn.com/apis/common/v3/sports/football/'+sport+'/athletes/'+aid
        try:
            payload=api(meta);a=payload.get('athlete',payload)
            official_names={norm(a.get(k,'')) for k in ('fullName','displayName','shortName')}
            if str(a.get('id',''))==aid and official_names&names:
                verified.append((sport,meta))
            else:errors.append('ESPN identity mismatch: '+str(a.get('displayName')))
        except Exception as e:errors.append(str(e))
    if not verified:
        attempts[cid]={'reason':'ESPN identity verification failed','detail':errors};continue
    # Prefer a college portrait; an NFL headshot is acceptable only for the verified NFL identity.
    urls=[]
    for sport in ('college-football','nfl'):
        if sport=='nfl' and league!='nfl':continue
        if any(v[0]==sport for v in verified) or (sport=='college-football' and league=='nfl'):
            urls.append((espn_image(sport,aid),next((m for l,m in verified if l==sport),verified[0][1])))
    candidates[cid]=(aid,source,urls)
sentinels={probe(espn_image(sport,x))[1] for sport in ('college-football','nfl') for x in ('0','999999999')}
results=probe_many(list({u for _,_,urls in candidates.values() for u,_ in urls}|{r['url'] for r in reg.values() if r.get('url')}))
hash_owners={}
for cid,r in reg.items():
    status,h=results.get(r.get('url'),('missing',None))
    if status=='image':hash_owners.setdefault(h,set()).add(cid)
for cid,(_,_,urls) in candidates.items():
    for u,_ in urls:
        status,h=results[u]
        if status=='image':hash_owners.setdefault(h,set()).add(cid)
for cid,(aid,source,urls) in candidates.items():
    for url,meta in urls:
        status,h=results[url]
        if status=='image' and h not in sentinels and hash_owners.get(h)=={cid}:
            reg[cid]={**people[cid],'url':url,'espn_id':aid,'source':source,'photo_source':meta,'provider':'espn'}
            added.append(cid);break
    else:attempts[cid]={'reason':'Unavailable or duplicate ESPN image','attempts':[{'url':u,'status':results[u][0]} for u,_ in urls]}

missing=[]
for cid,p in people.items():
    if cid in reg:continue
    record=prior_missing.get(cid,{'id':cid,**p,'reason':'Unresolved identity'})
    missing.append({**record,**attempts.get(cid,{})})
schools={}
for school,name in SCHOOLS.items():
    ids={cid for cid,p in people.items() if p['school']==school}
    schools[name]={'targeted':len(ids),'registered':len(ids&set(reg)),'missing':len(ids-set(reg))}
save(REG,reg)
save(REPORT,{'targeted':len(people),'registered':len(set(people)&set(reg)),'added':added,'missing':missing,'schools':schools,'notes':notes,'supplied_targets':list(TARGETS)})
print(schools)
