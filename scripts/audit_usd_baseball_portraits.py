"""Newest available verified college portrait first, preserving MLB and older college fallbacks."""
import json,re,subprocess,unicodedata,datetime
from collections import defaultdict
from urllib.parse import urljoin,urlsplit,unquote,parse_qs
from bs4 import BeautifulSoup
from audit_player_portraits import load,save,get,probe_many,probe
def norm(s):return re.sub('[^a-z0-9]','',unicodedata.normalize('NFKD',str(s)).encode('ascii','ignore').decode().lower())
def host(u):return (urlsplit(u).hostname or '').removeprefix('www.')
def allowed(u,school):
    h=host(u)
    return u.startswith('https://') and (h==school or any(h==d or h.endswith('.'+d) for d in ('sidearmsports.com','sidearmdev.com','sidearmnextgen.com','amazonaws.com','cloudfront.net')))
def urls(img,page,school):
    for k in ('data-src','src','data-lazy-src','data-original'):
        v=img.get(k)
        if v:
            u=urljoin(page,v)
            if allowed(u,school) and not re.search(r'placeholder|silhouette|default|logo|\.svg(?:\?|$)|blank|spacer',u,re.I):yield u
def named_images(soup,page,school,names):
    for img in soup.find_all('img'):
        alt=norm(img.get('alt',''))
        if any(alt in (n,'photoof'+n,'imageof'+n,n+'headshot','headshotof'+n,n+'portrait','portraitof'+n) for n in names):
            yield from urls(img,page,school)
def image_options(value,page,school):
    if not value:return []
    u=urljoin(page,value)
    if not allowed(u,school):return []
    raw=parse_qs(urlsplit(u).query).get('url',[])
    options=[u,*raw]
    return [v for v in options if allowed(v,school) and not re.search(r'placeholder|silhouette|default|logo|\.svg(?:\?|$)|blank|spacer',v,re.I)]
def card_images(soup,page,school,names):
    for card in soup.select('.sidearm-roster-player, .sidearm-roster-player-container, li.sidearm-roster-player, tr.sidearm-roster-player'):
        links=card.select('a[href*="/roster/"]')
        if not any(norm(a.get_text(' ',strip=True)) in names or norm(urlsplit(a['href']).path.rstrip('/').split('/')[-2]) in names for a in links if len(urlsplit(a['href']).path.rstrip('/').split('/'))>=2):continue
        for img in card.select('.sidearm-roster-player-image img, img.sidearm-roster-player-image, .sidearm-roster-player-image a, .sidearm-roster-player-image source'):
            for k in ('data-src','src','data-lazy-src','href'):
                yield from image_options(img.get(k),page,school)
def bio_images(soup,page,school,names):
    # Restrict unlabeled headshots to the designated player portrait container.
    for tag in soup.select('.sidearm-roster-player-image img, .sidearm-roster-player-image a, img.sidearm-roster-player-image, .sidearm-roster-player-headshot img, .sidearm-roster-player-headshot a, .sidearm-roster-player-header .sidearm-roster-player-image img'):
        for k in ('data-src','src','data-lazy-src','href'):
            yield from image_options(tag.get(k),page,school)
    # USD's portrait is an image anchor with width=300, distinct from gallery images.
    for a in soup.find_all('a',href=True):
        u=urljoin(page,a['href']);path=urlsplit(u).path
        if '/images/' not in path or not re.search(r'\.(?:png|jpe?g|webp)$',path,re.I):continue
        if parse_qs(urlsplit(u).query).get('width')!=['300']:continue
        stem=norm(path.rsplit('/',1)[-1].rsplit('.',1)[0])
        if any(n in stem or stem in n and len(stem)>=6 for n in names):
            yield from image_options(u,page,school)
    yield from named_images(soup,page,school,names)
def photo_year(url,season):
    # Only an explicit upload date is used; otherwise use verified roster season.
    m=re.search(r'/((?:19|20)\d{2})/\d{1,2}/\d{1,2}/',unquote(url))
    return int(m.group(1)) if m else season
def roster(year,school,notes):
    u=f'https://{school}/sports/baseball/roster/{year}'
    if school=='usdtoreros.com' and year==2027:u=f'https://{school}/sports/baseball/roster'
    try:
        r=get(u);r.raise_for_status()
        if host(r.url)!=school:return None
        soup=BeautifulSoup(r.text,'html.parser')
        heading=' '.join(t.get_text(' ',strip=True) for t in soup.find_all(['h1','h2','title']))
        if not re.search(r'\b'+str(year)+r'\b.{0,35}baseball.{0,25}roster',heading,re.I):
            notes.append(f'{school} {year}: roster heading not verified: {heading[:150]}');return None
        return soup,r.url
    except Exception as e:notes.append(f'{school} {year}: {e}');return None
