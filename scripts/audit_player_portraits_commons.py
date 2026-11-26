"""Second portrait pass: ID-matched Wikidata images with Commons credit and license."""
import html
import json
import re
import time
from collections import defaultdict
from urllib.parse import quote
from audit_player_portraits import load,save,slug,api,probe_many,trusted,ESPN

WD="https://query.wikidata.org/sparql"
COMMONS="https://commons.wikimedia.org/w/api.php"
def sparql(q):
    return api(WD,params={"query":q,"format":"json"})["results"]["bindings"]
def value(row,key):
    return row.get(key,{}).get("value","")
def plain(s):
    return html.unescape(re.sub(r"<[^>]*>"," ",s)).strip()
def chunks(items,n):
    items=list(items)
    for i in range(0,len(items),n):yield items[i:i+n]
def commons_candidates(ids,property_id,notes):
    found=defaultdict(set)
    for group in chunks(ids,30):
        vals=" ".join(json.dumps(i) for i in group)
        q="SELECT DISTINCT ?id ?person ?image WHERE { VALUES ?id { "+vals+" } ?person wdt:"+property_id+" ?id; wdt:P18 ?image. }"
        try:
            from urllib.parse import unquote,urlsplit
            for row in sparql(q):
                url=value(row,"image")
                title=unquote(urlsplit(url).path.rsplit("/",1)[-1]).replace("_"," ")
                if title and re.search(r"\.(jpg|jpeg|png|webp)$",title,re.I):
                    found[value(row,"id")].add((value(row,"person"),title))
        except Exception as exc:notes.append(f"Wikidata {property_id}: {exc}")
        time.sleep(1)
    # Require an unambiguous person; when there are multiple preferred files leave for manual review.
    return {i:next(iter(v)) for i,v in found.items() if len(v)==1}
def commons_metadata(titles,notes):
    out={}
    for batch in chunks(sorted(set(titles)),15):
        try:
            data=api(COMMONS,params={"action":"query","format":"json","formatversion":2,"titles":"|".join("File:"+t for t in batch),"prop":"imageinfo","iiprop":"url|extmetadata|mime","iiurlwidth":250,"redirects":1})
            for page in data.get("query",{}).get("pages",[]):
                title=page.get("title","").removeprefix("File:")
                info=(page.get("imageinfo") or [{}])[0]; meta=info.get("extmetadata",{})
                m=lambda k:plain(meta.get(k,{}).get("value",""))
                license=m("LicenseShortName"); author=m("Attribution") or m("Artist")
                license_url=m("LicenseUrl")
                if not license_url and license in ("Public domain","Public Domain","PD"):license_url="https://commons.wikimedia.org/wiki/Commons:Public_domain"
                if not license_url and license=="CC0":license_url="https://creativecommons.org/publicdomain/zero/1.0/"
                if not re.match(r"^(CC BY(?:-SA)? |CC0|Public [Dd]omain|PD$)",license):continue
                if not author:
                    if license.lower() in ("public domain","pd","cc0"):author="Public domain / Wikimedia Commons"
                    else:continue
                if not re.match(r"^https://(creativecommons\.org|commons\.wikimedia\.org)/",license_url):continue
                url=info.get("thumburl") or info.get("url","")
                if not url.startswith("https://upload.wikimedia.org/wikipedia/commons/"):continue
                out[title.replace("_"," ")]={"url":url,"source":"https://commons.wikimedia.org/wiki/File:"+quote(title.replace(" ","_")),"provider":"commons","author":author,"license":license,"license_url":license_url,"filename":title}
        except Exception as exc:notes.append(f"Commons metadata: {exc}")
        time.sleep(1)
    return out
def verified_records(candidates,notes):
    meta=commons_metadata([v[1] for v in candidates.values()],notes)
    items={i:{**meta[t],"wikidata":q} for i,(q,t) in candidates.items() if t in meta}
    checks=probe_many(list({v["url"] for v in items.values()}))
    good=trusted(checks,set())
    return {i:v for i,v in items.items() if v["url"] in good}
def soccer_ids(missing,notes):
    found=defaultdict(set)
    for m in load("soccer/data/matches.json",[]):
        expected=[{slug(n) for k in ("starters","subs_used") for n in m.get(s+"_"+k,[])} for s in ("home","away")]
        league={"MLS":"usa.1","FIFA World Cup":"fifa.world","USL Championship":"usa.usl.1"}.get(m["competition"])
        if not league:continue
        try:
            board=api(f"{ESPN}/{league}/scoreboard",params={"dates":m["date"].replace("-",""),"limit":100})
            for event in board.get("events",[]):
                sides={x["homeAway"]:x for x in event["competitions"][0]["competitors"]}
                if not all(str(sides.get(s,{}).get("score"))==str(m[s+"_score"]) for s in ("home","away")):continue
                summary=api(f"{ESPN}/{league}/summary",params={"event":event["id"]})
                matches=[]
                for i,s in enumerate(("home","away")):
                    teamid=str(sides[s]["team"]["id"])
                    roster=next((r.get("roster",[]) for r in summary.get("rosters",[]) if str(r.get("team",{}).get("id"))==teamid),[])
                    matched=defaultdict(set)
                    for row in roster:
                        a=row.get("athlete",{}); aid=str(a.get("id",""))
                        if not aid.isdigit():continue
                        for key in ("displayName","fullName"):
                            n=slug(a.get(key,""))
                            if n in expected[i]:matched[n].add(aid)
                    matches.append(matched)
                if min(map(len,matches))<5:continue
                for match in matches:
                    for n,ids in match.items():
                        if n in missing:found[n].update(ids)
        except Exception as exc:notes.append(f"{m['id']}: {exc}")
    return {n:next(iter(ids)) for n,ids in found.items() if len(ids)==1}
def main():
    report=load("reports/player_portrait_audit.json")
    spath="soccer/data/player_portraits.json"; mpath="mlb/data/player_portrait_fallbacks.json"
    soccer=load(spath,{}); mlb=load(mpath,{})
    notes=[]
    sm={slug(n):n for n in report["soccer"]["missing"] if slug(n) not in soccer}
    mm={str(p["id"]):p for p in report["mlb"]["missing"] if str(p["id"]) not in mlb}
    ids=soccer_ids(sm,notes)
    sc=verified_records(commons_candidates(set(ids.values()),"P3681",notes),notes)
    mc=verified_records(commons_candidates(mm,"P3541",notes),notes)
    before_s,before_m=len(soccer),len(mlb)
    for n,i in ids.items():
        if i in sc:soccer[n]={"name":sm[n],"espn_id":i,**sc[i]}
    for i,record in mc.items():mlb[i]={"name":mm[i]["name"],**record}
    save(spath,soccer);save(mpath,mlb)
    report["soccer"]["registered"]=len(soccer)
    report["soccer"]["missing"]=[n for n in report["soccer"]["missing"] if slug(n) not in soccer]
    report["mlb"]["fallbacks"]=len(mlb)
    report["mlb"]["missing"]=[p for p in report["mlb"]["missing"] if str(p["id"]) not in mlb]
    report["commons_pass"]={"soccer_added":len(soccer)-before_s,"mlb_added":len(mlb)-before_m,"soccer_identity_matches":len(ids),"notes":notes}
    save("reports/player_portrait_audit.json",report)
    print(json.dumps(report,ensure_ascii=False,indent=2))
if __name__=="__main__":main()
