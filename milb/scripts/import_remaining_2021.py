#!/usr/bin/env python3
"""Complete the attended 2021 Lake Elsinore Storm season in 12-game commits.

Official, idempotent, resumable importer:
- Season has 120 official Single-A games, of which May 4–16 (12) are excluded.
- The 108 remaining games are part of user-confirmed attendance.
- Every batch (12; last can be 6) is validated BEFORE it is committed.
- Only MiLB batting/pitching logs and MiLB->MLB debut links are updated.
- College Baseball <-> MiLB attendance links remain untouched until the end.
- Venues use ONE record per physical park, including mixed college/MiLB use.
"""
import collections
import concurrent.futures
import datetime
import json
import pathlib
import re
import subprocess
import sys
import urllib.parse

import import_batch1 as core
import enrich_game_details as details
import import_mlb_alumni as alumni

ROOT=pathlib.Path(__file__).resolve().parents[2]
DATA=ROOT/"milb"/"data"
VENUES=ROOT/"venues"/"data"/"venues.json"
STORM_ID=103
STORM="Lake Elsinore Storm"
BATCH_SIZE=12
SEASON_FIRST="2021-05-04"
ATTENDANCE_FIRST="2021-05-18"
SEASON_LAST="2021-09-19"
ALLOWED_TEAMS={
 "Lake Elsinore Storm":("The Diamond","Lake Elsinore, CA","venue-0133"),
 "Rancho Cucamonga Quakes":("LoanMart Field","Rancho Cucamonga, CA","venue-0131"),
 "San Jose Giants":("Excite Ballpark","San Jose, CA","venue-0132"),
 "Stockton Ports":("Banner Island Ballpark","Stockton, CA","venue-0005"),
 "Inland Empire 66ers":("San Manuel Stadium","San Bernardino, CA","venue-0135"),
 "Visalia Rawhide":("Valley Strong Ballpark","Visalia, CA","venue-0136"),
}
NEW_VENUES={
 "Inland Empire 66ers":{
  "id":"venue-0135","name":"San Manuel Stadium","sport":"MiLB",
  "city":"San Bernardino, CA",
  "address":"280 South E Street, San Bernardino, CA 92401",
  "lat":34.09722,"lon":-117.29528,
  "coordinateConfidence":"High","opened":"1996",
  "capacity":"8,000 (official Inland Empire 66ers ballpark guide)",
  "occupants":"Inland Empire 66ers minor-league baseball",
  "history":"Opened in August 1996 as The Ranch, also called San Bernardino Stadium and Arrowhead Credit Union Park before taking the San Manuel Stadium name in 2012. Home to the Inland Empire 66ers, including the 2021 Single-A season. All names describe the same ballpark.",
  "sources":["https://www.milb.com/inland-empire/ballpark",
             "https://www.mlb.com/news/featured/visit-san-manuel-stadium-home-of-the-inland-empire-66ers/",
             "https://www.milb.com/inland-empire/ballpark/club-info"],
  "factNote":"First attended June 15, 2021, during the Storm's series at Inland Empire.",
  "games":[],"visits":0,
 },
 "Visalia Rawhide":{
  "id":"venue-0136","name":"Valley Strong Ballpark","sport":"MiLB",
  "city":"Visalia, CA",
  "address":"300 North Giddings Street, Visalia, CA 93291",
  "lat":36.33242,"lon":-119.30458,
  "coordinateConfidence":"High","opened":"1946",
  "capacity":"2,468 (1,888 fixed seats; venue capacity guide)",
  "occupants":"Visalia Rawhide minor-league baseball",
  "history":"Opened in 1946 as Recreation Park (later Recreation Ballpark). The same long-serving Visalia baseball stadium was renamed Valley Strong Ballpark; it hosted the Rawhide throughout the 2021 Single-A season.",
  "sources":["https://www.milb.com/visalia/ballpark",
             "https://www.mlb.com/astros/news/featured/visit-valley-strong-ballpark-home-of-the-visalia-rawhide",
             "https://www.baseball-reference.com/bullpen/Recreation_Park_%28Visalia%29"],
  "factNote":"Your excluded opening-week 2021 games at Visalia are not imported; the September return visit is recorded.",
  "games":[],"visits":0,
 }
}