def main():
    players=json.loads(subprocess.check_output(['node','scripts/export_usd_baseball_portrait_targets.cjs'],text=True))
    hosts=load('college-baseball/data/portrait_school_hosts.json')
    fp='college-baseball/data/player_portraits.json';reg=load(fp,{})
    report={'school':'San Diego','targeted':len(players),'added':[],'upgraded':[],'preserved':[],'missing':[],'notes':[],'unmapped_transfer_schools':[]}
    requests=defaultdict(set)
    for p in players:
        for school,years in p['schools'].items():
            if school not in hosts:
                if school not in report['unmapped_transfer_schools']:report['unmapped_transfer_schools'].append(school)
                continue
            if not years:continue
            for y in range(min(years),min(2027,max(years)+5)+1):requests[hosts[school]].add(y)
    pages={}
    for school,years in requests.items():
        for y in sorted(years):pages[school,y]=roster(y,school,report['notes'])
    candidates=defaultdict(list)
    for p in players:
        names={norm(n) for n in [p['name'],*p.get('former_names',[])] if len(norm(n))>4}
        for school,years in p['schools'].items():
            h=hosts.get(school)
            if not h or not years:continue
            # Require a name match in a witnessed season or a known adjacent roster;
            # stop extending the same identity after a gap of two absent seasons.
            matched=[]
            for y in range(min(years),min(2027,max(years)+5)+1):
                page=pages.get((h,y))
                if not page:continue
                soup,u=page
                links=[]
                for a in soup.find_all('a',href=True):
                    v=urljoin(u,a['href']);path=urlsplit(v).path
                    if host(v)!=h or not re.search(r'/roster/[^/]+/\d+/?$',path):continue
                    part=path.rstrip('/').split('/')[-2]
                    if norm(part) in names or norm(a.get_text(' ',strip=True)) in names:links.append(v)
                imgs=list(dict.fromkeys([*card_images(soup,u,h,names),*named_images(soup,u,h,names)]))
                if not links and not imgs:continue
                if y not in years and (not matched or y-matched[-1]>2):continue
                matched.append(y)
                for v in imgs:candidates[p['id']].append((y,photo_year(v,y),v,u,school,None))
                # Bio pages may use a portrait not present in roster markup.
                for v in list(dict.fromkeys(links))[:2]:
                    candidates[p['id']].append((y,y,None,v,school,h))
    report['roster_pages_verified']=sum(v is not None for v in pages.values())
    report['players_with_candidates']=sum(bool(v) for v in candidates.values())
    found={}
    for p in players:
        cid=p['id'];names={norm(n) for n in [p['name'],*p.get('former_names',[])]}
        entries=sorted(candidates[cid],key=lambda x:(x[0],x[1],bool(x[2])),reverse=True)
        for y,py,u,source,school,h in entries:
            urls_to_try=[u] if u else []
            if not u:
                try:
                    r=get(source);r.raise_for_status()
                    if host(r.url)!=h:continue
                    soup=BeautifulSoup(r.text,'html.parser')
                    heading=' '.join(t.get_text(' ',strip=True) for t in soup.find_all(['h1','title','h2']))
                    if not any(n in norm(heading) for n in names):continue
                    urls_to_try=list(bio_images(soup,r.url,h,names))
                    source=r.url
                    season_match=re.search(r'\b(20\d{2}) Baseball Roster\b',heading,re.I)
                    if season_match:y=max(y,int(season_match.group(1)))
                except Exception:continue
            for url in dict.fromkeys(urls_to_try):
                state,hash_value=probe(url)
                if state=='image' and hash_value:
                    found[cid]=({'url':url,'source':source,'provider':'college','school':school,'season':y,'photo_year':photo_year(url,y)},hash_value);break
            if cid in found:break
    hashes=defaultdict(set)
    for cid,(r,h) in found.items():hashes[h].add(cid)
    for p in players:
        cid=p['id'];old=reg.get(cid)
        if cid not in found or len(hashes[found[cid][1]])>1:
            report['preserved' if old else 'missing'].append({'id':cid,'name':p['name']});continue
        new=found[cid][0]
        if old and old.get('provider')=='college' and (old.get('season',0),old.get('photo_year',0))>=(new['season'],new['photo_year']):
            report['preserved'].append({'id':cid,'name':p['name']});continue
        if old:
            fallback={k:v for k,v in old.items() if k!='fallbacks'}
            new['fallbacks']=[fallback,*old.get('fallbacks',[])]
        reg[cid]=new
        report['upgraded' if old else 'added'].append({'id':cid,'name':p['name'],**new})
    report['registered']=len(reg)
    save(fp,reg);save('college-baseball/data/usd_portrait_audit.json',report)
    print(json.dumps({k:len(v) if isinstance(v,list) else v for k,v in report.items()},indent=2))
if __name__=='__main__':main()
