#!/usr/bin/env python3
"""Official May 14 Virginia at Louisville ACC baseball player gamebook."""
import json
from pathlib import Path
from import_sidearm_pilot import scrape
from import_2026_may20_early_sec import verify_metadata,add_lineups
DATA=Path(__file__).resolve().parents[1]/"data"
ID="cb-2026-05-14-virginia-louisville-att0422"
SPEC={
 "source_url":"https://gocards.com/sports/baseball/stats/2026/virginia/boxscore/26032",
 "date":"2026-05-14","away":"Virginia","home":"Louisville",
 "away_score":8,"home_score":3,"away_hits":8,"home_hits":8,
 "away_errors":3,"home_errors":3,
 "away_innings":[0,3,3,0,0,1,1,0,0],
 "home_innings":[0,0,0,0,0,1,0,2,0],
 "winner":"Henry Zatkowski","loser":"Ethan Eberle","save":None,
 "first_pitch":"18:02","attendance_at_venue":2681,
 "lineups":{
  "Virginia":["Eric Becker","Aj Gracia","Joe Tiroly","Sam Harris",
     "Jake Weatherspoon","Harrison Didawick",
     ["Kyle Johnson","Antonio Perrotta"],"Zach Jackson","Noah Murray"],
  "Louisville":["Zion Rose","Griffin Crain","Tague Davis","Jimmy Nugent",
     "Bayram Hot","Lucas Moore","Kade Elam","Ben Slanker","Alex Alicea"],
 }}
def main():
    games=json.loads((DATA/"games.json").read_text())
    players=json.loads((DATA/"player_stats.json").read_text())
    report=json.loads((DATA/"import_report.json").read_text())
    if len(games)!=444:raise ValueError("Expected all 444 attended games")
    game=next(x for x in games if x["id"]==ID)
    prior=[r for r in players if r["game_id"]==ID]
    if prior:
        if game["verification"]!="official_boxscore_verified" or len(prior)<18 or \
           any(x["source_url"]!=SPEC["source_url"] for x in prior):
            raise ValueError("Inconsistent prior source import")
        print("PASS earlier verified May14 Virginia–Louisville player gamebook preserved")
        return
    verify_metadata(game,SPEC)
    new,audit=scrape({**game,**{k:v for k,v in SPEC.items() if k!="lineups"}})
    replacements=add_lineups({(r["game_id"],r["player_id"]) for r in players},new,game,SPEC)
    if len(new)<20:raise ValueError("Partial player source gamebook")
    game.update({
      "source_url":SPEC["source_url"],"verification":"official_boxscore_verified",
      "official_boxscore_status":"verified","score_provenance":"official_boxscore",
      "away_score":8,"home_score":3,"away_hits":8,"home_hits":8,
      "away_errors":3,"home_errors":3,
      "innings":[{"inning":i+1,"away":a,"home":h} for i,(a,h) in
        enumerate(zip(SPEC["away_innings"],SPEC["home_innings"]))],
      "pitching_decisions":{"win":SPEC["winner"],"loss":SPEC["loser"],"save":None},
      "ballpark":"Jim Patterson Stadium","city":"Louisville","state":"KY",
      "neutral_site":False,"game_type":"regular_season","postseason_round":None,
      "source_attendance":SPEC["attendance_at_venue"],
      "first_pitch_local":SPEC["first_pitch"]
    })
    players.extend(new)
    players.sort(key=lambda r:(r["game_id"],r["team"],r.get("batting_slot",99),
      r.get("batting_sub_index",99),r.get("pitching_appearance_index",99),r["player_id"]))
    report.update({
      "official_player_boxscores_imported":sum(g["verification"]=="official_boxscore_verified" for g in games),
      "official_score_and_inning_lines_matched":sum(g["verification"]!="attendance_only" for g in games),
      "official_scoreboard_player_lines_pending":sum(g["verification"]=="official_scoreboard_verified" for g in games),
      "attendance_only_pending_official_verification":sum(g["verification"]=="attendance_only" for g in games),
      "remaining_official_boxscore_work":sum(g["verification"]=="official_scoreboard_verified" for g in games),
      "player_stat_rows":len(players),"unique_player_ids":len({r["player_id"] for r in players}),
      "latest_verified_batch":"ACC Regular Season May 14, 2026 · Virginia at Louisville"
    })
    report.setdefault("additional_official_gamebooks",[]).append({
       "game_id":ID,"source_url":SPEC["source_url"],"verification":"official_boxscore_verified"})
    report["warning"]="444 attendance entries preserved; regular-season player gamebooks are verified against official individual box scores."
    audit["substitution_positions_source_verified"]=replacements
    for fname,v in (("games.json",games),("player_stats.json",players),
       ("import_report.json",report),("2026_may14_virginia_louisville_audit.json",audit)):
        (DATA/fname).write_text(json.dumps(v,ensure_ascii=False,indent=2)+"\n")
    print("PASS Virginia 8 Louisville 3 original official player gamebook",
       len(new),"player rows; complete count",report["official_player_boxscores_imported"])
if __name__=="__main__": main()