def read(path,default=None):
 try:return json.loads(path.read_text(encoding="utf8"))
 except FileNotFoundError:
  if default is not None:return default
  raise

def save(path,value):
 path.write_text(json.dumps(value,indent=2,ensure_ascii=False)+"\n",encoding="utf8")

def run(cmd):
 subprocess.run(cmd,cwd=ROOT,check=True)

def official_schedule():
 q=urllib.parse.urlencode({"sportId":14,"teamId":STORM_ID,"startDate":SEASON_FIRST,"endDate":SEASON_LAST})
 result=core.fetch(core.API+"/schedule?"+q)
 matches=[]
 for d in result.get("dates",[]):
  for g in d.get("games",[]):
   if g.get("status",{}).get("abstractGameState")!="Final":continue
   away,home=g.get("teams",{}).get("away",{}),g.get("teams",{}).get("home",{})
   if STORM_ID not in (away.get("team",{}).get("id"),home.get("team",{}).get("id")):continue
   if away.get("score") is None or home.get("score") is None:continue
   if home.get("team",{}).get("name") not in ALLOWED_TEAMS:
    raise ValueError("Unknown home team / venue: "+str(home.get("team")))
   date=g.get("officialDate") or g["gameDate"][:10]
   if not (SEASON_FIRST<=date<=SEASON_LAST):continue
   g["_date"]=date
   matches.append(g)
 matches.sort(key=lambda g:(g["_date"],g.get("gameDate") or "",g["gamePk"]))
 if len(matches)!=120 or len({g["gamePk"] for g in matches})!=120:
  raise ValueError(f"Official 2021 schedule expected 120 unique games, got {len(matches)}")
 wins=sum((g["teams"]["away"]["team"]["id"]==STORM_ID and g["teams"]["away"]["score"]>g["teams"]["home"]["score"]) or
          (g["teams"]["home"]["team"]["id"]==STORM_ID and g["teams"]["home"]["score"]>g["teams"]["away"]["score"]) for g in matches)
 if wins!=55:raise ValueError(f"Official season record expected 55–65, got {wins}–{120-wins}")
 included=[g for g in matches if g["_date"]>=ATTENDANCE_FIRST]
 if len(included)!=108:raise ValueError("Expected 108 user-approved attended Storm games")
 return included

def slug(team):
 return {"Lake Elsinore Storm":"storm","Rancho Cucamonga Quakes":"quakes",
         "San Jose Giants":"giants","Stockton Ports":"ports",
         "Inland Empire 66ers":"66ers","Visalia Rawhide":"rawhide"}[team]

def make_id(game,season):
 day=game["_date"]
 a=game["teams"]["away"]["team"]["name"]
 h=game["teams"]["home"]["team"]["name"]
 cluster=[g for g in season if g["_date"]==day and
          g["teams"]["away"]["team"]["name"]==a and g["teams"]["home"]["team"]["name"]==h]
 suffix=""
 if len(cluster)>1:
  cluster.sort(key=lambda g:(g.get("gameDate") or "",g["gamePk"]))
  suffix="-g"+str(next(i+1 for i,g in enumerate(cluster) if g["gamePk"]==game["gamePk"]))
 return f"milb-{day}-{slug(a)}-{slug(h)}{suffix}"

