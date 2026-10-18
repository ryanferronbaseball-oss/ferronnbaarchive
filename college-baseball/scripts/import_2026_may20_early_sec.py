#!/usr/bin/env python3
"""May 20, 2026 SEC Tournament: add two fully source-audited player gamebooks.

Creates verified matchups only if they correspond exactly to an original
attendance row. All source-derived score, R/H/E, innings, lineup and pitching
information are checked against original university Sidearm box score pages.
Never guesses a batting spot, makes up a player or edits the public site.
"""
from __future__ import annotations
import json
from pathlib import Path
from import_sidearm_pilot import scrape, slug

DATA=Path(__file__).resolve().parents[1]/"data"
GAMES={
"cb-2026-05-20-missouri-mississippi-state-att0429":{
  "source_url":"https://hailstate.com/sports/baseball/stats/2026/missouri/boxscore/27457",
  "date":"2026-05-20", "away":"Missouri","home":"Mississippi State",
  "away_score":2,"home_score":12,"away_hits":5,"home_hits":8,
  "away_errors":2,"home_errors":1,
  "away_innings":[1,0,0,0,1,0,0],"home_innings":[0,3,0,0,1,8,None],
  "winner":"Tomas Valincius","loser":"Brady Kehlenbrink","save":None,
  "lineups":{
    "Missouri":["Jase Woita","Kam Durnin","Blaize Ward","Mateo Serna",
                 "Donovan Jordan","Kaden Peer","Jamal George","Chris Patterson","Pierre Seals"],
    "Mississippi State":["Gehrig Frei","Ace Reese","Noah Sullivan","Jacob Parker",
                 "Vytas Valincius","Reed Stallman","Bryce Chance","Ryder Woodson","Chone James"]
   },
  "attendance_at_venue":None,"first_pitch":None,
},
"cb-2026-05-20-vanderbilt-florida-att0430":{
  "source_url":"https://floridagators.com/sports/baseball/stats/2026/vanderbilt/boxscore/27672",
  "date":"2026-05-20","away":"Vanderbilt","home":"Florida",
  "away_score":3,"home_score":8,"away_hits":6,"home_hits":14,
  "away_errors":0,"home_errors":0,
  "away_innings":[0,0,0,0,3,0,0,0,0],"home_innings":[2,1,0,0,2,0,2,1,None],
  "winner":"Jackson Barberi","loser":"Brennan Seiber","save":None,
  "lineups":{
     "Vanderbilt":["Brodie Johnston","Mike Mancini","Braden Holcomb","Logan Johnstone",
                   "Tommy Goodin","Ryker Waite","Rustan Rigdon","Colin Barczi",
                   ["Korbin Reynolds","Aukai Kea"]],
     "Florida":["Kyle Jones","Brendan Lawson","Blake Cyr","Ethan Surowiec",
                "Caden McDonald","Karson Bowen","Landon Stripling","Cade Kurland","Hayden Yost"],
   },
  "attendance_at_venue":8352,"first_pitch":"12:46",
},
}

def verify_metadata(original, spec):
    for key in ("date","away","home"):
        if original.get(key)!=spec[key]:raise ValueError(f"{key} mismatch {original['id']}")
    if original["verification"]!="attendance_only":raise ValueError("Already populated game")
    if len(spec["away_innings"])!=len(spec["home_innings"]):
        raise ValueError("Unbalanced innings")
    for field,innings in (("away_score","away_innings"),("home_score","home_innings")):
        if sum(n or 0 for n in spec[innings])!=spec[field]:
            raise ValueError("Official inning runs do not reconcile")
    if any(n is not None and (not isinstance(n,int) or n<0)
           for arr in (spec["away_innings"],spec["home_innings"]) for n in arr):
        raise ValueError("Invalid inning totals")

def add_lineups(records,stat_rows,game,spec):
    observed={(r["team"],slug(r["player"])):r for r in stat_rows if "batting" in r}
    expected=set()
    sub_report={}
    for team,order in spec["lineups"].items():
        if len(order)!=9:raise ValueError("Expected nine official batting slots")
        for spot,members in enumerate(order,1):
            entries=members if isinstance(members,list) else [members]
            for sub_index,name in enumerate(entries):
                key=(team,slug(name))
                if key not in observed:raise ValueError(f"Official lineup {game['id']} missing {key}")
                if key in expected:raise ValueError("Duplicated official lineup entry")
                expected.add(key)
                r=observed[key]
                r["batting_slot"]=spot
                r["batting_sub_index"]=sub_index
                r["batting_appearance_index"]=sum(1 for prev in expected if prev[0]==team)-1
                if sub_index:sub_report[name]={"team":team,"spot":spot,"sub_index":sub_index}
        pitchers=[r for r in stat_rows if r["team"]==team and "pitching" in r]
        for i,r in enumerate(pitchers):r["pitching_appearance_index"]=i
    if set(observed)!=expected:
        raise ValueError("Unexpected/unmatched source batters: "+str(set(observed)^expected))
    if set(spec["lineups"])!={game["away"],game["home"]}:
        raise ValueError("School lineup team mismatch")
    new_keys={(r["game_id"],r["player_id"]) for r in stat_rows}
    if len(new_keys)!=len(stat_rows) or new_keys & records:raise ValueError("Duplicate player-game row")
    records.update(new_keys)
    return sub_report

