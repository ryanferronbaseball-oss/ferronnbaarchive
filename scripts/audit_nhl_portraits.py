"""Match witnessed NHL players by exact official game/roster identities; reject placeholder images."""
import collections, hashlib, io, json, pathlib, re, unicodedata
from urllib.parse import urlsplit
import requests
from PIL import Image

ROOT=pathlib.Path(__file__).resolve().parents[1]
DATA=ROOT/'nhl/data'
REG=DATA/'player_portraits.json'
REPORT=DATA/'player_portrait_audit.json'
BASE='https://api-web.nhle.com/v1'
S=requests.Session()
S.headers['User-Agent']='CourtsideArchive/1.0 (historical player portrait verification)'
def load(path,default):
    return json.loads(path.read_text()) if path.exists() else default
def save(path,data):
    path.write_text(json.dumps(data,ensure_ascii=False,indent=2,sort_keys=True)+'\n')
def norm(s):
    return re.sub(r'[^a-z0-9]','',unicodedata.normalize('NFKD',str(s)).encode('ascii','ignore').decode().lower())
def val(x):
    return x.get('default','') if isinstance(x,dict) else x or ''
def get(url):
    r=S.get(url,timeout=20);r.raise_for_status();return r.json()
def digest(url):
    if not isinstance(url,str) or not re.fullmatch(r'https://assets\.nhle\.com/mugs/nhl/[^?#]+\.png',url):return None
    try:
        r=S.get(url,timeout=15);r.raise_for_status()
        if urlsplit(r.url).hostname!='assets.nhle.com':return None
        im=Image.open(io.BytesIO(r.content)).convert('RGBA')
        if min(im.size)<80:return None
        im=im.resize((128,128))
        return hashlib.sha256(im.tobytes()).hexdigest()
    except Exception:return None
games=load(DATA/'games.json',[])
registry=load(REG,{})
targets={}
matches=collections.defaultdict(list)
notes=[]
for g in games:
    for p in g['players']:targets[p['id']]=p
    year=int(g['date'][:4])-(int(g['date'][5:7])<7)
    season=str(year)+str(year+1)
    gid=g['game_id']
    box_url=f'{BASE}/gamecenter/{gid}/boxscore'
    try:box=get(box_url)
    except Exception as e:box={};notes.append(f'{box_url}: {e}')
    for side in ('away','home'):
        team=g[side];abbr=g[side+'_abbr']
        # Official game box score gives IDs and sometimes surnames only.
        block=box.get('playerByGameStats',{}).get(side+'Team',{})
        ids={int(p['playerId']) for role in ('forwards','defense','goalies') for p in block.get(role,[]) if p.get('playerId')}
        roster_url=f'{BASE}/roster/{abbr}/{season}'
        try:roster=get(roster_url)
        except Exception as e:roster={};notes.append(f'{roster_url}: {e}')
        candidates=[]
        for role in ('forwards','defensemen','goalies'):
            for row in roster.get(role,[]):
                pid=row.get('id');name=val(row.get('firstName'))+' '+val(row.get('lastName'))
                if pid and (not ids or int(pid) in ids):candidates.append((int(pid),name,row.get('headshot'),roster_url))
        # The game IDs themselves are a second identity route if historical roster is unavailable.
        for pid in ids:
            if any(row[0]==pid for row in candidates):continue
            try:
                landing=get(f'{BASE}/player/{pid}/landing')
                candidates.append((pid,val(landing.get('firstName'))+' '+val(landing.get('lastName')),landing.get('headshot'),box_url))
            except Exception as e:notes.append(f'player {pid}: {e}')
        for p in g['players']:
            if p['team']!=team:continue
            exact=[row for row in candidates if norm(row[1])==norm(p['name'])]
            if len(exact)==1:
                pid,name,photo,source=exact[0]
                matches[p['id']].append((pid,name,photo,source,season,abbr))
            elif len(exact)>1:notes.append(f"Ambiguous official match: {p['name']}")
placeholder={d for d in (digest('https://assets.nhle.com/mugs/nhl/latest/0.png'),digest('https://assets.nhle.com/mugs/nhl/20072008/LAK/0.png')) if d}
found={};missing=[]
for cid,p in targets.items():
    if cid in registry:continue
    rows=matches[cid];attempts=[]
    if not rows or len({r[0] for r in rows})!=1:
        missing.append({'id':cid,'name':p['name'],'reason':'No unique exact official roster identity'});continue
    pid,name,rosterphoto,source,season,abbr=rows[0]
    landing_url=f'{BASE}/player/{pid}/landing'
    try:landing=get(landing_url)
    except Exception as e:landing={};notes.append(f'{landing_url}: {e}')
    if landing and (int(landing.get('playerId',pid))!=pid or norm(val(landing.get('firstName'))+' '+val(landing.get('lastName')))!=norm(p['name'])):
        missing.append({'id':cid,'name':p['name'],'reason':'Official biography identity mismatch'});continue
    urls=[(f'https://assets.nhle.com/mugs/nhl/{season}/{abbr}/{pid}.png',source),(rosterphoto,source),(landing.get('headshot'),landing_url)]
    seen=set()
    for url,photo_source in urls:
        if not url or url in seen:continue
        seen.add(url);d=digest(url);attempts.append({'url':url,'valid_image':bool(d and d not in placeholder)})
        if d and d not in placeholder:
            found[cid]=({'url':url,'source':photo_source,'nhl_id':pid,'name':p['name'],'provider':'nhl','identity_source':source},d);break
    if cid not in found:missing.append({'id':cid,'name':p['name'],'nhl_id':pid,'reason':'No verified NHL image','attempts':attempts})
counts=collections.Counter(d for _,d in found.values())
added=[]
for cid,(record,d) in found.items():
    if counts[d]>1:
        missing.append({'id':cid,'name':record['name'],'reason':'Duplicate image digest (possible generic silhouette)'});continue
    registry[cid]=record;added.append(cid)
save(REG,registry)
save(REPORT,{'targeted':len(targets),'registered':sum(cid in registry for cid in targets),'added':added,'missing':missing,'notes':notes})
print(json.dumps({'targeted':len(targets),'registered':sum(cid in registry for cid in targets),'added':len(added),'missing':len(missing)}))