def match_game(game,season):
 home=game["teams"]["home"]
 away=game["teams"]["away"]
 club=home["team"]["name"]
 ballpark,city,venueid=ALLOWED_TEAMS[club]
 if not (away["team"]["id"]==STORM_ID or home["team"]["id"]==STORM_ID):
  raise ValueError("Official game does not feature Lake Elsinore")
 if club==STORM and home["team"]["id"]!=STORM_ID:
  raise ValueError("Official home team ID not matched")
 if any(int(side["score"])<0 for side in (home,away)):
  raise ValueError("Negative final score")
 return {
  "id":make_id(game,season),"date":game["_date"],
  "away_team":away["team"]["name"],"home_team":club,
  "away_score":away["score"],"home_score":home["score"],
  "level":"Single-A","venue":ballpark,"city":city,
  "source_game_id":game["gamePk"],
  "source_url":"https://www.milb.com/gameday/"+str(game["gamePk"]),
  "box_score_status":"verified","attendance_confirmed":True,
  "official_home_team_id":home["team"]["id"],
  "official_away_team_id":away["team"]["id"],
  "venue_id":venueid,
 }

def venue_game(g):
 return {"id":g["id"],"date":g["date"],"away":g["away_team"],"home":g["home_team"],
         "awayScore":g["away_score"],"homeScore":g["home_score"],
         "url":"../milb/game.html?id="+g["id"]}

def sync_venues(games):
 data=read(VENUES)
 all_venues=data["venues"]
 byid={v["id"]:v for v in all_venues}
 touched={g["venue_id"] for g in games if g["date"].startswith("2021")}
 for club,meta in NEW_VENUES.items():
  vid=meta["id"]
  if vid not in touched or vid in byid:continue
  if any(v["name"]==meta["name"] for v in all_venues):
   raise ValueError("Duplicate physical stadium detected for "+meta["name"])
  copied=json.loads(json.dumps(meta))
  all_venues.append(copied);byid[vid]=copied
 for vid in touched:
  if vid not in byid:raise ValueError("Unknown venue ID "+vid)
  v=byid[vid]
  vg={r["id"]:r for r in v["games"]}
  for g in games:
   if g["venue_id"]==vid:
    vg[g["id"]]=venue_game(g)
  # A single stadium may hold both NCAA and MiLB games.
  if any(r["id"].startswith("cb-") for r in vg.values()) and any(r["id"].startswith("milb-") for r in vg.values()):
   v["sports"]=sorted(set((v.get("sports") or [v["sport"]])+["College Baseball","MiLB"]))
  v["games"]=sorted(vg.values(),key=lambda r:(r["date"],r["id"]))
  v["visits"]=len(v["games"])
  v["firstVisit"]=v["games"][0]["date"]
  v["lastVisit"]=v["games"][-1]["date"]
 data["venues"]=sorted(all_venues,key=lambda v:(v["name"],v["id"]))
 data["venueCount"]=len(data["venues"])
 data["mappedGames"]=sum(v["visits"] for v in data["venues"])
 data["updated"]=datetime.datetime.now(datetime.timezone.utc).date().isoformat()
 if data["mappedGames"]!=706+len(games):
  raise ValueError(f"Venue attendance expected {706+len(games)} mapped visits; got {data['mappedGames']}")
 if not (134<=data["venueCount"]<=136):
  raise ValueError("Venue count unexpectedly changed")
 if any(len(v["games"])!=v["visits"] for v in data["venues"]):
  raise ValueError("Inconsistent venue visits")
 return data

def update_html_counts(data):
 home=ROOT/"index.html"
 text=home.read_text(encoding="utf8")
 for key,number in (("venueCount",data["venueCount"]),("venueGameCount",data["mappedGames"])):
  pat=r'(id="'+key+r'">)\d+'
  new,count=re.subn(pat,lambda m:m.group(1)+str(number),text)
  if count!=1:raise ValueError("Homepage venue number not found "+key)
  text=new
 pattern=r'(id="venueMapResult">)\d+( attended venues)'
 text,c=re.subn(pattern,lambda m:m.group(1)+str(data["venueCount"])+m.group(2),text)
 if c!=1:raise ValueError("Missing homepage map count")
 home.write_text(text,encoding="utf8")
 page=ROOT/"venues"/"index.html"
 body=page.read_text(encoding="utf8")
 body,c=re.subn(r'(Browse all )\d+( stadiums)',lambda m:m.group(1)+str(data["venueCount"])+m.group(2),body)
 if c!=1:raise ValueError("Venue metadata heading missing")
 body,c=re.subn(r'\d+( physical stadiums)',lambda m:str(data["venueCount"])+m.group(1),body)
 if c!=1:raise ValueError("Venue landing heading missing")
 page.write_text(body,encoding="utf8")

