"""Find official soccer profile photos; never substitute a generic social image."""
import concurrent.futures as cf
import json
import re
from collections import defaultdict
from urllib.parse import urljoin,urlsplit,unquote
from bs4 import BeautifulSoup
from audit_player_portraits import load,save,slug,get,probe

SOURCES=load("soccer/data/portrait_official_sources.json",{})
CLUBS={"Nashville SC":"www.nashvillesc.com","FC Cincinnati":"www.fccincinnati.com","Sporting Kansas City":"www.sportingkc.com"}
ALIASES={"yassine-bounou":["yassine-bono"],"brahim-diaz":["brahim"],"shapi-suleymanov":["magomed-shapi-suleymanov"],"ruben-ramos-jr":["ruben-ramos"],"tah-brian-anunga":["brian-anunga"],"jake-davis":["jacob-davis"]}
def norm(s):return slug(str(s or ""))
def matches_name(s,keys):
    n=norm(s)
    return any(n==k or n in ("player-portrait-"+k,"portrait-of-"+k,k+"-headshot","headshot-of-"+k,"image-of-"+k,"player-photo-"+k) for k in keys)
def photo_urls(tag,base):
    vals=[]
    for attr in ("data-src","src","data-lazy-src","data-original"):
        if tag.get(attr):vals.append(tag[attr])
    for attr in ("srcset","data-srcset"):
        if tag.get(attr):
            vals.extend(s.strip().split()[0] for s in tag[attr].split(",") if s.strip())
    for v in vals:
        if not isinstance(v,str):continue
        u=urljoin(base,v)
        if not u.startswith("https://") or re.search(r"placeholder|default-player|generic|silhouette|logo|crest|flag|sprite|\.svg(?:\?|$)|transparent\.gif",u,re.I):continue
        yield u
def json_person(node,keys):
    if isinstance(node,list):
        for x in node:yield from json_person(x,keys)
    elif isinstance(node,dict):
        if node.get("@type") in ("Person","Athlete") and matches_name(node.get("name"),keys):
            img=node.get("image")
            if isinstance(img,dict):img=img.get("url") or img.get("contentUrl")
            if isinstance(img,str):yield img
        for x in node.values():
            if isinstance(x,(dict,list)):yield from json_person(x,keys)
def inspect_page(url,key,team):
    keys=[key]+ALIASES.get(key,[])
    try:
        r=get(url);r.raise_for_status()
        if not r.url.startswith("https://"):return [],"non-HTTPS redirect"
        soup=BeautifulSoup(r.text,"html.parser")
        titles=[t.get_text(" ",strip=True) for t in soup.find_all(["h1","title"])]
        if not any(any(k in norm(t) for k in keys) for t in titles):
            return [],"player identity absent in page title"
        if "mlssoccer.com" in urlsplit(url).hostname and team and team not in soup.get_text(" ",strip=True):
            return [],"attended club not found on player page"
        candidates={}
        for img in soup.find_all("img"):
            alt=img.get("alt","")
            if not matches_name(alt,keys):continue
            # Named player images only; reject badges, flags and generic social art.
            context=" ".join([str(img.get("class","")),str(img.get("id","")),alt])
            score=10+(5 if re.search(r"portrait|headshot|player",context,re.I) else 0)
            for u in photo_urls(img,r.url):
                if re.search(r"headshot|portrait|MLS-OBJ|playerimage",unquote(u),re.I):score2=score+5
                else:score2=score
                candidates[u]=max(candidates.get(u,0),score2)
        for tag in soup.find_all("script",type="application/ld+json"):
            try:
                for u in json_person(json.loads(tag.string or tag.get_text()),keys):
                    u=urljoin(r.url,u)
                    if u.startswith("https://"):candidates[u]=max(candidates.get(u,0),25)
            except (ValueError,TypeError):pass
        for u,score in sorted(candidates.items(),key=lambda x:-x[1])[:8]:
            status,h=probe(u)
            if status=="image":return [(u,h,r.url)],""
        return [],"no valid named player image"
    except Exception as exc:return [],str(exc)
def main():
    report=load("reports/player_portrait_audit.json")
    path="soccer/data/player_portraits.json"; registry=load(path,{})
    missing={slug(n):n for n in report["soccer"]["missing"] if slug(n) not in registry}
    teams=defaultdict(set)
    for m in load("soccer/data/matches.json",[]):
        for side in ("home","away"):
            for k in ("starters","subs_used"):
                for name in m.get(side+"_"+k,[]):teams[slug(name)].add((m[side],m["competition"]))
    def task(pair):
        key,name=pair
        urls=[(u,None) for u in SOURCES.get(key,[])]
        for team,comp in sorted(teams[key]):
            if comp=="MLS":
                for k in [key]+ALIASES.get(key,[]):
                    urls.extend([(f"https://www.mlssoccer.com/players/{k}/",team),(f"https://{CLUBS[team]}/players/{k}/",None)])
            elif comp=="FIFA World Cup":
                # Bundesliga and LaLiga offer player profiles beyond their domestic leagues.
                urls.extend([(f"https://www.bundesliga.com/en/player/{key}",None),(f"https://www.laliga.com/en-GB/player/{key}",None)])
        notes=[]
        for u,t in dict.fromkeys(urls):
            rows,msg=inspect_page(u,key,t)
            if rows:return key,rows[0],notes
            notes.append({"url":u,"reason":msg})
        return key,None,notes
    with cf.ThreadPoolExecutor(max_workers=4) as pool:results=list(pool.map(task,missing.items()))
    hashes=defaultdict(list)
    for key,record,notes in results:
        if record:hashes[record[1]].append(key)
    added=[]
    for key,record,notes in results:
        if not record or len(hashes[record[1]])!=1:continue
        url,h,source=record
        registry[key]={"name":missing[key],"url":url,"source":source,"provider":"official"}
        added.append(missing[key])
    save(path,registry)
    report["soccer"]["registered"]=len(registry)
    report["soccer"]["missing"]=[n for n in report["soccer"]["missing"] if slug(n) not in registry]
    report["official_soccer_pass"]={"added":added,"attempted":len(missing),"unresolved":[{"name":missing[key],"attempts":notes} for key,record,notes in results if key not in registry]}
    save("reports/player_portrait_audit.json",report)
    print(json.dumps(report["official_soccer_pass"],ensure_ascii=False,indent=2))
if __name__=="__main__":main()
