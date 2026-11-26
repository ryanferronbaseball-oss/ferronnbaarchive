"""Historical MLB portrait audit: exact MLBAM ID and Chadwick crosswalk; no generic photos."""
import concurrent.futures as cf
import csv
import io
import json
import re
import time
from collections import defaultdict
from urllib.parse import urlsplit,urljoin
from bs4 import BeautifulSoup
from audit_player_portraits import load,save,slug,get,probe,api

ROOT="https://raw.githubusercontent.com/chadwickbureau/register/master/data/"
MLB="https://img.mlbstatic.com/mlb-photos/image/upload/w_213,q_85/v1/people/"
def candidate_urls(i):
    return [
      f"https://mlb.mlb.com/images/players/mugshot/ph_{i}.jpg",
      f"https://content.mlb.com/images/headshots/current/60x60/{i}.png",
      f"https://content.mlb.com/images/headshots/current/210x210/{i}.png",
      f"https://img.mlbstatic.com/mlb-photos/image/upload/w_213,q_85/v1/people/{i}/headshot/67/2016",
      f"{MLB}{i}/headshot/67/2015",
      f"{MLB}{i}/headshot/67/2014",
      f"{MLB}{i}/headshot/67/2013",
      f"{MLB}{i}/headshot/67/2012",
      f"{MLB}{i}/headshot/67/2011",
      f"{MLB}{i}/headshot/67/2010",
      f"{MLB}{i}/headshot/67/2009",
      f"{MLB}{i}/headshot/milb/current",
    ]
def crosswalk(missing,notes):
    result=defaultdict(set)
    for shard in "0123456789abcdef":
        try:
            r=get(ROOT+"people-"+shard+".csv");r.raise_for_status()
            for row in csv.DictReader(io.StringIO(r.text)):
                i=row.get("key_mlbam","")
                if i in missing:
                    result[i].add((row.get("key_bbref",""),row.get("key_bbref_minors",""),row.get("key_retro","")))
        except Exception as e:notes.append(f"Chadwick shard {shard}: {e}")
    return {i:next(iter(v)) for i,v in result.items() if len(v)==1}
def name_norm(n):return slug(n).replace("-","")
def reference_candidates(i,person,ids):
    if not ids:return []
    bb,minor,_=ids
    urls=[]
    if bb and re.fullmatch(r"[a-z0-9]+",bb):urls.append(f"https://www.baseball-reference.com/players/{bb[0]}/{bb}.shtml")
    if minor and re.fullmatch(r"[a-z0-9]+",minor):urls.append(f"https://www.baseball-reference.com/register/player.fcgi?id={minor}")
    out=[]
    for page in urls:
        try:
            r=get(page);r.raise_for_status()
            soup=BeautifulSoup(r.text,"html.parser")
            name=name_norm(person["name"])
            title=" ".join(x.get_text(" ",strip=True) for x in soup.find_all(["h1","title"]))
            if name not in name_norm(title):continue
            for tag in soup.find_all("img"):
                alt=name_norm(tag.get("alt",""))
                if alt not in (name,"photoof"+name,"imageof"+name,"headshotof"+name):continue
                for v in (tag.get("src"),tag.get("data-src")):
                    if not v:continue
                    u=urljoin(r.url,v);host=urlsplit(u).hostname or ""
                    if not u.startswith("https://") or not any(host==h or host.endswith("."+h) for h in ("baseball-reference.com","sports-reference.com","sr-logos.com")):continue
                    if re.search("generic|default|placeholder|silhouette|logo[s]?/|\\.svg",u,re.I):continue
                    out.append((u,r.url))
        except Exception:continue
        time.sleep(1)
    return out
def main():
    path="mlb/data/player_portrait_fallbacks.json"; reportpath="reports/player_portrait_audit.json"
    report=load(reportpath); registry=load(path,{})
    missing={str(p["id"]):p for p in report["mlb"]["missing"] if str(p["id"]) not in registry}
    notes=[]; seen=defaultdict(set)
    # Probe nonexistent IDs to detect endpoint-specific placeholders.
    sentinels={probe(url)[1] for url in candidate_urls("999999999")}
    sentinels.update(probe(url)[1] for url in candidate_urls("1"))
    def direct(i):
        for url in candidate_urls(i):
            state,h=probe(url)
            if state=="image" and h not in sentinels:
                return (i,url,h,f"https://www.mlb.com/player/{i}")
        return (i,None,None,None)
    with cf.ThreadPoolExecutor(max_workers=6) as pool:
        first=list(pool.map(direct,missing))
    for i,url,h,source in first:
        if url:seen[h].add(i)
    added=[]; details=[]
    for i,url,h,source in first:
        if url and len(seen[h])==1:
            registry[i]={"name":missing[i]["name"],"url":url,"source":source,"provider":"historical"}
            added.append(i);details.append({"name":missing[i]["name"],"provider":"legacy MLB","url":url})
    remaining={i:p for i,p in missing.items() if i not in registry}
    ids=crosswalk(remaining,notes)
    # A named portrait must be located on the ID-matched Baseball Reference page.
    # Stop on unavailable/forbidden pages rather than bypassing restrictions.
    for i,p in remaining.items():
        for url,source in reference_candidates(i,p,ids.get(i)):
            state,h=probe(url)
            if state!="image" or h in sentinels or h in seen:continue
            seen[h].add(i)
            registry[i]={"name":p["name"],"url":url,"source":source,"provider":"historical"}
            added.append(i);details.append({"name":p["name"],"provider":"Baseball Reference","url":url})
            break
    save(path,registry)
    report["mlb"]["fallbacks"]=len(registry)
    report["mlb"]["missing"]=[p for p in report["mlb"]["missing"] if str(p["id"]) not in registry]
    report["mlb_historical_pass"]={"attempted":len(missing),"added":details,"crosswalk_matches":len(ids),"notes":notes,"remaining_to_90":max(0,(9*report["mlb"]["total_older"]+9)//10-report["mlb"]["current_verified"]-len(registry))}
    save(reportpath,report)
    print(json.dumps(report["mlb_historical_pass"],indent=2))
if __name__=="__main__":main()
