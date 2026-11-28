"""Official women's basketball roster portrait recovery. Never modify player identities."""
import concurrent.futures as cf
import hashlib, io, json, re, unicodedata
from collections import defaultdict
from urllib.parse import urljoin, urlsplit, unquote, parse_qs
from bs4 import BeautifulSoup
from PIL import Image
import requests
from audit_player_portraits import load, save

CDNS=('sidearmsports.com','sidearmdev.com','sidearmnextgen.com','cloudfront.net','amazonaws.com','storage.googleapis.com','wmt.digital','wmtcdn.com','imgix.net')
HEADERS={'User-Agent':'Mozilla/5.0 (compatible; CourtsideArchive/1.0)','Accept':'text/html,application/xhtml+xml,image/avif,image/webp,image/*,*/*;q=0.8'}
def norm(s):
    return re.sub(r'[^a-z0-9]','',unicodedata.normalize('NFKD',str(s)).lower())
def host(u):
    return (urlsplit(u).hostname or '').removeprefix('www.')
def allowed(u,school):
    h=host(u)
    return u.startswith('https://') and (h==school or any(h==d or h.endswith('.'+d) for d in CDNS))
def get(url):
    return requests.get(url,headers=HEADERS,timeout=(5,12))
def clean(u):
    return not re.search(r'placeholder|silhouette|default[-_]?headshot|blank|no[-_]?image|logo|\.svg(?:\?|$)',unquote(u),re.I)
def variants(url,school):
    if allowed(url,school) and clean(url):
        yield url
        q=parse_qs(urlsplit(url).query)
        for u in q.get('url',[]):
            if allowed(u,school) and clean(u):yield u
        if host(url)==school and '/images/' in urlsplit(url).path:
            p=urlsplit(url)
            raw='https://dxbhsrqyrr690.cloudfront.net/sidearm.nextgen.sites/'+school+p.path
            # CDN path is a fallback candidate only. It must pass image verification.
            if clean(raw):yield raw
def attrs(img,page,school):
    for k in ('data-src','src','data-lazy-src','data-original','data-image','data-srcset','srcset'):
        v=img.get(k)
        if not isinstance(v,str) or not v.strip():continue
        # Do not split a URL on commas; srcset is parsed separately.
        if k.endswith('srcset'):v=v.split(',')[0].strip().split()[0]
        u=urljoin(page,v)
        if allowed(u,school) and clean(u):yield u
def named_images(soup,page,names,school):
    ns={norm(n) for n in names}
    out=[]
    for img in soup.find_all('img'):
        alt=norm(img.get('alt',''))
        if any(alt in {n,'photoof'+n,'imageof'+n,n+'headshot','headshotof'+n,n+'portrait','portraitof'+n,n+'photo',n+'image'} for n in ns):
            out.extend(attrs(img,page,school))
    # Sidearm roster cards contain the player's name and a dedicated roster image.
    for card in soup.select('.sidearm-roster-player, .sidearm-roster-player-container, .sidearm-roster-player-card'):
        heading=card.select_one('.sidearm-roster-player-name, h3, h2')
        if not heading or norm(heading.get_text(' ',strip=True)) not in ns:continue
        for img in card.select('.sidearm-roster-player-image img, .sidearm-roster-player-headshot img, img.sidearm-roster-player-image'):
            out.extend(attrs(img,page,school))
    return list(dict.fromkeys(out))
def bio_images(soup,page,names,school):
    out=named_images(soup,page,names,school)
    # The main bio headshot is separate from the action-photo carousel.
    for img in soup.select('.sidearm-roster-player-image img, .sidearm-roster-player-headshot img, .sidearm-roster-player-header-image img, .sidearm-roster-player-header-headshot img, .sidearm-roster-player-image > a > img, img.sidearm-roster-player-image'):
        if not img.find_parent(class_=re.compile(r'gallery|carousel|slider',re.I)):
            out.extend(attrs(img,page,school))
    # Name-derived filenames are only used on verified athlete bios.
    ns={norm(n) for n in names}
    for img in soup.find_all('img'):
        if img.find_parent(class_=re.compile(r'gallery|carousel|slider',re.I)):continue
        for u in attrs(img,page,school):
            p=unquote(u)
            if any(n in norm(p) for n in ns) and re.search(r'headshot|portrait|roster',p+' '+str(img.get('class','')),re.I):
                out.append(u)
    return list(dict.fromkeys(out))
def valid_bio(soup,names):
    ns={norm(n) for n in names}
    for tag in soup.select('h1,h2,title,.sidearm-roster-player-name,.sidearm-roster-player-header-name'):
        content=norm(tag.get_text(' ',strip=True))
        if any(n in content for n in ns):return True
    return False