def verify_games(games,rows):
 uniqueIDs={g["id"] for g in games}
 gamepks={g["source_game_id"] for g in games}
 if len(uniqueIDs)!=len(games) or len(gamepks)!=len(games):
  raise ValueError("Duplicate game slug or source gamePk")
 if any(r["game_id"] not in uniqueIDs for r in rows):
  raise ValueError("Orphan MiLB stat line")
 if len({(r["game_id"],r["side"],r["player_id"]) for r in rows})!=len(rows):
  raise ValueError("Duplicate per-side player boxscore line")
 if any(g["date"]<ATTENDANCE_FIRST for g in games if g["date"].startswith("2021")):
  raise ValueError("Excluded early-May Storm game included")

def verify_and_import(batch,season,existing,previous_rows):
 oldpks={g["source_game_id"] for g in existing}
 entries=[];newrows=[]
 # Re-use core import to keep exact MLBAM ids, missing-value semantics, and official lineups.
 for match in batch:
  entry=match_game(match,season)
  if entry["id"] in {g["id"] for g in existing} or entry["source_game_id"] in oldpks:
   raise ValueError("Batch duplicates a previously loaded game")
  rows=core.make_player_rows(entry,match,
      core.fetch(core.API+"/game/"+str(match["gamePk"])+"/boxscore"))
  for side in ("away","home"):
   runs=sum(int(r["batting"].get("r") or 0) for r in rows if r["side"]==side and r.get("batting"))
   if runs!=entry[side+"_score"]:
    raise ValueError(f"{entry['date']} {side} official batting runs {runs} do not match game score")
  if len(rows)<18:raise ValueError("Incomplete player boxscore on "+entry["date"])
  entries.append(entry);newrows.extend(rows)
  print("VERIFIED_GAME",json.dumps({"id":entry["id"],"pk":entry["source_game_id"],"score":[entry["away_score"],entry["home_score"]],"players":len(rows)}),flush=True)
 innings=read(DATA/"inning_scores.json",{})
 plays=read(DATA/"scoring_plays.json",{})
 decisions=read(DATA/"pitching_decisions.json",{})
 results=[];patches=collections.defaultdict(dict)
 with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
  for item in pool.map(details.enrich,entries):
   results.append(item)
   g=next(g for g in entries if g["id"]==item["game_id"])
   if any(item.get(k+"_status")!="verified" for k in ("score","play","order")):
    raise ValueError("Official play/lineup/inning verification failed: "+str({k:item.get(k+"_status") for k in ("score","play","order")}))
   pk=str(g["source_game_id"])
   innings[pk]=item["scores"];plays[pk]=item["plays"]
   if item["decisions"] is not None:decisions[pk]=item["decisions"]
   patches[g["id"]]=item["order"]
 for r in newrows:
  patch=patches[r["game_id"]].get((r["side"],str(r["player_id"])))
  if patch is None:raise ValueError("Missing official appearance order for player "+str(r["player_id"]))
  r.update(patch)
 allgames=sorted(existing+entries,key=lambda g:(g["date"],g["id"]))
 allrows=sorted(previous_rows+newrows,key=lambda r:(r["date"],r["game_id"],r["side"],r["player_id"]))
 verify_games(allgames,allrows)
 venues=sync_venues(allgames)
 previous=read(DATA/"game_detail_report.json")
 previousResults={item["game_id"]:item for item in previous.get("games",[])}
 for item in results:
  previousResults[item["game_id"]]={k:v for k,v in item.items() if k not in ("order","scores","plays","decisions")}
 fullResults=list(previousResults.values())
 detail={
  **previous,
  "timestamp":datetime.datetime.now(datetime.timezone.utc).isoformat(),
  "games_checked":len(fullResults),
  "innings_verified":sum(x.get("score_status")=="verified" for x in fullResults),
  "scoring_plays_verified":sum(x.get("play_status")=="verified" for x in fullResults),
  "pitcher_order_verified":sum(x.get("order_status")=="verified" for x in fullResults),
  "pitching_decisions_verified":sum(x.get("decision_status")=="verified" for x in fullResults),
  "games":fullResults
 }
 if detail["games_checked"]!=len(allgames):
  raise ValueError("Incomplete game detail coverage")
 save(DATA/"games.json",allgames)
 save(DATA/"player_stats.json",allrows)
 save(DATA/"inning_scores.json",innings)
 save(DATA/"scoring_plays.json",plays)
 save(DATA/"pitching_decisions.json",decisions)
 save(DATA/"game_detail_report.json",detail)
 save(VENUES,venues)
 update_html_counts(venues)
 return entries,newrows,venues