def main():
    games=json.loads((DATA/"games.json").read_text())
    players=json.loads((DATA/"player_stats.json").read_text())
    report=json.loads((DATA/"import_report.json").read_text())
    by_id={g["id"]:g for g in games}
    if len(games)!=444 or len(by_id)!=444:raise ValueError("Attendance master corrupted")
    already=[gid for gid in GAMES if any(r["game_id"]==gid for r in players)]
    if already:
        if len(already)!=len(GAMES):raise ValueError("Incomplete re-run cannot overwrite source data")
        for gid in GAMES:
            g=by_id[gid]
            source=[r for r in players if r["game_id"]==gid]
            if g["verification"]!="official_boxscore_verified" or len(source)<18 or \
                any(x.get("source_url")!=GAMES[gid]["source_url"] for x in source):
                raise ValueError("Previously staged source-verified game incomplete: "+gid)
        print("PASS: prior two verified May 20 gamebooks remain complete; no duplicate import")
        return

    audit=[];added=[];existing={(r["game_id"],r["player_id"]) for r in players}
    for gid,spec in GAMES.items():
        g=by_id[gid]
        verify_metadata(g,spec)
        source_input={**g,**{k:v for k,v in spec.items() if k!="lineups"}}
        source_rows,source_audit=scrape(source_input)
        replacements=add_lineups(existing,source_rows,g,spec)
        # Promoting the game is permitted only AFTER team-level, lineup, pitching,
        # opposing-hits and exact score reconciliation by source gamebook scraper.
        g.update({
           "source_url":spec["source_url"],"verification":"official_boxscore_verified",
           "official_boxscore_status":"verified","score_provenance":"official_boxscore",
           "away_score":spec["away_score"],"home_score":spec["home_score"],
           "away_hits":spec["away_hits"],"home_hits":spec["home_hits"],
           "away_errors":spec["away_errors"],"home_errors":spec["home_errors"],
           "innings":[{"inning":i+1,"away":a,"home":h}
                      for i,(a,h) in enumerate(zip(spec["away_innings"],spec["home_innings"]))],
           "pitching_decisions":{"win":spec["winner"],"loss":spec["loser"],"save":spec["save"]},
           "ballpark":"Hoover Met","city":"Hoover","state":"AL","neutral_site":True,
           "game_type":"conference_tournament","postseason_round":"SEC Tournament · Second Round",
           "source_attendance":spec["attendance_at_venue"],
           "first_pitch_local":spec["first_pitch"],
        })
        source_audit["source_lineups_verified"]=True
        source_audit["substitutions"]=replacements
        audit.append(source_audit);added.extend(source_rows)
    players.extend(added)
    players.sort(key=lambda r:(r["game_id"],r["team"],r.get("batting_slot",99),
                               r.get("batting_sub_index",99),r.get("pitching_appearance_index",99),r["player_id"]))
    report["official_player_boxscores_imported"]=sum(g["verification"]=="official_boxscore_verified" for g in games)
    report["official_score_and_inning_lines_matched"]=sum(g["verification"]!="attendance_only" for g in games)
    report["official_scoreboard_player_lines_pending"]=sum(g["verification"]=="official_scoreboard_verified" for g in games)
    report["attendance_only_pending_official_verification"]=sum(g["verification"]=="attendance_only" for g in games)
    report["remaining_official_boxscore_work"]=report["official_scoreboard_player_lines_pending"]
    report["player_stat_rows"]=len(players)
    report["unique_player_ids"]=len({r["player_id"] for r in players})
    report["latest_verified_batch"]="SEC Tournament May 20 2026 · Missouri/Mississippi State and Vanderbilt/Florida"
    report["next_2026_boxscore_audit"]="data/2026_sec_may20_second_round_audit.json"
    report["warning"]=("444 attendance games staged in unpublished branch. "
       f"{report['official_player_boxscores_imported']} official complete player gamebooks, "
       f"{report['official_scoreboard_player_lines_pending']} official score-only, "
       f"{report['attendance_only_pending_official_verification']} attendance-only. "
       "No player statistics are inferred for unverified games.")
    report.setdefault("additional_official_gamebooks",[]).extend({
        "game_id":gid,"source_url":spec["source_url"],"verification":"official_boxscore_verified"
        } for gid,spec in GAMES.items())
    (DATA/"games.json").write_text(json.dumps(games,ensure_ascii=False,indent=2)+"\n")
    (DATA/"player_stats.json").write_text(json.dumps(players,ensure_ascii=False,indent=2)+"\n")
    (DATA/"import_report.json").write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n")
    (DATA/"2026_sec_may20_second_round_audit.json").write_text(
        json.dumps({"status":"PASS","verified_games":len(audit),
                    "player_game_rows_added":len(added),"games":audit},indent=2,ensure_ascii=False)+"\n")
    print("PASS 2026 May 20 SEC gamebooks: 2 new full games,",len(added),"new player rows",flush=True)

if __name__=="__main__":
    main()