def bio_links(soup,page,names,school):
    ns={norm(n) for n in names}
    out=[]
    for a in soup.find_all('a',href=True):
        u=urljoin(page,a['href'])
        path=urlsplit(u).path
        if host(u)!=school or '/roster/' not in path:continue
        parts=path.rstrip('/').split('/')
        if len(parts)<2:continue
        slug=parts[-2] if parts[-1].isdigit() else parts[-1]
        if norm(slug) in ns or norm(a.get_text(' ',strip=True)) in ns:out.append(u)
    return list(dict.fromkeys(out))
def verify(url,school):
    for u in dict.fromkeys(variants(url,school)):
        try:
            r=get(u)
            if not r.ok or not allowed(r.url,school) or not r.headers.get('Content-Type','').startswith('image/'):continue
            im=Image.open(io.BytesIO(r.content));im.load()
            if min(im.size)<80:continue
            # Avoid returning a tiny image or obviously landscape action photograph.
            if im.width>im.height*1.45:continue
            hash_=hashlib.sha256(im.convert('RGBA').tobytes()).hexdigest()
            return u,hash_
        except Exception:continue
    return None
def main():
    targets=load('college-women/data/school_portrait_targets.json',{})
    data=load('college-women/data/player_headshots.json',{'players':{}})
    reg=data.setdefault('players',{})
    pages={};errors={}
    rosters=sorted({t['roster'] for t in targets.values()})
    def fetch_page(url):
        r=get(url);r.raise_for_status()
        if host(r.url)!=host(url):raise ValueError('off-school redirect')
        return BeautifulSoup(r.text,'html.parser'),r.url
    with cf.ThreadPoolExecutor(max_workers=6) as pool:
        futures={pool.submit(fetch_page,url):url for url in rosters}
        for future in cf.as_completed(futures):
            u=futures[future]
            try:pages[u]=future.result()
            except Exception as ex:errors[u]=str(ex)
    def find(pid,t):
        school=t['host'];names=t['names'];roster=t['roster']
        candidates=[];links=[]
        if t.get('bio'):links.append(t['bio'])
        if roster in pages:
            soup,page=pages[roster]
            candidates.extend((u,page) for u in named_images(soup,page,names,school))
            links.extend(bio_links(soup,page,names,school))
        # Explicit bio candidates, then roster, then linked athlete bios.
        if t.get('bio') and t.get('direct_image'):
            try:
                soup,page=fetch_page(t['bio'])
                if valid_bio(soup,names):candidates.insert(0,(t['direct_image'],page))
            except Exception:pass
        tested=set()
        def attempt(cs):
            for u,source in cs:
                if u in tested:continue
                tested.add(u)
                got=verify(u,school)
                if got:return (got[0],source,got[1])
        result=attempt(candidates)
        if result:return result,None
        for link in list(dict.fromkeys(links))[:5]:
            try:
                soup,page=fetch_page(link)
                if not valid_bio(soup,names):continue
                result=attempt((u,page) for u in bio_images(soup,page,names,school))
                if result:return result,None
            except Exception:continue
        return None,errors.get(roster,'No verified named portrait; '+str(len(links))+' linked bios, '+str(len(tested))+' image candidates')
    report={'targeted':len(targets),'added':[],'missing':[],'preserved':[],'excluded_schools':['Carolina University'],'roster_errors':errors}
    found={}
    with cf.ThreadPoolExecutor(max_workers=8) as pool:
        futures={}
        for pid,t in targets.items():
            if pid in reg:
                report['preserved'].append(pid);continue
            futures[pool.submit(find,pid,t)]=pid
        for future in cf.as_completed(futures):
            pid=futures[future]
            try:
                got,reason=future.result()
                if got:found[pid]=got
                else:report['missing'].append({'id':pid,'name':targets[pid]['names'][0],'reason':reason})
            except Exception as ex:report['missing'].append({'id':pid,'name':targets[pid]['names'][0],'reason':str(ex)})
    hashes=defaultdict(list)
    for pid,(_,_,h) in found.items():hashes[h].append(pid)
    for pid,(url,source,h) in found.items():
        if len(hashes[h])>1:
            report['missing'].append({'id':pid,'name':targets[pid]['names'][0],'reason':'Duplicate image hash'})
            continue
        reg[pid]={'image_url':url,'source_url':source,'provider':'official school'}
        report['added'].append({'id':pid,'name':targets[pid]['names'][0],'image_url':url,'source_url':source})
    report['verified_total']=sum(pid in reg for pid in targets)
    save('college-women/data/player_headshots.json',data)
    save('college-women/reports/school_portrait_audit.json',report)
    print(json.dumps(report,indent=2))
if __name__=='__main__':
    main()
