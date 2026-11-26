"""Targeted CSUN portrait recovery using official roster-linked biographies."""
import json,re,subprocess
from urllib.parse import urljoin,urlsplit,parse_qs,unquote
from collections import defaultdict
from bs4 import BeautifulSoup
from audit_player_portraits import load,save,get,probe
from audit_csun_baseball_portraits import norm,host,roster,image_options,photo_year
P='college-baseball/data/'
reg=load(P+'player_portraits.json',{})
hosts=load(P+'portrait_school_hosts.json')
players=json.loads(subprocess.check_output(['node','scripts/export_baseball_portrait_preferences.cjs','Cal State Northridge'],text=True))
targets=[p for p in players if p['id'] not in reg or (not reg[p['id']].get('owner_preferred') and '/resize?' in reg[p['id']].get('url',''))]
report={'added':[],'upgraded':[],'missing':[],'preserved':[],'notes':[]}
requests=defaultdict(set)
for p in targets:
    for school,years in p['schools'].items():
        if school in hosts and years:
            requests[school].update(range(max(2010,min(years)-2),min(2026,max(years)+5)+1))
requests['Cal State Northridge'].update([2021,2022,2023])
pages={}
for school,years in requests.items():
    for year in sorted(years):
        page=roster(year,hosts[school],report['notes'])
        if page:pages[school,year]=page
used={v.get('url'):k for k,v in reg.items()}
hashes={}
for p in targets:
    cid=p['id'];name=p['name'];n=norm(name);surname=norm(name.split()[-1])
    names={norm(x) for x in [name,*p.get('former_names',[])] if len(norm(x))>4}
    names.add(norm(' '.join(name.split()[::-1])))
    ranks={s['school']:i for i,s in enumerate(p['preference']['schools'])}
    links={}
    for (school,year),(soup,page) in pages.items():
        if school not in p['schools']:continue
        for a in soup.find_all('a',href=True):
            u=urljoin(page,a['href']);path=urlsplit(u).path.rstrip('/')
            if host(u)!=hosts[school] or not re.search(r'/sports/baseball/roster/[^/]+/\d+$',path):continue
            if norm(path.split('/')[-2]) not in names and norm(a.get_text(' ',strip=True)) not in names:continue
            links[(school,u)]=max(year,links.get((school,u),0))
    attempts=[]
    found=None
    for (school,source),year in sorted(links.items(),key=lambda item:(ranks.get(item[0][0],999),-item[1])):
        try:
            r=get(source);r.raise_for_status()
            if host(r.url)!=hosts[school]:continue
            soup=BeautifulSoup(r.text,'html.parser')
            title=soup.title.get_text(' ',strip=True) if soup.title else ''
            if not any(x in norm(title) for x in names):
                attempts.append({'source':source,'title_mismatch':title});continue
            m=re.search(r'\b(20\d{2}) Baseball Roster\b',title,re.I)
            if m:year=int(m.group(1))
            crops=[];other=[];observed=[]
            for img in soup.find_all('img'):
                alt=norm(img.get('alt',''))
                for key in ('src','data-src','data-lazy-src','data-original'):
                    for u in image_options(img.get(key),r.url,hosts[school]):
                        q=parse_qs(urlsplit(u).query)
                        stem=norm(urlsplit(q.get('url',[u])[0]).path.rsplit('/',1)[-1].rsplit('.',1)[0])
                        if '/images/' not in unquote(u):continue
                        if len(observed)<35:observed.append({'alt':img.get('alt',''),'url':u})
                        if '/crop' in urlsplit(u).path and q.get('width')==['180'] and q.get('height')==['270']:
                            # The dedicated roster headshot crop is distinct from news/gallery resize images.
                            crops.append(u)
                        elif 'headshot' in alt and (any(x in alt for x in names) or any(x in stem for x in names)):
                            other.append(u)
            crops=list(dict.fromkeys(crops))
            candidates=crops+other if len(crops)==1 else [u for u in crops if any(x in norm(unquote(u)) for x in names)]+other
            if not candidates:attempts.append({'source':r.url,'observed':observed,'crop_count':len(crops)})
            for u in dict.fromkeys(candidates):
                state,h=probe(u);attempts.append({'url':u,'state':state,'source':r.url})
                if state!='image' or not h or h in hashes or (u in used and used[u]!=cid):continue
                hashes[h]=cid;used[u]=cid
                found={'provider':'college','school':school,'season':year,'photo_year':photo_year(u,year),'source':r.url,'url':u}
                break
            if found:break
        except Exception as e:attempts.append({'source':source,'error':str(e)})
    old=reg.get(cid)
    if found:
        if old and old['url']==found['url']:report['preserved'].append({'id':cid,'name':name});continue
        if old:
            if old.get('provider')=='college' and ranks.get(old.get('school'),999)<ranks.get(found['school'],999):
                report['preserved'].append({'id':cid,'name':name,'reason':'Existing preferred-school photo'});continue
            found['fallbacks']=[{k:v for k,v in old.items() if k!='fallbacks'},*old.get('fallbacks',[])]
        reg[cid]=found
        report['upgraded' if old else 'added'].append({'id':cid,'name':name,**found})
    else:
        report['preserved' if old else 'missing'].append({'id':cid,'name':name,'bio_candidates':len(links),'attempts':attempts})
report.update(profiles=len(players),registered_portraits=sum(p['id'] in reg for p in players))
save(P+'player_portraits.json',reg);save(P+'csun_portrait_followup.json',report)
print(json.dumps({k:len(v) if isinstance(v,list) else v for k,v in report.items()},indent=2))
