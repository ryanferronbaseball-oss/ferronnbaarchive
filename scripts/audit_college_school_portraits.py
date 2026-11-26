"""Find named portraits on the original school roster or linked official athlete bio.
No changes to athlete identities or box scores. Life Pacific explicitly excluded."""
import json,re,unicodedata
from urllib.parse import urljoin,urlsplit
from bs4 import BeautifulSoup
from audit_player_portraits import load,save,get,probe
from collections import defaultdict

def norm(s):return re.sub(r'[^a-z0-9]','',unicodedata.normalize('NFKD',s).lower())
def host(u):return (urlsplit(u).hostname or '').removeprefix('www.')
def allowed(u,school):
    h=host(u)
    return u.startswith('https://') and (h==school or any(h==d or h.endswith('.'+d) for d in ('sidearmsports.com','sidearmdev.com','sidearmnextgen.com','amazonaws.com','cloudfront.net')))
def candidates(soup,page,names,school):
    accepted={norm(n) for n in names}
    out=[]
    for img in soup.find_all('img'):
        alt=norm(img.get('alt',''))
        if not any(alt in (n,'photoof'+n,'imageof'+n,n+'headshot','headshotof'+n,n+'portrait','portraitof'+n) for n in accepted):continue
        for k in ('data-src','src','data-lazy-src','data-original'):
            v=img.get(k)
            if not v:continue
            u=urljoin(page,v)
            if allowed(u,school) and not re.search(r'placeholder|silhouette|default|logo|\.svg(?:\?|$)|blank',u,re.I):out.append(u)
    return list(dict.fromkeys(out))
def main():
    targets=load('college/data/school_portrait_targets.json')
    fp='college/data/player_headshots.json'; data=load(fp);reg=data['players']
    report={'targeted':len(targets),'added':[],'missing':[],'preserved':[],'excluded_school':'Life Pacific'}
    pages={}; found={}
    for pid,t in targets.items():
        if pid in reg:
            report['preserved'].append(pid);continue
        try:
            roster=t['roster'];school=t['host'];names=t['names']
            if roster not in pages:
                r=get(roster);r.raise_for_status()
                if host(r.url)!=school:raise ValueError('roster redirected off school')
                pages[roster]=(BeautifulSoup(r.text,'html.parser'),r.url)
            soup,page=pages[roster]; cs=[(u,page) for u in candidates(soup,page,names,school)]
            slugs={re.sub(r'[^a-z0-9]+','-',n.lower().replace("'","")).strip('-') for n in names}
            links=[]
            for a in soup.find_all('a',href=True):
                u=urljoin(page,a['href']);path=urlsplit(u).path
                if host(u)!=school or not re.search(r'/roster/[^/]+/\d+/?$',path):continue
                part=path.rstrip('/').split('/')[-2]
                if norm(part) in {norm(n) for n in names} or part in slugs:links.append(u)
            for link in dict.fromkeys(links):
                try:
                    r=get(link);r.raise_for_status()
                    if host(r.url)!=school:continue
                    bio=BeautifulSoup(r.text,'html.parser')
                    headings=' '.join(x.get_text(' ',strip=True) for x in bio.find_all(['h1','title']))
                    if not any(norm(n) in norm(headings) for n in names):continue
                    cs.extend((u,r.url) for u in candidates(bio,r.url,names,school))
                except Exception:continue
            for u,source in dict.fromkeys(cs):
                state,h=probe(u)
                if state=='image' and h:
                    found[pid]=(u,source,h);break
            if pid not in found:report['missing'].append({'id':pid,'name':names[0],'reason':'No verified named portrait found'})
        except Exception as e:report['missing'].append({'id':pid,'name':t['names'][0],'reason':str(e)})
    hashes=defaultdict(list)
    for pid,(_,_,h) in found.items():hashes[h].append(pid)
    for pid,(u,source,h) in found.items():
        if len(hashes[h])>1:
            report['missing'].append({'id':pid,'name':targets[pid]['names'][0],'reason':'Duplicate image hash'});continue
        reg[pid]={'image_url':u,'source_url':source,'provider':'official school'}
        report['added'].append({'id':pid,'name':targets[pid]['names'][0],'image_url':u,'source_url':source})
    save(fp,data);save('college/reports/school_portrait_audit.json',report)
    print(json.dumps(report,indent=2))
if __name__=='__main__':main()
