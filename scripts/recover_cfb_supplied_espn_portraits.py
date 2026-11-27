"""Verify owner-supplied ESPN identities without changing archive IDs."""
from audit_player_portraits import load,save,api,espn_image,probe,probe_many
from collections import Counter
import re,unicodedata
REG='cfb/data/player_portraits.json'
REPORT='cfb/data/espn_portrait_supplied_recovery.json'
SCHOOLS={'NCS':'NC State','WFU':'Wake Forest','DEL':'Delaware','WKU':'Western Kentucky'}
TARGETS={
 'cfb-del-sean-wilson':('5224764','sean-wilson',{'seanwilson'}),
 'cfb-wku-rodney-tisdale-jr':('5196864','rodney-tisdale-jr',{'rodneytisdale','rodneytisdalejr'}),
 'cfb-wku-jyzaiah-rockwell':('4689118','jyziah-rockwell',{'jyziahrockwell','jyzaiahrockwell'}),
 'cfb-wku-jaylen-wester':('4799985','jaylen-wester',{'jaylenwester'}),
 'cfb-wku-christian-white':('5081071','christian-white',{'christianwhite'}),
}
def norm(s):
    return re.sub(r'[^a-z0-9]','',unicodedata.normalize('NFKD',str(s)).encode('ascii','ignore').decode().lower())
rows=load('cfb/data/player_stats.json',[])
people={str(r['athlete_id']):{'name':r['player'],'school':r['team']} for r in rows if r['team'] in SCHOOLS}
reg=load(REG,{})
prior=load('cfb/data/espn_portrait_recovery.json',{})
prior_missing={r['id']:r for r in prior.get('missing',[])}
notes=[];added=[];attempts={};candidates={}
for cid,(aid,slug,names) in TARGETS.items():
    if cid in reg:continue
    if cid not in people or cid not in prior_missing:
        notes.append({'id':cid,'reason':'Not in prior missing cohort'});continue
    if any(str(r.get('espn_id'))==aid for r in reg.values()):
        notes.append({'id':cid,'reason':'ESPN ID already assigned to another archive player'});continue
    source='https://www.espn.com/college-football/player/_/id/'+aid+'/'+slug
    meta='https://site.web.api.espn.com/apis/common/v3/sports/football/college-football/athletes/'+aid
    try:
        payload=api(meta);a=payload.get('athlete',payload)
        official_names={norm(a.get(k,'')) for k in ('fullName','displayName','shortName')}
        if str(a.get('id',''))!=aid or not (official_names&names):
            raise ValueError('ESPN identity mismatch: '+str(a.get('displayName')))
        candidates[cid]=(aid,source,meta,espn_image('college-football',aid))
    except Exception as e:
        attempts[cid]={'reason':'ESPN identity verification failed','detail':str(e)}
sentinels={probe(espn_image('college-football',x))[1] for x in ('0','999999999')}
results=probe_many(list({v[3] for v in candidates.values()}|{r['url'] for r in reg.values() if r.get('url')}))
hash_counts=Counter(h for status,h in results.values() if status=='image')
for cid,(aid,source,meta,url) in candidates.items():
    status,h=results[url]
    if status=='image' and h not in sentinels and hash_counts[h]==1:
        reg[cid]={**people[cid],'url':url,'espn_id':aid,'source':source,'photo_source':meta,'provider':'espn'}
        added.append(cid)
    else:attempts[cid]={'reason':'Unavailable or duplicate ESPN image','probe_status':status}
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
