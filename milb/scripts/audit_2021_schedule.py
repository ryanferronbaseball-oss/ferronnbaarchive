#!/usr/bin/env python3
"""Audit the complete official 2021 Storm game schedule for repeatable 12-game imports."""
import collections,datetime,json,pathlib,urllib.parse
import import_batch1 as core
ROOT=pathlib.Path(__file__).resolve().parents[2]
q=urllib.parse.urlencode(dict(sportId=14,teamId=103,startDate="2021-05-04",endDate="2021-09-19"))
api=core.API+"/schedule?"+q
payload=core.fetch(api)
raw=[g for d in payload.get("dates",[]) for g in d.get("games",[])]
found=[]
for g in raw:
 if g.get("status",{}).get("abstractGameState")!="Final":continue
 a=g["teams"]["away"];h=g["teams"]["home"]
 if 103 not in [a["team"]["id"],h["team"]["id"]]:continue
 if a.get("score") is None or h.get("score") is None:continue
 day=g.get("officialDate") or str(g.get("gameDate",""))[:10]
 found.append({"date":day,"game_pk":g["gamePk"],"game_date":g.get("gameDate"),
  "game_number":g.get("gameNumber"),
  "away_team":a["team"]["name"],"home_team":h["team"]["name"],
  "away_id":a["team"]["id"],"home_id":h["team"]["id"],
  "away_score":a["score"],"home_score":h["score"]})
found.sort(key=lambda g:(g["date"],g.get("game_date") or "",g["game_pk"]))
prior=json.loads((ROOT/"milb/data/games.json").read_text())
prepk={g["source_game_id"] for g in prior if g["date"].startswith("2021")}
included=[g for g in found if g["date"]>="2021-05-18"]
remaining=[g for g in included if g["game_pk"] not in prepk]
wins=sum((g["away_id"]==103 and g["away_score"]>g["home_score"]) or (g["home_id"]==103 and g["home_score"]>g["away_score"]) for g in found)
report={"source":"Official MLB StatsAPI 2021 Single-A schedule", "total_season_games":len(found),
 "season_wins":wins,"season_losses":len(found)-wins,
 "excluded_may4_through_16":len([g for g in found if g["date"]<"2021-05-18"]),
 "expected_attended_games":len(included),"already_imported_2021":len(prepk),
 "still_to_import":len(remaining),"remaining_dates":remaining,
 "doubleheaders":{date:len(lst) for date,lst in ((date,[x for x in found if x["date"]==date]) for date in set(g["date"] for g in found)) if len(lst)>1},
 "distinct_home_teams":sorted(set(g["home_team"] for g in found))}
print("OFFICIAL_SCHEDULE_AUDIT",json.dumps({k:v for k,v in report.items() if k!="remaining_dates"},indent=2),flush=True)
if len(found)!=120 or wins!=55 or len(included)!=108 or len(prepk)!=18 or len(remaining)!=90:
 raise ValueError("2021 official schedule does not match expected 120-game and 108-attended scope")
if len({g["game_pk"] for g in found})!=len(found):
 raise ValueError("Duplicate official game primary keys")
if not prepk.issubset({g["game_pk"] for g in included}):
 raise ValueError("An already-imported Storm game is missing from official schedule")
(ROOT/"milb/data/season_2021_audit.json").write_text(json.dumps(report,indent=2)+"\n")
print("AUDIT_SUCCESS: official 120, attended 108, prior 18, remaining 90",flush=True)
