"""Find missing portraits by stable identifiers and matched historical lineups."""
import concurrent.futures as cf
import hashlib
import io
import json
import re
import time
import unicodedata
from collections import defaultdict
from pathlib import Path
import requests
from PIL import Image

ROOT=Path(__file__).resolve().parents[1]
HEADERS={"User-Agent":"CourtsideArchivePortraitAudit/1.0 (https://github.com/ryanferronbaseball-oss/ferronnbaarchive)"}
ESPN="https://site.api.espn.com/apis/site/v2/sports/soccer"
def load(path,default=None):
    p=ROOT/path
    return json.loads(p.read_text()) if p.exists() else default
def save(path,data):
    p=ROOT/path
    p.parent.mkdir(parents=True,exist_ok=True)
    p.write_text(json.dumps(data,ensure_ascii=False,indent=2,sort_keys=True)+"\n")
def slug(s):
    return re.sub(r"[^a-z0-9]+","-",unicodedata.normalize("NFKD",s).encode("ascii","ignore").decode().lower()).strip("-")
def get(url,**kwargs):
    return requests.get(url,headers=HEADERS,timeout=20,**kwargs)
def api(url,**kwargs):
    r=get(url,**kwargs);r.raise_for_status();return r.json()
def espn_image(sport,id):
    return f"https://a.espncdn.com/i/headshots/{sport}/players/full/{id}.png"
def official(id):
    return f"https://img.mlbstatic.com/mlb-photos/image/upload/w_213,q_85/v1/people/{id}/headshot/67/current"
def probe(url):
    try:
        r=get(url)
        if r.status_code in (404,410): return ("missing",None)
        if not r.ok: return ("error",None)
        if not r.headers.get("Content-Type","").startswith("image/"): return ("missing",None)
        im=Image.open(io.BytesIO(r.content)); im.load()
        if min(im.size)<80: return ("missing",None)
        return ("image",hashlib.sha256(im.convert("RGBA").tobytes()).hexdigest())
    except Exception:
        return ("error",None)
def probe_many(urls):
    with cf.ThreadPoolExecutor(max_workers=6) as pool:
        return dict(zip(urls,pool.map(probe,urls)))
def trusted(results,sentinels):
    counts=defaultdict(int)
    for status,h in results.values():
        if status=="image": counts[h]+=1
    return {url for url,(status,h) in results.items() if status=="image" and h not in sentinels and counts[h]==1}
def soccer():
    matches=load("soccer/data/matches.json",[])
    registry=load("soccer/data/player_portraits.json",{})
    people={}
    candidates=defaultdict(set)
    notes=[]
    for m in matches:
        expected=[]
        for side in ("home","away"):
            names={slug(n):n for k in ("starters","subs_used") for n in m.get(side+"_"+k,[])}
            expected.append(names);people.update(names)
        for e in m.get("events",[]):
            for k in ("player","assist","secondary_assist"):
                if e.get(k):people[slug(e[k])]=e[k]
        league={"MLS":"usa.1","FIFA World Cup":"fifa.world","USL Championship":"usa.usl.1"}.get(m["competition"])
        if not league:continue
        try:
            board=api(f"{ESPN}/{league}/scoreboard",params={"dates":m["date"].replace("-",""),"limit":100})
            events=[]
            for event in board.get("events",[]):
                c=event["competitions"][0]
                sides={x["homeAway"]:x for x in c["competitors"]}
                if all(str(sides.get(s,{}).get("score"))==str(m[s+"_score"]) for s in ("home","away")):
                    events.append((event,sides))
            for event,sides in events:
                summary=api(f"{ESPN}/{league}/summary",params={"event":event["id"]})
                found=[]
                for i,side in enumerate(("home","away")):
                    teamid=str(sides[side]["team"]["id"])
                    roster=next((r.get("roster",[]) for r in summary.get("rosters",[]) if str(r.get("team",{}).get("id"))==teamid),[])
                    matched=defaultdict(set)
                    for row in roster:
                        a=row.get("athlete",{}); aid=str(a.get("id",""))
                        if not aid.isdigit():continue
                        for key in ("displayName","fullName"):
                            n=slug(a.get(key,""))
                            if n in expected[i]:matched[n].add(aid)
                    found.append(matched)
                # Both teams must independently match at least five archive players.
                if min(map(len,found))<5:continue
                for side in found:
                    for n,ids in side.items():
                        for aid in ids:candidates[n].add((aid,event["id"],league))
        except Exception as e:notes.append(f"{m['id']}: {e}")
    unique={n:sorted(v)[0] for n,v in candidates.items() if len({x[0] for x in v})==1 and n not in registry}
    urls={n:espn_image("soccer",v[0]) for n,v in unique.items()}
    sentinel=probe(espn_image("soccer","999999999"))[1]
    good=trusted(probe_many(list(set(urls.values()))),{sentinel})
    for n,url in urls.items():
        if url in good:
            aid,event,league=unique[n]
            registry[n]={"name":people[n],"url":url,"espn_id":aid,"source":f"{ESPN}/{league}/summary?event={event}"}
    save("soccer/data/player_portraits.json",registry)
    return {"total":len(people),"registered":len(set(people)&set(registry)),"missing":[people[n] for n in sorted(set(people)-set(registry))],"notes":notes}
