#!/usr/bin/env python3
"""Audit May 4 2019 Quakes/Giants against official MLB debuts and attended MLB/college games.

This tool changes verified MLB link records only, never unverified college
identities. Run in repository checkout, where large attendance files are
available in full (unlike the API preview). Writes an inspectable audit JSON.
"""
import datetime as dt
import json
import pathlib
import re
import time
import unicodedata
import urllib.parse
import urllib.request
from collections import defaultdict

ROOT=pathlib.Path(__file__).resolve().parents[2]
M=ROOT/"milb"/"data"
GAME="milb-2019-05-04-quakes-giants"
API="https://statsapi.mlb.com/api/v1"
def read(path):return json.loads(path.read_text(encoding="utf-8"))
def save(path,obj):path.write_text(json.dumps(obj,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
def norm(v):
    s=unicodedata.normalize("NFKD",str(v or "").lower())
    return re.sub(r"[^a-z0-9]","", "".join(x for x in s if not unicodedata.combining(x)))
def official_people(ids):
    url=API+"/people?"+urllib.parse.urlencode({"personIds":",".join(map(str,sorted(ids)))})
    error=None
    for i in range(4):
        try:
            req=urllib.request.Request(url,headers={"User-Agent":"CourtsideArchive-MiLB/2019-audit","Accept":"application/json"})
            with urllib.request.urlopen(req,timeout=35) as res:
                people=json.load(res).get("people",[])
            found={int(x["id"]):x for x in people}
            if set(found)!=set(ids):raise RuntimeError("Official MLB people endpoint ID set mismatch: "+str(sorted(set(ids)-set(found))))
            return found
        except Exception as exc:
            error=exc
            time.sleep(i+1)
    raise RuntimeError("Official MLB player ID/debut source unavailable; no changes saved") from error

def main():
    supplement=read(M/"player_stats_2019_05_04.json")
    assert len(supplement)==26 and all(r.get("game_id")==GAME for r in supplement)
    seen={int(r["player_id"]):r["name"] for r in supplement}
    if len(seen)!=26:raise RuntimeError("Expected 26 unique numeric MLBAM IDs")
    people=official_people(set(seen))
    mlb_rows=read(ROOT/"mlb"/"data"/"player_stats.json")
    if not isinstance(mlb_rows,list):raise RuntimeError("Attended MLB player dataset not an array")
    mlb_seen={int(r["player_id"]) for r in mlb_rows if r.get("player_id") is not None and str(r.get("player_id")).isdigit()}
    college_rows=read(ROOT/"college-baseball"/"data"/"player_stats.json")
    if not isinstance(college_rows,list):raise RuntimeError("College attended player dataset not an array")
    college_merges=read(ROOT/"college-baseball"/"data"/"player_identity_crosswalk.json")
    canonical={str(x):str(m["canonical_id"]) for m in college_merges.get("merges",[]) for x in m.get("source_player_ids",[])}
    by_name=defaultdict(dict)
    for r in college_rows:
        name=r.get("player") or r.get("name")
        cid=r.get("player_id")
        if not name or not cid:continue
        key=norm(name)
        c=canonical.get(str(cid),str(cid))
        item=by_name[key].setdefault(c,{"college_player_id":c,"name":name,"teams":set(),"game_ids":set()})
        if r.get("team"):item["teams"].add(str(r["team"]))
        if r.get("game_id"):item["game_ids"].add(str(r["game_id"]))
    prior=read(M/"player_links.json")
    prior_college=read(M/"college_links.json")
    by_id={int(x["milb_id"]):x for x in prior}
    records=[]
    candidates=[]
    errors=[]
    added=[]
    changed=[]
    for id,name in sorted(seen.items(),key=lambda v:v[1]):
        person=people[id]
        official_name=person.get("fullName") or ""
        official_surname=norm(person.get("lastName") or official_name.split(" ")[-1])
        name_words=str(name).split()
        if not official_surname or official_surname!=norm(name_words[-1]):
            errors.append({"name":name,"id":id,"official_name":official_name,"reason":"Name/surname mismatch: review MLBAM ID"})
            continue
        debut=person.get("mlbDebutDate")
        witnessed=id in mlb_seen
        possible=list(by_name.get(norm(name),{}).values())
        for hit in possible:
            candidates.append({"name":name,"milb_id":id,"college_player_id":hit["college_player_id"],
                               "school_appearances":sorted(hit["teams"]),
                               "attended_college_games":len(hit["game_ids"]),
                               "status":"review_required",
                               "note":"Exact name alone does not authorize a college-to-MiLB tag"})
        existing_college=[x for x in prior_college if int(x.get("milb_id") or 0)==id and x.get("verified")]
        if existing_college and not possible:
            errors.append({"name":name,"id":id,"reason":"Previously verified college link not found in attended college data"})
        records.append({"name":name,"milb_id":id,"official_name":official_name,
                        "official_mlb_debut":debut,"mlb_seen_in_archive":witnessed if debut else False,
                        "college_name_candidates":len(possible),"existing_college_verified":bool(existing_college),
                        "status":"reached_mlb" if debut else "no_official_mlb_debut"})
        if not debut:continue
        rec={"milb_id":id,"mlb_id":id,"verified":True,"mlb_debut":debut,"mlb_seen":witnessed,
             "source":"MLB StatsAPI /people mlbDebutDate and attended MLB player_stats.json",
             "first_attended_milb":"2019-05-04"}
        if id in by_id:
            old=by_id[id]
            if old.get("college_id"):rec["college_id"]=old["college_id"]
            if any(old.get(k)!=rec.get(k) for k in ("mlb_debut","mlb_seen")):changed.append(id)
            by_id[id]={**old,**rec}
        else:
            by_id[id]=rec
            added.append(id)
    if errors:
        raise RuntimeError("MLB ID identity exceptions; refusing unverified tag update: "+json.dumps(errors))
    if len(records)!=26:raise RuntimeError("Missing verified official ID status")
    if any(x["milb_id"] not in set(seen) for x in candidates):raise RuntimeError("Bad college candidate")
    result={
      "game_id":GAME,"verified_at":dt.datetime.now(dt.timezone.utc).isoformat(),
      "audit_scope":"26 participants; MLB debuts vs official MLBAM /people; attended MLB crossovers by exact player IDs; college names require separate person verification",
      "players_audited":26,"mlb_debutants":sum(bool(x["official_mlb_debut"]) for x in records),
      "no_official_mlb_debut":sum(not x["official_mlb_debut"] for x in records),
      "mlb_witnessed_crossovers":sum(x["mlb_seen_in_archive"] for x in records),
      "college_candidates_unverified":len(candidates),
      "new_mlb_tags":added,"corrected_mlb_tags":changed,
      "college_tags_added":0,"players":records,"college_review_candidates":candidates,
      "source":"https://statsapi.mlb.com/api/v1/people; local attended MLB and college baseball stat rows"
    }
    save(M/"quakes_giants_2019_crossover_audit.json",result)
    save(M/"player_links.json",sorted(by_id.values(),key=lambda x:int(x["milb_id"])))
    print("MAY_2019_CROSSOVER_AUDIT",json.dumps({k:v for k,v in result.items() if k not in ("players","college_review_candidates")}),flush=True)

if __name__=="__main__":main()
