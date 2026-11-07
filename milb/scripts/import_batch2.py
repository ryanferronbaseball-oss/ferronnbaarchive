#!/usr/bin/env python3
"""Courtside Archive MiLB Batch 2: 12 consecutive attended Storm games, May 25–June 6, 2021.

One-pass import: confirm official Single-A game IDs and scores, box scores,
lineup and innings, update venues and home map, then reconcile MLB debuts.
Preserve all previously verified records and defer college/MiLB cross-matching.
No output is committed unless every required verification succeeds.
"""
import collections
import concurrent.futures
import datetime
import json
import pathlib
import re

import import_batch1 as core
import enrich_game_details as details
import import_mlb_alumni as alumni

ROOT=pathlib.Path(__file__).resolve().parents[2]
DATA=ROOT/"milb"/"data"
VENUES=ROOT/"venues"/"data"/"venues.json"
DATES=[f"2021-05-{day:02d}" for day in range(25,31)]+[f"2021-06-{day:02d}" for day in range(1,7)]
EXPECTED_RESULTS=[
    (8,7),(9,3),(2,8),(0,1),(1,3),(1,2),
    (1,6),(4,5),(4,5),(5,4),(6,2),(9,7),
]
STORM="Lake Elsinore Storm"
OPPONENT=[("San Jose Giants","Excite Ballpark","San Jose, CA","venue-0132")]*6+[
         ("Stockton Ports","Banner Island Ballpark","Stockton, CA","venue-0135")]*6
BATCH_NUMBER=2

def read(path):
    return json.loads(path.read_text(encoding="utf8"))

def write(path,obj):
    path.write_text(json.dumps(obj,indent=2,ensure_ascii=False)+"\n",encoding="utf8")

def official_game(date,club,score):
    options=core.schedule(date,14)
    matches=[]
    for g in options:
        ts=g.get("teams") or {}
        a,h=ts.get("away") or {},ts.get("home") or {}
        if a.get("team",{}).get("id")!=103:continue
        if core.normalized(h.get("team",{}).get("name"))!=core.normalized(club):continue
        if g.get("status",{}).get("abstractGameState")!="Final":continue
        if (a.get("score"),h.get("score"))!=score:continue
        matches.append(g)
    if len(matches)!=1:
        raise ValueError(f"{date} {STORM} @ {club}: expected unique official final {score}, got {len(matches)}")
    return matches[0]

def new_entry(day,club,stadium,city,vid,expected,game):
    slug={"San Jose Giants":"giants","Stockton Ports":"ports"}[club]
    return {"id":f"milb-{day}-storm-{slug}","date":day,"away_team":STORM,
        "home_team":club,"away_score":expected[0],"home_score":expected[1],
        "level":"Single-A","venue":stadium,"city":city,
        "source_game_id":game["gamePk"],
        "source_url":"https://www.milb.com/gameday/"+str(game["gamePk"]),
        "box_score_status":"verified","attendance_confirmed":True,
        "official_home_team_id":game["teams"]["home"]["team"]["id"],
        "official_away_team_id":game["teams"]["away"]["team"]["id"],
        "venue_id":vid}

def venue_game(g):
    return {"id":g["id"],"date":g["date"],"away":g["away_team"],"home":g["home_team"],
        "awayScore":g["away_score"],"homeScore":g["home_score"],
        "url":"../milb/game.html?id="+g["id"]}

