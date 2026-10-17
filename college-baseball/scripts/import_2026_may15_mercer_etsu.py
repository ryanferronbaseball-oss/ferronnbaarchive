#!/usr/bin/env python3
"""Audit and import official May 15 Mercer at ETSU SoCon gamebook.

Two-way Braydon Kersey is intentionally a single player game record with
both batting and pitching stats; substitutes remain in their source slots.
"""
import json
from pathlib import Path
from import_sidearm_pilot import scrape
from import_2026_may20_early_sec import verify_metadata,add_lineups
DATA=Path(__file__).resolve().parents[1]/"data"
ID="cb-2026-05-15-mercer-east-tennessee-state-att0423"
SPEC={
 "source_url":"https://etsubucs.com/sports/baseball/stats/2026/mercer/boxscore/12578",
 "date":"2026-05-15","away":"Mercer","home":"East Tennessee State",
 "away_score":9,"home_score":7,"away_hits":11,"home_hits":10,
 "away_errors":1,"home_errors":0,
 "away_innings":[0,0,0,2,2,1,3,1,0],
 "home_innings":[0,0,0,4,2,0,0,1,0],
 "winner":"Andrew Garnett","loser":"Reid Brosnan","save":"Braydon Kersey",
 "first_pitch":"14:00","attendance_at_venue":502,
 "lineups":{
  "Mercer":["Logan Shepherd","Chris Katz",["Eli Stephens","Nathan Rowland"],
     "Brant Baughcum","Braydon Kersey","Dylan LaPointe","Michael Graziano",
     "Drew Johnson","Ethan Buffone"],
  "East Tennessee State":["Nate Conner","Henry Ferguson","Tristan Curless",
     "Jamie Palmese","Ian Guanzon","Gabe Juarez","Joey Little","Mason Ault","Andrew Hill"]
 }}
def main():
    games=json.loads((DATA/"games.json").read_text())
    players=json.loads((DATA/"player_stats.json").read_text())
    report=json.loads((DATA/"import_report.json").read_text())
    if len(games)!=444:raise ValueError("Attended game master lost rows")
    game=next(g for g in games if g["id"]==ID)
    earlier=[r for r in players if r["game_id"]==ID]
    if earlier:
        if (game["verification"]!="official_boxscore_verified" or len(earlier)<20
            or any(r["source_url"]!=SPEC["source_url"] for r in earlier)):
            raise ValueError("Existing complete Mercer gamebook inconsistent")
        print("PASS previous official Mercer/ETSU player source preserved")
        return
    verify_metadata(game,SPEC)
    records,audit=scrape({**game,**{k:v for k,v in SPEC.items() if k!="lineups"}})
    subs=add_lineups({(r["game_id"],r["player_id"]) for r in players},
      records,game,SPEC)
    twoway=[r for r in records if r["team"]=="Mercer" and r["player"]=="Braydon Kersey"]
    if len(twoway)!=1 or not all(k in twoway[0] for k in ("batting","pitching")):
        raise ValueError("Mercer Kersey batting/pitching must belong to one player ID")
    for key in ("away_score","home_score","away_hits","home_hits","away_errors","home_errors"):
        game[key]=SPEC[key]
    game.update({
      "verification":"official_boxscore_verified","source_url":SPEC["source_url"],
      "official_boxscore_status":"verified","score_provenance":"official_boxscore",
      "innings":[{"inning":i+1,"away":a,"home":h} for i,(a,h) in
          enumerate(zip(SPEC["away_innings"],SPEC["home_innings"]))],
      "pitching_decisions":{"win":SPEC["winner"],"loss":SPEC["loser"],"save":SPEC["save"]},
      "ballpark":"Thomas Stadium","city":"Johnson City","state":"TN",
      "neutral_site":False,"game_type":"regular_season","postseason_round":None,
      "source_attendance":SPEC["attendance_at_venue"],
      "first_pitch_local":SPEC["first_pitch"]
    })
    players.extend(records)
    players.sort(key=lambda r:(r["game_id"],r["team"],r.get("batting_slot",99),
      r.get("batting_sub_index",99),r.get("pitching_appearance_index",99),r["player_id"]))
    report.update({
      "official_player_boxscores_imported":sum(g["verification"]=="official_boxscore_verified" for g in games),
      "official_score_and_inning_lines_matched":sum(g["verification"]!="attendance_only" for g in games),
      "official_scoreboard_player_lines_pending":sum(g["verification"]=="official_scoreboard_verified" for g in games),
      "attendance_only_pending_official_verification":sum(g["verification"]=="attendance_only" for g in games),
      "remaining_official_boxscore_work":sum(g["verification"]=="official_scoreboard_verified" for g in games),
      "player_stat_rows":len(players),"unique_player_ids":len({r["player_id"] for r in players}),
      "latest_verified_batch":"SoCon Regular Season May 15, 2026 · Mercer at East Tennessee State"
    })
    report.setdefault("additional_official_gamebooks",[]).append({
      "game_id":ID,"source_url":SPEC["source_url"],"verification":"official_boxscore_verified"})
    report["warning"]="444 attendance entries preserved. Official player stats included only after independent source reconciliation."
    audit["lineup_substitutions"]=subs
    audit["two_way_batter_and_pitcher"]="Braydon Kersey"
    for fname,item in (("games.json",games),("player_stats.json",players),
      ("import_report.json",report),("2026_may15_mercer_etsu_audit.json",audit)):
        (DATA/fname).write_text(json.dumps(item,ensure_ascii=False,indent=2)+"\n")
    print("PASS Mercer 9 at ETSU 7 player source, two-way Kersey verified;",
      len(records),"player records;",report["official_player_boxscores_imported"],"full gamebooks")
if __name__=="__main__":main()