def mlb():
    rows=load("mlb/data/player_stats.json",[])
    registry=load("mlb/data/player_portrait_fallbacks.json",{})
    people={}
    for row in rows:
        aid=str(row["player_id"]);date=str(row.get("date",""))
        if not aid.isdigit() or not date[:4].isdigit():continue
        if aid not in people or date<people[aid]["date"]:people[aid]={"name":row["name"],"date":date}
    # First pass prioritizes players first witnessed through 2015.
    older={i:p for i,p in people.items() if p["date"][:4]<="2015"}
    urls={i:official(i) for i in older if i not in registry}
    results=probe_many(list(urls.values()))
    sentinel=probe(official("999999999"))[1]
    valid=trusted(results,{sentinel})
    missing=[i for i,u in urls.items() if results[u][0]=="missing" or (results[u][0]=="image" and results[u][1]==sentinel)]
    unresolved=[i for i,u in urls.items() if u not in valid and i not in missing]
    mapped=defaultdict(set);notes=[]
    for offset in range(0,len(missing),80):
        vals=" ".join(json.dumps(i) for i in missing[offset:offset+80])
        query="SELECT ?mlb ?espn ?person WHERE { VALUES ?mlb { "+vals+" } ?person wdt:P3541 ?mlb; wdt:P3571 ?espn. }"
        try:
            data=api("https://query.wikidata.org/sparql",params={"query":query,"format":"json"})
            for b in data["results"]["bindings"]:
                i=b["mlb"]["value"]; eid=b["espn"]["value"]
                if i in missing and eid.isdigit():mapped[i].add((eid,b["person"]["value"]))
        except Exception as e:notes.append(str(e))
        time.sleep(1)
    unique={i:next(iter(v)) for i,v in mapped.items() if len(v)==1}
    alternatives={i:espn_image("mlb",v[0]) for i,v in unique.items()}
    good=trusted(probe_many(list(set(alternatives.values()))),{probe(espn_image("mlb","999999999"))[1]})
    for i,url in alternatives.items():
        if url in good:registry[i]={"name":older[i]["name"],"url":url,"espn_id":unique[i][0],"source":unique[i][1]}
    save("mlb/data/player_portrait_fallbacks.json",registry)
    return {"total_older":len(older),"current_verified":len(valid),"fallbacks":len(set(older)&set(registry)),"missing":[{"id":i,**older[i]} for i in missing if i not in registry],"unresolved":[{"id":i,**older[i]} for i in unresolved],"notes":notes}
if __name__=="__main__":
    report={"soccer":soccer(),"mlb":mlb()}
    save("reports/player_portrait_audit.json",report)
    print(json.dumps(report,indent=2,ensure_ascii=False))