def updated_venues(allgames):
    data=read(VENUES)
    sites=data["venues"]
    sj=next(v for v in sites if v.get("id")=="venue-0132")
    if sj.get("name")!="Excite Ballpark":raise ValueError("San Jose venue identity changed")
    other=[v for v in sites if v.get("id")=="venue-0135"]
    if other:
        stock=other[0]
        if stock["name"]!="Banner Island Ballpark":raise ValueError("Unexpected Stockton venue identity")
    else:
        if any(v.get("name")=="Banner Island Ballpark" for v in sites):
            raise ValueError("Stockton ballpark is already present under another venue ID")
        stock={
          "id":"venue-0135",
          "name":"Banner Island Ballpark",
          "sport":"MiLB",
          "city":"Stockton, CA",
          "address":"404 West Fremont Street, Stockton, CA 95203",
          "lat":37.9548556,"lon":-121.2979556,
          "coordinateConfidence":"High",
          "opened":"2005",
          "capacity":"5,200 (4,200 fixed seats; Stockton Ports official ballpark guide)",
          "occupants":"Stockton Ports minor-league baseball",
          "history":"Opened April 28, 2005, as the Stockton Ports' downtown waterfront home. Also referred to as Stockton Ballpark. Banner Island Ballpark and Stockton Ballpark refer to the same venue, not two separate visits.",
          "sources":["https://www.milb.com/stockton/ballpark/banner-island-ballpark",
                     "https://www.milb.com/stockton/ballpark/contact-us",
                     "https://www.mlb.com/news/featured/visit-banner-island-ballpark-home-of-the-stockton-ports/"],
          "factNote":"First attended June 1, 2021, for the Storm–Ports series; games June 1–6, 2021.",
          "games":[],"visits":0,
        }
        sites.append(stock)
    ids={g["id"] for g in allgames}
    for v in (sj,stock):
        combined={x["id"]:x for x in v["games"]}
        for g in allgames:
            if g.get("venue_id")==v["id"]:
                combined[g["id"]]=venue_game(g)
        v["games"]=sorted(combined.values(),key=lambda x:(x["date"],x["id"]))
        if any(e["id"] not in ids for e in v["games"] if e["id"].startswith("milb-")):
            raise ValueError("Orphan MiLB venue visit")
        v["visits"]=len(v["games"])
        v["firstVisit"]=v["games"][0]["date"]
        v["lastVisit"]=v["games"][-1]["date"]
    sj["factNote"]="Attended August 2, 2015, and six additional Storm games May 25–30, 2021."
    data["venues"]=sorted(sites,key=lambda x:(x["name"],x["id"]))
    data["venueCount"]=len(data["venues"])
    data["mappedGames"]=sum(len(x["games"]) for x in data["venues"])
    data["updated"]=datetime.datetime.now(datetime.timezone.utc).date().isoformat()
    if data["venueCount"]!=135 or data["mappedGames"]!=728:
        raise ValueError(f"Venue counters wrong: {data['venueCount']} venues, {data['mappedGames']} games")
    return data

def refresh_page_counters(venue_data):
    n=venue_data["venueCount"];mapped=venue_data["mappedGames"]
    home=ROOT/"index.html"
    text=home.read_text(encoding="utf8")
    replacements={
        'id="venueCount">134':f'id="venueCount">{n}',
        'id="venueGameCount">716':f'id="venueGameCount">{mapped}',
        'id="venueMapResult">134 attended venues':f'id="venueMapResult">{n} attended venues'
    }
    for old,new in replacements.items():
        if text.count(old)!=1:raise ValueError("Homepage venue count marker missing: "+old)
        text=text.replace(old,new)
    home.write_text(text,encoding="utf8")
    directory=ROOT/"venues"/"index.html"
    content=directory.read_text(encoding="utf8")
    if content.count("134 physical stadiums")!=1 or content.count("all 134 stadiums")!=1:
        raise ValueError("Venue directory count markers changed")
    content=content.replace("134 physical stadiums",f"{n} physical stadiums")
    content=content.replace("all 134 stadiums",f"all {n} stadiums")
    directory.write_text(content,encoding="utf8")