def preserve_previous_draft_records(old):
 current=read(DATA/"mlb_alumni_seed.json")
 byId={x["mlb_player_id"]:x for x in old.get("players",[]) if x.get("draft_verified") is True and x.get("draft_pick") is not None}
 for row in current["players"]:
  before=byId.get(row["mlb_player_id"])
  if before and not row.get("draft_verified"):
   for key in ("draft_year","draft_round","draft_pick","draft_team","draft_verified"):
    row[key]=before[key]
 save(DATA/"mlb_alumni_seed.json",current)
 audit=read(DATA/"mlb_status_audit.json")
 pending=[r["mlb_player_id"] for r in current["players"] if not r.get("draft_verified")]
 audit["draft_details_pending"]=len(pending)
 audit["draft_pending_ids"]=pending
 save(DATA/"mlb_status_audit.json",audit)

def commit(batchNo,entries,rows,venues,allgames,allrows,remaining):
 audit=read(DATA/"mlb_status_audit.json")
 if read(DATA/"college_links.json")!=COLLEGE_LINKS_ORIGINAL:
  raise ValueError("Deferred college-to-MiLB matching changed")
 report={
  "batch":batchNo,
  "target":BATCH_SIZE,
  "verified_games":len(entries),
  "player_rows_added":len(rows),
  "total_games":len(allgames),
  "total_player_rows":len(allrows),
  "unique_milb_players":len({r["player_id"] for r in allrows}),
  "official_mlb_debuts":audit["official_mlb_debuts"],
  "mlb_players_also_witnessed":audit["also_attended_in_mlb"],
  "college_matching_deferred":True,
  "college_links_preserved":len(COLLEGE_LINKS_ORIGINAL),
  "venue_count":venues["venueCount"],
  "venue_game_links":venues["mappedGames"],
  "remaining_storm_2021_games":remaining,
  "games":[{"id":g["id"],"date":g["date"],"source_game_id":g["source_game_id"],"venue_id":g["venue_id"]} for g in entries]
 }
 save(DATA/f"batch{batchNo}_report.json",report)
 save(DATA/"season_2021_import_progress.json",{
  "last_completed_batch":batchNo,
  "official_2021_season_games":120,
  "approved_attended_2021_games":108,
  "2021_games_imported":108-remaining,
  "2021_games_remaining":remaining,
  "full_2021_season_complete":remaining==0,
  "all_milb_games_imported":len(allgames),
  "next_stage":"Run cross-level College Baseball ↔ MiLB identity audit after completion" if remaining==0 else "Import next 12 official MiLB games",
  "college_matching_deferred":True,
  "updated":datetime.datetime.now(datetime.timezone.utc).isoformat(),
 })
 # Keep all changes in the current batch together. Every commit is an independently
 # valid 12-game archive snapshot, not a partial placeholder import.
 tostage=[
  "milb/data/games.json","milb/data/player_stats.json",
  "milb/data/inning_scores.json","milb/data/scoring_plays.json","milb/data/pitching_decisions.json",
  "milb/data/game_detail_report.json","milb/data/player_links.json",
  "milb/data/mlb_alumni_seed.json","milb/data/mlb_status_audit.json",
  f"milb/data/batch{batchNo}_report.json","milb/data/season_2021_import_progress.json",
  "venues/data/venues.json","index.html","venues/index.html"
 ]
 run(["git","add",*tostage])
 run(["git","commit","-m",f"MiLB Batch {batchNo}: {len(entries)} verified attended Storm games, MLB alumni and venue updates"])
 run(["git","pull","--rebase","origin","main"])
 run(["git","push","origin","HEAD:main"])
 print("PUBLISHED_BATCH",json.dumps({k:v for k,v in report.items() if k!="games"}),flush=True)

