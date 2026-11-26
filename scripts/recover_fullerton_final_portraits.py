"""Recover three owner-supplied Fullerton portraits from exact official bio image links."""
import json
from audit_player_portraits import load,save,probe
from audit_fullerton_baseball_portraits import host
targets=[
('cb-cal-state-fullerton-james-wambold','James Wambold',2021,'james-wambold/1926','2023/8/3/james_wambold_m_basebl_2020_21.jpg'),
('cb-cal-state-fullerton-jake-pavletich','Jake Pavletich',2019,'jacob-pavletich/1838','2023/8/3/jacob_pavletich_m_basebl_2018_19.jpg'),
('cb-cal-state-fullerton-jt-navyac','JT Navyac',2023,'jt-navyac/4155','2023/8/31/jt_navyac_m_basebl_2022_23.jpg')]
fp='college-baseball/data/player_portraits.json'
reg=load(fp,{})
report={'added':[],'missing':[]}
hashes=set()
for cid,name,season,bio,filename in targets:
    source='https://fullertontitans.com/sports/baseball/roster/'+bio
    urls=['https://fullertontitans.com/images/'+filename+'?width=300','https://dbukjj6eu5tsf.cloudfront.net/sidearm.sites/csufullerton.sidearmsports.com/images/'+filename,'https://fullertontitans.com/images/'+filename+'?width=80&quality=90']
    for url in urls:
        state,h=probe(url)
        if state!='image' or not h or h in hashes:continue
        hashes.add(h)
        record={'provider':'college','school':'Cal State Fullerton','season':season,'photo_year':season,'source':source,'url':url}
        if cid in reg:
            old=reg[cid]
            if old.get('owner_preferred'):break
            if old['url']!=url:record['fallbacks']=[{k:v for k,v in old.items() if k!='fallbacks'},*old.get('fallbacks',[])]
        reg[cid]=record
        report['added'].append({'id':cid,'name':name,**record})
        break
    else:report['missing'].append({'id':cid,'name':name,'source':source})
save(fp,reg)
save('college-baseball/data/fullerton_portrait_followup.json',report)
print(json.dumps(report,indent=2))