def main():
    current=read(DATA/"games.json")
    previous_rows=read(DATA/"player_stats.json")
    if len(current)!=10:raise ValueError("Batch 2 expected exactly 10 prior games, got "+str(len(current)))
    if any(g["date"] in DATES for g in current):raise ValueError("Batch 2 dates already added; refusing duplicates")
    if any(g["date"]>="2021-05-25" and g["date"]<="2021-06-06" for g in current):
        raise ValueError("Partial overlapping batch")
    existing_gamepks={int(g["source_game_id"]) for g in current}
    newgames=[];newrows=[]
    for date,score,(club,park,city,vid) in zip(DATES,EXPECTED_RESULTS,OPPONENT):
        game=official_game(date,club,score)
        entry=new_entry(date,club,park,city,vid,score,game)
        if entry["source_game_id"] in existing_gamepks:raise ValueError("Duplicate gamePk")
        box=core.fetch(core.API+"/game/"+str(entry["source_game_id"])+"/boxscore")
        rows=core.make_player_rows(entry,game,box)
        for side in ("away","home"):
            players=[r for r in rows if r["side"]==side]
            runs=sum(int(r["batting"]["r"] or 0) for r in players if r.get("batting"))
            if runs!=entry[side+"_score"]:
                raise ValueError(f"Official batting runs did not match the {side} final on {date}: {runs}")
        if len(rows)<20:raise ValueError("Incomplete player rows on "+date)
        newrows.extend(rows)
        newgames.append(entry)
        existing_gamepks.add(entry["source_game_id"])
        print("OFFICIAL_GAME",json.dumps({"date":date,"pk":entry["source_game_id"],"teams":[STORM,club],"final":score,"players":len(rows)}),flush=True)
    if len(newgames)!=12 or len({g["source_game_id"] for g in newgames})!=12:
        raise ValueError("Expected 12 complete unique official MiLB games")
    innings=read(DATA/"inning_scores.json")
    scoring=read(DATA/"scoring_plays.json")
    decisions=read(DATA/"pitching_decisions.json")
    summaries=[]
    patches=collections.defaultdict(dict)
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
        for item in executor.map(details.enrich,newgames):
            summaries.append(item)
            g=next(g for g in newgames if g["id"]==item["game_id"])
            pk=str(g["source_game_id"])
            if item["score_status"]!="verified" or item["play_status"]!="verified" or item["order_status"]!="verified":
                raise ValueError(f"Missing official line/plays/lineups in {g['date']}: "
                                 +str({k:item.get(k+"_status") for k in ["score","play","order"]}))
            innings[pk]=item["scores"]
            scoring[pk]=item["plays"]
            if item["decisions"] is not None:decisions[pk]=item["decisions"]
            patches[g["id"]]=item["order"]
            print("OFFICIAL_DETAIL",json.dumps({k:v for k,v in item.items() if k not in ("scores","plays","decisions","order")}),flush=True)
    for r in newrows:
        patch=patches[r["game_id"]].get((r["side"],str(r["player_id"])))
        if not patch:raise ValueError("Missing official lineup/appearance record "+str(r["player_id"]))
        r.update(patch)
    allgames=sorted(current+newgames,key=lambda g:(g["date"],g["id"]))
    allrows=sorted(previous_rows+newrows,key=lambda r:(r["date"],r["game_id"],r["side"],r["player_id"]))
    if len({g["id"] for g in allgames})!=22 or len({g["source_game_id"] for g in allgames})!=22:
        raise ValueError("Duplicate final MiLB game")
    if len(allrows)!=len(previous_rows)+len(newrows):
        raise ValueError("Stats rows were dropped")
    if any(r["game_id"] not in {g["id"] for g in allgames} for r in allrows):
        raise ValueError("Orphan MiLB player rows")
    venueData=updated_venues(allgames)
    write(DATA/"games.json",allgames)
    write(DATA/"player_stats.json",allrows)
    write(DATA/"inning_scores.json",innings)
    write(DATA/"scoring_plays.json",scoring)
    write(DATA/"pitching_decisions.json",decisions)
    write(VENUES,venueData)
    refresh_page_counters(venueData)
    previous=read(DATA/"game_detail_report.json")
    before=[x for x in previous.get("games",[]) if x.get("game_id") not in {g["id"] for g in newgames}]
    allresults=before+[{k:v for k,v in x.items() if k not in ("order","scores","plays","decisions")} for x in summaries]
    write(DATA/"game_detail_report.json",{
        **previous,"timestamp":datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "games_checked":len(allresults),
        "innings_verified":sum(x.get("score_status")=="verified" for x in allresults),
        "scoring_plays_verified":sum(x.get("play_status")=="verified" for x in allresults),
        "pitcher_order_verified":sum(x.get("order_status")=="verified" for x in allresults),
        "pitching_decisions_verified":sum(x.get("decision_status")=="verified" for x in allresults),
        "games":allresults})
    # Never run College Baseball ↔ MiLB matcher; preserve prior six confirmed links.
    existing_college=(DATA/"college_links.json").read_bytes()
    previous_mlb_links=read(DATA/"player_links.json")
    alumni.main()
    if (DATA/"college_links.json").read_bytes()!=existing_college:
        raise ValueError("Deferred college-to-MiLB links were changed")
    after_mlb=read(DATA/"player_links.json")
    if not {x["milb_id"] for x in previous_mlb_links}.issubset({x["milb_id"] for x in after_mlb}):
        raise ValueError("Previously verified MLB debuts missing after new batch")
    if len(after_mlb)<len(previous_mlb_links):
        raise ValueError("Previously verified MLB player count decreased")
    report={
        "batch":BATCH_NUMBER,"target":12,"verified_games":len(newgames),
        "player_rows_added":len(newrows),"total_games":len(allgames),
        "total_player_rows":len(allrows),"unique_milb_players":len({r["player_id"] for r in allrows}),
        "verified_mlb_alumni":len(after_mlb),
        "also_attended_mlb":sum(x["mlb_seen"] for x in after_mlb),
        "college_links_preserved":len(read(DATA/"college_links.json")),
        "college_matching_deferred":True,
        "venues":venueData["venueCount"],
        "mapped_venue_games":venueData["mappedGames"],
        "new_ballparks":["Banner Island Ballpark"],
        "games":[{"date":g["date"],"id":g["id"],"official_pk":g["source_game_id"],
                   "away_score":g["away_score"],"home_score":g["home_score"],
                   "venue_id":g["venue_id"]} for g in newgames],
    }
    write(DATA/"batch2_report.json",report)
    print("BATCH_2_SUCCESS",json.dumps({k:v for k,v in report.items() if k!="games"}),flush=True)

if __name__=="__main__":main()
