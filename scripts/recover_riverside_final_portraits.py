"""Recover missing UCR portraits from official roster and individual bio headshot markup."""
import json,re,subprocess
from collections import defaultdict
from urllib.parse import urljoin,urlsplit,unquote
from bs4 import BeautifulSoup
from audit_player_portraits import load,save,get,probe
from audit_riverside_baseball_portraits import norm,host,image_options,bio_images,roster
P='college-baseball/data/'
reg=load(P+'player_portraits.json',{})
players=json.loads(subprocess.check_output(['node','scripts/export_baseball_portrait_preferences.cjs','UC Riverside'],text=True))
targets=[p for p in players if p['id'] not in reg]
report={'added':[],'missing':[],'notes':[]}
pages={}
for year in range(2018,2027):
    p=roster(year,'gohighlanders.com',report['notes'])
    if p:pages[year]=p
direct={'anthony-lepre':(2018,'anthony-lepre/5221'),'ian-nowak':(2018,'ian-nowak/5205'),'hazahel-quijada':(2018,'hazahel-quijada/5207'),'kevin-west':(2021,'kevin-west/6210'),'anthony-russo':(2021,'anthony-russo/6205'),'devin-mckesson':(2019,'devin-mckesson/5745'),'taylor-juline':(2021,'taylor-juline/6636')}
hashes={}
for p in targets:
    name=p['name'];cid=p['id'];n=norm(name);links=[]
    for year,(soup,source) in pages.items():
        for a in soup.find_all('a',href=True):
            u=urljoin(source,a['href']);path=urlsplit(u).path
            if host(u)=='gohighlanders.com' and re.search(r'/sports/baseball/roster/[^/]+/\d+/?$',path) and norm(path.split('/')[-2])==n:
                links.append((year,u))
    slug=cid.removeprefix('cb-uc-riverside-')
    if slug in direct:
        year,bio=direct[slug];links.append((year,'https://gohighlanders.com/sports/baseball/roster/'+bio))
    attempts=[]
    for year,source in sorted(set(links),reverse=True):
        try:
            r=get(source);r.raise_for_status()
            if host(r.url)!='gohighlanders.com':continue
            soup=BeautifulSoup(r.text,'html.parser')
            title=soup.title.get_text(' ',strip=True) if soup.title else ''
            if n not in norm(title):continue
            season=re.search(r'\b(20\d{2})\b',title)
            if season:year=int(season.group(1))
            candidates=[]
            # Generic "UCR baseball headshots" alt text is legitimate on a verified
            # individual biography, but never on a roster page.
            for img in soup.find_all('img'):
                alt=norm(img.get('alt',''))
                if 'headshot' in alt and ('ucrbaseball' in alt or n in alt):
                    for key in ('src','data-src','data-lazy-src','data-original'):
                        candidates.extend(image_options(img.get(key),r.url,'gohighlanders.com'))
                    a=img.find_parent('a',href=True)
                    if a:candidates.extend(image_options(a['href'],r.url,'gohighlanders.com'))
            candidates.extend(bio_images(soup,r.url,'gohighlanders.com',{n}))
            for url in dict.fromkeys(candidates):
                state,h=probe(url);attempts.append({'url':url,'state':state})
                if state!='image' or not h or h in hashes:continue
                hashes[h]=cid
                reg[cid]={'provider':'college','school':'UC Riverside','season':year,'photo_year':year,'source':r.url,'url':url}
                report['added'].append({'id':cid,'name':name,**reg[cid]})
                break
            if cid in reg:break
        except Exception as e:attempts.append({'source':source,'error':str(e)})
    if cid not in reg:report['missing'].append({'id':cid,'name':name,'bio_candidates':len(set(links)),'attempts':attempts})
report.update(profiles=len(players),registered_portraits=sum(p['id'] in reg for p in players))
save(P+'player_portraits.json',reg);save(P+'riverside_portrait_followup.json',report)
print(json.dumps(report,indent=2))
