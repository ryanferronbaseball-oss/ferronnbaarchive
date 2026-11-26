"""Verify final SDSU portraits from specific official player biographies."""
import json,subprocess
from bs4 import BeautifulSoup
from audit_player_portraits import load,save,get,probe
from audit_sdsu_baseball_portraits import bio_images,norm
P='college-baseball/data/'
reg=load(P+'player_portraits.json',{})
targets=[
 ('jordan-verdon','Jordan Verdon','MiLB',None,'https://www.milb.com/player/jordan-verdon-664981',['https://img.mlbstatic.com/mlb-photos/image/upload/c_fill,g_auto/w_180/v1/people/664981/headshot/milb/current']),
 ('sean-ross','Sean Ross','Indiana State',2022,'https://gosycamores.com/sports/baseball/roster/sean-ross/6722',['https://gosycamores.com/images/2022/2/8/Ross_Sean.jpg?width=300','https://dxbhsrqyrr690.cloudfront.net/sidearm.nextgen.sites/indstate.sidearmsports.com/images/2022/2/8/Ross_Sean.jpg']),
 ('eldridge-armstrong','Eldridge Armstrong III','San Diego State',2023,'https://goaztecs.com/sports/baseball/roster/season/2023-24/player/eldridge-armstrong-iii',[]),
 ('xavier-cardenas','Xavier Cardenas III','San Diego State',2025,'https://goaztecs.com/sports/baseball/roster/player/xavier-cardenas-iii',[])]
report={'added':[],'preserved':[],'missing':[]}
for slug,name,school,season,source,urls in targets:
    cid='cb-san-diego-state-'+slug
    if cid in reg:
        report['preserved'].append({'id':cid,'name':name});continue
    if not urls:
        try:
            r=get(source);r.raise_for_status()
            soup=BeautifulSoup(r.text,'html.parser')
            title=' '.join(t.get_text(' ',strip=True) for t in soup.find_all(['h1','title','h2']))
            if norm(name) not in norm(title):raise ValueError('Name not verified')
            urls=list(bio_images(soup,r.url,'goaztecs.com',{norm(name)}))
        except Exception as e:
            report['missing'].append({'id':cid,'name':name,'reason':str(e)});continue
    attempts=[]
    for url in dict.fromkeys(urls):
        state,h=probe(url);attempts.append({'url':url,'state':state})
        if state!='image' or not h:continue
        record={'url':url,'source':source,'provider':'milb' if school=='MiLB' else 'college'}
        if season:record.update(school=school,season=season,photo_year=season)
        else:record['mlb_player_id']='664981'
        reg[cid]=record
        report['added'].append({'id':cid,'name':name,**record})
        break
    else:report['missing'].append({'id':cid,'name':name,'attempts':attempts})
save(P+'player_portraits.json',reg)
players=json.loads(subprocess.check_output(['node','scripts/export_baseball_identity_targets.cjs','San Diego State'],text=True))
report.update(profiles=len(players),registered_portraits=sum(p['id'] in reg for p in players))
save(P+'sdsu_portrait_followup.json',report)
print(json.dumps(report,indent=2))
