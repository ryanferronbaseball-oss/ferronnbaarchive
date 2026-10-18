#!/usr/bin/env python3
"""Verified source import of May 10, 2026 Little Rock @ UT Martin 16-14 boxscore.

Strictly checks 9 source lineup positions, every substitution, source team
AB/R/H/RBI/BB/K, opposing pitchers' IP/H/R/K, game date and winning pitcher.
"""
from pathlib import Path
import json
from import_sidearm_pilot import scrape
from import_2026_may20_early_sec import verify_metadata,add_lineups
DATA=Path(__file__).resolve().parents[1]/"data"
ID="cb-2026-05-10-little-rock-ut-martin-att0421"
SPEC={
 "source_url":"https://utmsports.com/sports/baseball/stats/2026/little-rock/boxscore/13609",
 "date":"2026-05-10","away":"Little Rock","home":"UT Martin",
 "away_score":16,"home_score":14,"away_hits":23,"home_hits":13,
 "away_errors":5,"home_errors":3,
 "away_innings":[0,0,0,10,0,3,0,1,2],
 "home_innings":[1,0,5,2,5,0,0,1,0],
 "winner":"Tag Andrews","loser":"Gabe Bryant","save":None,
 "first_pitch":"13:00","attendance_at_venue":246,
 "lineups":{
   "Little Rock":["Jerdy Lopez","Kade Smith","Angel Cano",
      ["Blake Simpson","Michael O'brien"],"Nolan Freund",
      ["Ty Rhoades","Austin Coyle"],"Nico Baumbach",
      ["Cade Martin","Trey Hill"],"Cooper Chaplain"],
   "UT Martin":["Tj Grines","Andrew Lawrence","Colten Payton",
      "Tj Dunsford","Andrew Davis","Jt Popick","Cameron Greene",
      "Tommy Koch","Garner Anderson"]
 }}
def main():
    games=json.loads((DATA/"games.json").read_text())
    stats=json.loads((DATA/"player_stats.json").read_text())
    report=json.loads((DATA/"import_report.json").read_text())
    if len(games)!=444:raise ValueError("Not original 444 attended games")
    match=[g for g in games if g["id"]==ID]
    if len(match)!=1:raise ValueError("May10 original unique attendance ID missing")
    game=match[0]
    prior=[r for r in stats if r["game_id"]==ID]
    if prior:
        if (game["verification"]!="official_boxscore_verified" or len(prior)<26 or
            any(r.get("source_url")!=SPEC["source_url"] for r in prior)):
            raise ValueError("Previously staged stats differ from audited source")
        print("PASS already source-verified May10 Little Rock/UT Martin")
        return
    verify_metadata(game,SPEC)
    rows,audit=scrape({**game,**{k:v for k,v in SPEC.items() if k!="lineups"}})
    replacements=add_lineups(
        {(r["game_id"],r["player_id"]) for r in stats},rows,game,SPEC)
    if len(rows)<29:raise ValueError("Too few independent source hitters/pitchers")
    game.update({
      "verification":"official_boxscore_verified","source_url":SPEC["source_url"],
      "official_boxscore_status":"verified","score_provenance":"official_boxscore",
      "away_score":16,"home_score":14,"away_hits":23,"home_hits":13,
      "away_errors":5,"home_errors":3,
      "innings":[{"inning":i+1,"away":a,"home":h} for i,(a,h) in
          enumerate(zip(SPEC["away_innings"],SPEC["home_innings"]))],
      "pitching_decisions":{"win":"Tag Andrews","loss":"Gabe Bryant","save":None},
      "ballpark":"Skyhawk Field","city":"Martin","state":"TN",
      "neutral_site":False,"game_type":"regular_season","postseason_round":None,
      "source_attendance":246,"first_pitch_local":"13:00"
    })
    stats.extend(rows)
    stats.sort(key=lambda r:(r["game_id"],r["team"],r.get("batting_slot",99),
      r.get("batting_sub_index",99),r.get("pitching_appearance_index",99),r["player_id"]))
    report.update({
      "official_player_boxscores_imported":sum(g["verification"]=="official_boxscore_verified" for g in games),
      "official_score_and_inning_lines_matched":sum(g["verification"]!="attendance_only" for g in games),
      "official_scoreboard_player_lines_pending":sum(g["verification"]=="official_scoreboard_verified" for g in games),
      "attendance_only_pending_official_verification":sum(g["verification"]=="attendance_only" for g in games),
      "remaining_official_boxscore_work":sum(g["verification"]=="official_scoreboard_verified" for g in games),
      "player_stat_rows":len(stats),"unique_player_ids":len({r["player_id"] for r in stats}),
      "latest_verified_batch":"OVC Regular Season May 10, 2026 · Little Rock at UT Martin"
    })
    report.setdefault("additional_official_gamebooks",[]).append({
      "game_id":ID,"source_url":SPEC["source_url"],"verification":"official_boxscore_verified"})
    report["warning"]="All 444 attended games retained, only fully confirmed gamebooks assigned player stats."
    audit["source_order_substitutions"]=replacements
    for name,value in (("games.json",games),("player_stats.json",stats),
        ("import_report.json",report),("2026_may10_little_rock_utmartin_audit.json",audit)):
        (DATA/name).write_text(json.dumps(value,ensure_ascii=False,indent=2)+"\n")
    print("PASS official May10 Little Rock 16 at UT Martin 14",
      len(rows),"game-player rows;",report["official_player_boxscores_imported"],"full games")
if __name__=="__main__": main()
