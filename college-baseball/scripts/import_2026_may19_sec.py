#!/usr/bin/env python3
"""Two additional May 19 SEC Tournament first-round complete player gamebooks.

Official Sidearm university scorebooks only, precise 1–9 batting spots and
source-reconciled pitching decisions. Never upgrades an unreviewed game.
"""
import json
from pathlib import Path
from import_sidearm_pilot import scrape
from import_2026_may20_early_sec import verify_metadata, add_lineups

DATA=Path(__file__).resolve().parents[1]/"data"
SOURCES={
"cb-2026-05-19-missouri-ole-miss-att0425":{
  "source_url":"https://olemisssports.com/sports/baseball/stats/2026/missouri/boxscore/14713",
  "date":"2026-05-19","away":"Missouri","home":"Ole Miss",
  "away_score":10,"home_score":8,"away_hits":14,"home_hits":9,
  "away_errors":0,"home_errors":1,
  "away_innings":[0,0,2,0,5,1,0,2,0],
  "home_innings":[1,1,0,0,4,0,2,0,0],
  "winner":"Eli Skidmore","loser":"Landon Koenig","save":None,
  "lineups":{
    "Missouri":["Jase Woita","Kam Durnin",
               ["Blaize Ward","Isaiah Frost","Eric Maisonet"],
               "Mateo Serna","Donovan Jordan","Kaden Peer",
               "Jamal George","Chris Patterson","Pierre Seals"],
    "Ole Miss":["Dom Decker","Tristan Bissetta","Judd Utermark",
                "Will Furniss","Hayden Federico","Owen Paino",
                "Austin Fawley","Daniel Pacella","Brayden Randle"]},
  "first_pitch":"09:33","attendance_at_venue":None
},
"cb-2026-05-19-lsu-oklahoma-att0428":{
  "source_url":"https://soonersports.com/sports/baseball/stats/2026/lsu/boxscore/15789",
  "date":"2026-05-19","away":"LSU","home":"Oklahoma",
  "away_score":6,"home_score":2,"away_hits":11,"home_hits":6,
  "away_errors":2,"home_errors":3,
  "away_innings":[0,0,1,0,3,0,0,2,0],
  "home_innings":[0,0,1,1,0,0,0,0,0],
  "winner":"Gavin Guidry","loser":"Lj Mercurius","save":"Deven Sheerin",
  "lineups":{
    "LSU":["Mason Braun",["Omar Serna Jr.","Brayden Simpson"],
           "Derek Curiel","Cade Arrambide","Steven Milam","John Pearson",
           ["Seth Dardar","William Patrick"],"Chris Stanfield","Jack Ruckert"],
    "Oklahoma":["Jason Walk","Camden Johnson","Deiten Lachance","Jaxon Willits",
                "Trey Gambill","Brendan Brock","Dasan Harris",
                ["Dayton Tockey","Nolan Stevens"],["Kyle Branch","Drew Dickerson"]]},
  "first_pitch":"20:56","attendance_at_venue":7617,
},
}

def main():
    games=json.loads((DATA/"games.json").read_text())
    records=json.loads((DATA/"player_stats.json").read_text())
    report=json.loads((DATA/"import_report.json").read_text())
    by_id={g["id"]:g for g in games}
    assert len(games)==444 and len(by_id)==444
    existing={(r["game_id"],r["player_id"]) for r in records}
    already=[gid for gid in SOURCES if any(r["game_id"]==gid for r in records)]
    if already:
        if len(already)!=len(SOURCES):raise ValueError("Partially staged May 19 batch")
        for gid in SOURCES:
            g=by_id[gid]
            subset=[r for r in records if r["game_id"]==gid]
            if (g["verification"]!="official_boxscore_verified" or len(subset)<18
                or any(r.get("source_url")!=SOURCES[gid]["source_url"] for r in subset)):
                raise ValueError("Previously staged official source mismatch")
        print("PASS: two earlier May 19 gamebooks already verified")
        return

    extra=[];audits=[]
    for gid,spec in SOURCES.items():
        if gid not in by_id:raise ValueError("Attendance missing "+gid)
        g=by_id[gid]
        verify_metadata(g,spec)
        result,audit=scrape({**g,**{k:v for k,v in spec.items() if k!="lineups"}})
        subs=add_lineups(existing,result,g,spec)
        for key in ("away_score","home_score","away_hits","home_hits","away_errors","home_errors"):
            g[key]=spec[key]
        g["source_url"]=spec["source_url"]
        g["verification"]="official_boxscore_verified"
        g["official_boxscore_status"]="verified"
        g["score_provenance"]="official_boxscore"
        g["innings"]=[{"inning":i+1,"away":a,"home":h}
                      for i,(a,h) in enumerate(zip(spec["away_innings"],spec["home_innings"]))]
        g["pitching_decisions"]={"win":spec["winner"],"loss":spec["loser"],"save":spec["save"]}
        g["ballpark"]="Hoover Met";g["city"]="Hoover";g["state"]="AL"
        g["neutral_site"]=True
        g["game_type"]="conference_tournament";g["postseason_round"]="SEC Tournament · First Round"
        g["source_attendance"]=spec["attendance_at_venue"]
        g["first_pitch_local"]=spec["first_pitch"]
        audit["batting_lineups_source_verified"]=True
        audit["lineup_substitutions"]=subs
        audits.append(audit);extra.extend(result)
    records.extend(extra)
    records.sort(key=lambda r:(r["game_id"],r["team"],r.get("batting_slot",99),
                               r.get("batting_sub_index",99),r.get("pitching_appearance_index",99),r["player_id"]))
    report.update({
       "official_player_boxscores_imported":sum(g["verification"]=="official_boxscore_verified" for g in games),
       "official_score_and_inning_lines_matched":sum(g["verification"]!="attendance_only" for g in games),
       "official_scoreboard_player_lines_pending":sum(g["verification"]=="official_scoreboard_verified" for g in games),
       "attendance_only_pending_official_verification":sum(g["verification"]=="attendance_only" for g in games),
       "player_stat_rows":len(records),
       "unique_player_ids":len({r["player_id"] for r in records}),
       "latest_verified_batch":"SEC Tournament May 19 2026 · Missouri/Ole Miss and LSU/Oklahoma",
       "2026_may19_first_round_audit":"data/2026_sec_may19_first_round_audit.json",
    })
    report["remaining_official_boxscore_work"]=report["official_scoreboard_player_lines_pending"]
    report["warning"]="No attendance or player records inferred: 444 source attendance rows preserved, only independently reconciled official gamebooks promoted."
    report.setdefault("additional_official_gamebooks",[]).extend({
        "game_id":gid,"source_url":spec["source_url"],"verification":"official_boxscore_verified"
        } for gid,spec in SOURCES.items())
    (DATA/"games.json").write_text(json.dumps(games,ensure_ascii=False,indent=2)+"\n")
    (DATA/"player_stats.json").write_text(json.dumps(records,ensure_ascii=False,indent=2)+"\n")
    (DATA/"import_report.json").write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n")
    (DATA/"2026_sec_may19_first_round_audit.json").write_text(
       json.dumps({"status":"PASS","verified_games":2,"player_rows_added":len(extra),"games":audits},
                  ensure_ascii=False,indent=2)+"\n")
    print("PASS May 19 SEC first round: 2 official complete games,",len(extra),"new player-game records")

if __name__=="__main__":
    main()
