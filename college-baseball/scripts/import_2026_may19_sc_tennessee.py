#!/usr/bin/env python3
"""Import official May 19 South Carolina–Tennessee SEC Tournament gamebook."""
import json
from pathlib import Path
from import_sidearm_pilot import scrape
from import_2026_may20_early_sec import verify_metadata, add_lineups

DATA=Path(__file__).resolve().parents[1]/"data"
GAME_ID="cb-2026-05-19-south-carolina-tennessee-att0427"
SPEC={
  "source_url":"https://utsports.com/sports/baseball/stats/2026/south-carolina/boxscore/29760",
  "date":"2026-05-19","away":"South Carolina","home":"Tennessee",
  "away_score":6,"home_score":11,"away_hits":11,"home_hits":15,
  "away_errors":3,"home_errors":1,
  "away_innings":[0,0,3,0,0,0,3,0,0],
  "home_innings":[2,0,6,1,0,0,0,2,None],
  "winner":"Cam Appenzeller","loser":"Brandon Stone","save":"Will Haas",
  "lineups":{
    "South Carolina":["Patrick Evans","Kj Scobey","Talmadge Lecroy",
      "Jake Randolph",["Will Craddock","Logan Sutter"],
      "Ethan Lizama","Luke Yuhasz","Dawson Harman","Tyler Bak"],
    "Tennessee":["Garrett Wright","Blake Grimmer","Henry Ford",
      "Trent Grindlinger","Levi Clark","Blaine Brown","Manny Marin",
      ["Nate Eisfelder","Ariel Antigua"],"Jay Abernathy"],
  },
  "first_pitch":"17:36","attendance_at_venue":7617,
}

def main():
    games=json.loads((DATA/"games.json").read_text())
    players=json.loads((DATA/"player_stats.json").read_text())
    report=json.loads((DATA/"import_report.json").read_text())
    if len(games)!=444:raise ValueError("Attendance history incomplete")
    existing=[r for r in players if r["game_id"]==GAME_ID]
    game=next(g for g in games if g["id"]==GAME_ID)
    if existing:
        if (game["verification"]!="official_boxscore_verified"
            or len(existing)<18
            or any(r["source_url"]!=SPEC["source_url"] for r in existing)):
            raise ValueError("Prior official source does not match")
        print("PASS May 19 South Carolina Tennessee official game already complete")
        return
    verify_metadata(game,SPEC)
    people,audit=scrape({**game,**{k:v for k,v in SPEC.items() if k!="lineups"}})
    existing_keys={(r["game_id"],r["player_id"]) for r in players}
    replacements=add_lineups(existing_keys,people,game,SPEC)
    if len(people)<20:raise ValueError("Incomplete official player records")
    for field in ("away_score","home_score","away_hits","home_hits","away_errors","home_errors"):
        game[field]=SPEC[field]
    game.update({
      "source_url":SPEC["source_url"],"verification":"official_boxscore_verified",
      "official_boxscore_status":"verified","score_provenance":"official_boxscore",
      "innings":[{"inning":i+1,"away":a,"home":h} for i,(a,h) in
        enumerate(zip(SPEC["away_innings"],SPEC["home_innings"]))],
      "pitching_decisions":{"win":SPEC["winner"],"loss":SPEC["loser"],"save":SPEC["save"]},
      "ballpark":"Hoover Met","city":"Hoover","state":"AL","neutral_site":True,
      "game_type":"conference_tournament","postseason_round":"SEC Tournament · First Round",
      "source_attendance":SPEC["attendance_at_venue"],
      "first_pitch_local":SPEC["first_pitch"]
    })
    players.extend(people)
    players.sort(key=lambda r:(r["game_id"],r["team"],r.get("batting_slot",99),
      r.get("batting_sub_index",99),r.get("pitching_appearance_index",99),r["player_id"]))
    report.update({
      "official_player_boxscores_imported":sum(g["verification"]=="official_boxscore_verified" for g in games),
      "official_score_and_inning_lines_matched":sum(g["verification"]!="attendance_only" for g in games),
      "official_scoreboard_player_lines_pending":sum(g["verification"]=="official_scoreboard_verified" for g in games),
      "attendance_only_pending_official_verification":sum(g["verification"]=="attendance_only" for g in games),
      "remaining_official_boxscore_work":sum(g["verification"]=="official_scoreboard_verified" for g in games),
      "player_stat_rows":len(players),"unique_player_ids":len({r["player_id"] for r in players}),
      "latest_verified_batch":"SEC Tournament May 19 2026 · South Carolina vs Tennessee"
    })
    report["warning"]="444 attendance records retained; official player stats only after full source reconciliation."
    report.setdefault("additional_official_gamebooks",[]).append({
       "game_id":GAME_ID,"source_url":SPEC["source_url"],"verification":"official_boxscore_verified"})
    audit["lineup_substitutions_source_verified"]=replacements
    for file,records in (("games.json",games),("player_stats.json",players),
      ("import_report.json",report),("2026_sec_may19_south_carolina_tennessee_audit.json",audit)):
        (DATA/file).write_text(json.dumps(records,ensure_ascii=False,indent=2)+"\n")
    print("PASS official May19 South Carolina 6 Tennessee 11,",
          len(people),"verified player game rows; full total",
          report["official_player_boxscores_imported"])
if __name__=="__main__":main()
