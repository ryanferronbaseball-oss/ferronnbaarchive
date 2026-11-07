#!/usr/bin/env python3
"""Verify MiLB->MLB alumni by official MLBAM identities and MLB debut records.

Incremental, conservative: audit ALL imported MiLB player IDs, publish ONLY
officially debuted players, never merge MiLB, MLB or college statistics.
"""
from __future__ import annotations
import collections
import datetime as dt
import json
import pathlib
import time
import urllib.error
import urllib.parse
import urllib.request

ROOT=pathlib.Path(__file__).resolve().parents[2]
MILB=ROOT/"milb"/"data"
API="https://statsapi.mlb.com/api/v1"
HEADERS={"User-Agent":"CourtsideArchive-MiLB-MLB/1.0","Accept":"application/json"}
def read(path,default):
    try:return json.loads(path.read_text(encoding="utf8"))
    except FileNotFoundError:return default

def get(url):
    for attempt in range(4):
        try:
            with urllib.request.urlopen(urllib.request.Request(url,headers=HEADERS),timeout=35) as r:
                return json.load(r)
        except (urllib.error.HTTPError,urllib.error.URLError,TimeoutError):
            if attempt==3:raise
            time.sleep((attempt+1)*1.8)

def people(ids):
    found={}
    for i in range(0,len(ids),24):
        part=ids[i:i+24]
        url=API+"/people?"+urllib.parse.urlencode({"personIds":",".join(map(str,part))})
        batch=get(url)
        for p in batch.get("people",[]):
            if p.get("id") in part:found[p["id"]]=p
        # Do not label missing person IDs as non-debuted.
        missing=set(part)-set(found)
        if missing:raise RuntimeError("Official people endpoint omitted MLBAM IDs "+str(sorted(missing)))
    return found

def draft_lookup(id,year):
    if not year:return None
    url=API+"/draft/"+str(year)+"?"+urllib.parse.urlencode({"playerId":id,"limit":400})
    data=get(url)
    drafts=data.get("drafts") or []
    if isinstance(drafts,dict):drafts=[drafts]
    picks=[]
    for d in drafts:
        for rnd in d.get("rounds",[]):
            for pick in rnd.get("picks",[]):
                person=pick.get("person") or {}
                if person.get("id")!=id:continue
                team=pick.get("team") or {}
                num=pick.get("pickNumber")
                picks.append({"draft_year":year,"draft_round":str(pick.get("pickRound") or rnd.get("round") or "").strip() or None,
                              "draft_pick":int(num) if num is not None else None,
                              "draft_team":team.get("name") or team.get("teamName")})
    # This endpoint is not guaranteed to contain every historical draft choice.
    return min(picks,key=lambda r:r["draft_pick"] if r["draft_pick"] is not None else 99999) if picks else None