def main():
 season=official_schedule()
 initial=read(DATA/"games.json")
 imported2021=[g for g in initial if g["date"].startswith("2021") and g.get("attendance_confirmed")]
 pks={g["source_game_id"] for g in imported2021}
 officialpks={g["gamePk"] for g in season}
 if not pks.issubset(officialpks):
  raise ValueError("An existing attended 2021 game is not on the official season schedule")
 if not (18<=len(pks)<=108):
  raise ValueError("Existing witnessed 2021 game count outside the approved scope")
 if len(initial)-len(imported2021)!=4:
  raise ValueError("Four non-2021 MiLB games must remain intact")
 remaining=[g for g in season if g["gamePk"] not in pks]
 print("RESUME_SCOPE",json.dumps({"verified2021":len(pks),"remaining":len(remaining),
    "planned_batches":(len(remaining)+BATCH_SIZE-1)//BATCH_SIZE,
    "venues":sorted(set(g["teams"]["home"]["team"]["name"] for g in remaining))}),flush=True)
 if "--plan" in sys.argv:return
 if "--all" not in sys.argv:
  raise ValueError("Specify --all for autonomous twelve-game commits, or --plan")
 if not remaining:
  print("ALL_2021_STORM_GAMES_IMPORTED",flush=True);return
 baseCount=len(pks)
 batchNo=3+(baseCount-18)//12
 processed=0
 while remaining:
  batch=remaining[:BATCH_SIZE]
  before=read(DATA/"games.json")
  rows=read(DATA/"player_stats.json")
  collegeBefore=read(DATA/"college_links.json")
  alumniBefore=read(DATA/"mlb_alumni_seed.json")
  entries,newrows,venues=verify_and_import(batch,season,before,rows)
  oldLinks=read(DATA/"player_links.json")
  alumni.main()
  preserve_previous_draft_records(alumniBefore)
  if read(DATA/"college_links.json")!=collegeBefore:
   raise ValueError("College crossover changed during deferred matching")
  newLinks=read(DATA/"player_links.json")
  if not {r["milb_id"] for r in oldLinks}.issubset({r["milb_id"] for r in newLinks}):
   raise ValueError("Previously verified MLB alumni vanished")
  processed+=len(entries)
  remaining=remaining[len(batch):]
  allgames=read(DATA/"games.json")
  allrows=read(DATA/"player_stats.json")
  if len(allgames)!=len(before)+len(entries) or len(allrows)!=len(rows)+len(newrows):
   raise ValueError("Batch totals did not reconcile")
  if len([g for g in allgames if g["date"].startswith("2021")])!=baseCount+processed:
   raise ValueError("Incomplete running 2021 attendance count")
  commit(batchNo,entries,newrows,venues,allgames,allrows,len(remaining))
  batchNo+=1
 print("ALL_APPROVED_2021_STORM_GAMES_PUBLISHED",flush=True)

COLLEGE_LINKS_ORIGINAL=read(DATA/"college_links.json")
if __name__=="__main__":main()