def main():
    games=read(MILB/"games.json",[])
    rows=read(MILB/"player_stats.json",[])
    prior=read(MILB/"player_links.json",[])
    if not games or not rows:raise RuntimeError("Cannot audit empty MiLB archive")
    if not isinstance(prior,list):raise ValueError("Existing verified link registry must be an array")
    gameids={g["id"]:g for g in games if g.get("box_score_status")=="verified" and g.get("source_game_id") is not None}
    if any(r.get("game_id") not in gameids for r in rows):raise ValueError("Unverified / orphan MiLB player rows")
    witnessed=collections.defaultdict(list)
    for row in rows:
        id=row.get("player_id")
        if not isinstance(id,int):raise ValueError("Missing MLBAM ID")
        witnessed[id].append(row)
    ids=sorted(witnessed)
    if len(ids)<100:raise RuntimeError("Unexpectedly few player identities; refusing partial status audit")

    official=people(ids)
    # Existing witnessed MLB archive is used for personal crossover ONLY.
    # The MLB stat lines are never imported to the MiLB profile.
    mlbrows=read(ROOT/"mlb"/"data"/"player_stats.json",[])
    if not isinstance(mlbrows,list):raise ValueError("Unexpected MLB attendance rows schema")
    mlb_seen={int(r["player_id"]) for r in mlbrows if r.get("player_id") is not None}
    college=read(ROOT/"college-baseball"/"data"/"mlb_alumni_seed.json",{})
    known_draft={int(r["mlb_player_id"]):r for r in college.get("players",[]) if r.get("mlb_player_id")}

    prior_by_id={int(x["milb_id"]):x for x in prior if x.get("verified") is True and x.get("milb_id")}
    alumni=[]
    links=[]
    nondebut=[]
    draft_pending=[]
    for id in ids:
        person=official[id]
        name=person.get("fullName") or witnessed[id][0].get("name")
        debut=person.get("mlbDebutDate")
        if not debut:
            nondebut.append({"mlb_id":id,"name":name,"status":"no_official_mlb_debut"})
            continue
        if not isinstance(debut,str) or len(debut)!=10 or debut[:4].isdigit() is False:
            raise ValueError("Malformed official MLB debut: "+str(id))
        year=person.get("draftYear")
        try:year=int(year) if year else None
        except (ValueError,TypeError):year=None
        college_draft=known_draft.get(id)
        draft=None
        # Use officially audited college draft record as a fallback for overlapping alumni.
        if college_draft and college_draft.get("draft_pick") is not None:
            draft={k:college_draft.get(k) for k in ("draft_year","draft_round","draft_pick","draft_team")}
        if year and (not draft or int(draft.get("draft_year") or 0)<year):
            try:
                selected=draft_lookup(id,year)
                if selected:draft=selected
            except Exception as exc:
                print("DRAFT_LOOKUP_PENDING",id,year,str(exc)[:110],flush=True)
        if not draft:
            draft={"draft_year":year,"draft_round":None,"draft_pick":None,"draft_team":None}
            draft_pending.append(id)
        appearance_ids={r["game_id"] for r in witnessed[id]}
        mlb_watched=id in mlb_seen
        record={"milb_id":id,"mlb_id":id,"verified":True,"mlb_debut":debut,"mlb_seen":mlb_watched,"source":"MLB StatsAPI people MLB debut date","first_attended_milb":min(r["date"] for r in witnessed[id])}
        if prior_by_id.get(id,{}).get("college_id"):record["college_id"]=prior_by_id[id]["college_id"]
        links.append(record)
        alumni.append({"milb_player_id":id,"mlb_player_id":id,"name":name,"mlb_debut":debut,"mlb_seen":mlb_watched,
                       "draft_year":draft.get("draft_year"),"draft_round":draft.get("draft_round"),
                       "draft_pick":draft.get("draft_pick"),"draft_team":draft.get("draft_team"),
                       "draft_verified":draft.get("draft_pick") is not None,
                       "milb_games":len(appearance_ids)})
    if len(links)+len(nondebut)!=len(ids):raise RuntimeError("Roster classification incomplete")
    if len({r["milb_id"] for r in links})!=len(links):raise ValueError("Duplicate MLB links")
    existing_verified={int(r["milb_id"]) for r in prior if r.get("verified") is True}
    missing=existing_verified-{r["milb_id"] for r in links}
    if missing:raise ValueError("A previously verified MLB alumnus lost debut status: "+str(sorted(missing)))
    stamped=dt.datetime.now(dt.timezone.utc).date().isoformat()
    registry={"version":1,"last_verified":stamped,"source":"MLB StatsAPI /people official mlbDebutDate",
              "description":"Only MLB-debuted athletes in attended MiLB box scores. MLB and MiLB totals separate. Draft records are displayed only when verified.",
              "players":alumni}
    report={"verified_at":stamped,"player_ids_checked":len(ids),
            "official_mlb_debuts":len(links),"also_attended_in_mlb":sum(x["mlb_seen"] for x in links),
            "not_debuted":len(nondebut),"draft_details_pending":len(draft_pending),
            "unmatched_ids":[],"draft_pending_ids":draft_pending,"non_debuted_players":nondebut}
    for name,value in [("player_links.json",links),("mlb_alumni_seed.json",registry),("mlb_status_audit.json",report)]:
        (MILB/name).write_text(json.dumps(value,indent=2,ensure_ascii=False)+"\n",encoding="utf8")
    print("FINAL_REPORT",json.dumps({k:v for k,v in report.items() if not isinstance(v,list)}),flush=True)
if __name__=="__main__":main()
