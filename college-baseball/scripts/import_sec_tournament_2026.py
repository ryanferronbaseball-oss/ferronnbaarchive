#!/usr/bin/env python3
"""Source-reconciled SEC Tournament gamebook import (May 20–22, 2026).

Only full official Sidearm gamebooks listed in SOURCES are eligible for promotion.
Reuses existing strict gamebook parser; requires source totals to match the
previously verified score and R/H, and requires exact 1–9 lineup identities.
No inferred box scores, unnamed substitutes or stage changes to main.
"""
from __future__ import annotations

import json
from collections import Counter
from pathlib import Path

from import_sidearm_pilot import scrape, slug

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
SOURCES = {
    "cb-2026-05-20-tennessee-arkansas-att0431":
        "https://utsports.com/sports/baseball/stats/2026/arkansas/boxscore/30092",
    "cb-2026-05-21-mississippi-state-georgia-att0433":
        "https://hailstate.com/sports/baseball/stats/2026/georgia/boxscore/27713",
    "cb-2026-05-21-florida-alabama-att0434":
        "https://floridagators.com/sports/baseball/stats/2026/alabama/boxscore/28031",
    "cb-2026-05-22-arkansas-texas-att0435":
        "https://texaslonghorns.com/sports/baseball/stats/2026/arkansas/boxscore/22672",
}

# Each nested group is one starting lineup slot followed by any official
# substitutions in that same slot, exactly as listed in the game's box score.
# Game/source/player set matching is strict: omissions or extra names abort.
LINEUPS = {
"cb-2026-05-20-tennessee-arkansas-att0431": {
  "Tennessee": ["Garrett Wright","Blake Grimmer","Henry Ford",
     "Trent Grindlinger","Levi Clark","Manny Marin",
     ["Blaine Brown","Stone Lawless"],"Nate Eisfelder","Jay Abernathy"],
  "Arkansas": ["Damian Ruiz","Camden Kozeal","Ryder Helfrick",
     "Zack Stewart","Tj Pompey","Nolan Souza",
     ["Kuhio Aloy","Carter Rutenbar"],"Maika Niu","Reese Robinett"],
},
"cb-2026-05-21-mississippi-state-georgia-att0433": {
  "Mississippi State": ["Gehrig Frei","Ace Reese","Noah Sullivan",
     "Jacob Parker","Vytas Valincius","Reed Stallman",
     ["Bryce Chance","Blake Bevis"],"Ryder Woodson","Chone James"],
  "Georgia": ["Tre Phelps","Daniel Jackson",
     ["M. O'shaughnessy","Jordy Oriach"],"Rylan Lujo",
     "Kenny Ishikawa","Ryan Wynn","Brennan Hudson","Kolby Branch","Ryan Black"],
},
"cb-2026-05-21-florida-alabama-att0434": {
  "Florida": ["Kyle Jones","Brendan Lawson","Blake Cyr","Ethan Surowiec",
     "Caden McDonald","Karson Bowen","Landon Stripling","Cade Kurland",
     "Hayden Yost"],
  "Alabama": ["Bryce Fowler","Justin Lebron","Brady Neal",
     "Jason Torres","John Lemm","Eric Hines","Brennan Holt",
     "Luke Vaughn","Peyton Steele"],
},
"cb-2026-05-22-arkansas-texas-att0435": {
  "Arkansas": ["Damian Ruiz","Camden Kozeal","Ryder Helfrick",
     "Zack Stewart","Tj Pompey","Nolan Souza","Maika Niu",
     "Carter Rutenbar","Reese Robinett"],
  "Texas": ["Aiden Robbins",["Carson Tinney","Presley Courville"],
     "Anthony Pack Jr.","Temo Becerra","Casey Borba",
     "Adrian Rodriguez",["Ethan Mendoza","Callum Early"],
     ["Ashton Larson","Josh Livingston"],
     ["Dariyan Pendergrass","Jayden Duplantier"]],
},
}

def main():
    games = json.loads((DATA / "games.json").read_text())
    records = json.loads((DATA / "player_stats.json").read_text())
    report = json.loads((DATA / "import_report.json").read_text())
    by_id = {g["id"]: g for g in games}
    assert len(games) == 444 and len(by_id) == 444
    assert len(SOURCES) == 4
    existing_keys = {(r["game_id"], r["player_id"]) for r in records}
    if len(existing_keys) != len(records):
        raise ValueError("Duplicate pre-existing athlete/game identity")

    complete_existing = [gid for gid in SOURCES
                         if any(r["game_id"] == gid for r in records)]
    if complete_existing:
        if len(complete_existing) != len(SOURCES):
            raise ValueError("Partial previously imported SEC batch requires manual reconciliation")
        for gid in SOURCES:
            game=by_id[gid]
            group=[r for r in records if r["game_id"] == gid]
            if (game["verification"]!="official_boxscore_verified"
                or len(group)<18 or {r["team"] for r in group}!={game["away"],game["home"]}
                or any(r.get("source_url")!=SOURCES[gid] for r in group)):
                raise ValueError("Previously staged gamebook is not source-reconciled: "+gid)
            for team in (game["away"],game["home"]):
                spots=[r["batting_slot"] for r in group if r["team"]==team
                       and "batting" in r and r.get("batting_sub_index")==0]
                if sorted(spots)!=list(range(1,10)):
                    raise ValueError("Missing source-verified batting order on re-run: "+gid)
        updated=0
        for gid in SOURCES:
            game=by_id[gid]
            group=[r for r in records if r["game_id"]==gid and "pitching" in r]
            decisions=game.get("pitching_decisions",{})
            for choice,field in (("win","wins"),("loss","losses"),("save","saves")):
                official=decisions.get(choice)
                eligible=[r for r in group if official and slug(r["player"])==slug(official)]
                if official and len(eligible)!=1:
                    raise ValueError(f"{gid}: official {choice} {official!r} not uniquely identified in pitcher lines")
                for pitcher in group:
                    correct=int(bool(official and pitcher["player_id"]==eligible[0]["player_id"]))
                    if pitcher["pitching"].get(field)!=correct:
                        pitcher["pitching"][field]=correct
                        updated+=1
        if updated:
            (DATA/"player_stats.json").write_text(
                json.dumps(records,ensure_ascii=False,indent=2)+"\\n",encoding="utf-8")
        print("PASS: four SEC gamebooks re-checked; pitcher decisions repaired:",
              updated,"fields; no duplicate records")
        return

    audit = []
    new_records = []
    for gid, url in SOURCES.items():
        if gid not in by_id:
            raise ValueError("Unrecognized attendance entry " + gid)
        game = by_id[gid]
        if game["verification"] not in ("official_scoreboard_verified","official_boxscore_verified"):
            raise ValueError("Refusing unverified game " + gid)
        if game["source_url"] != url:
            raise ValueError("Official source URL mismatch for " + gid)
        if game["date"][:4] != "2026":
            raise ValueError("Incorrect game season")
        if any(r["game_id"] == gid for r in records):
            raise ValueError("Game already has player records; no duplicate import " + gid)
        source_rows, source_audit = scrape({**game, "winner":game.get("pitching_decisions",{}).get("win"),
                                           "loser":game.get("pitching_decisions",{}).get("loss"),
                                           "save":game.get("pitching_decisions",{}).get("save")})
        observed = {(r["team"], slug(r["player"])): r for r in source_rows if "batting" in r}
        spec = LINEUPS[gid]
        if set(spec) != {game["away"],game["home"]}:
            raise ValueError("Official batting lineup school mismatch")
        expected_names = set()
        replacements = {}
        for team, slots in spec.items():
            if len(slots) != 9:
                raise ValueError("Lineup must have nine slots")
            appearance = 0
            for index, group in enumerate(slots, start=1):
                members = group if isinstance(group, list) else [group]
                for sub_index, name in enumerate(members):
                    key = (team, slug(name))
                    if key not in observed:
                        raise ValueError(f"{gid}: source batter not found for slot {index}: {key}")
                    if key in expected_names:
                        raise ValueError("Duplicate ordered source batter " + str(key))
                    expected_names.add(key)
                    rec = observed[key]
                    rec["batting_slot"] = index
                    rec["batting_sub_index"] = sub_index
                    rec["batting_appearance_index"] = appearance
                    if sub_index: replacements[name] = [team, index, sub_index]
                    appearance += 1
        if set(observed) != expected_names:
            raise ValueError(f"{gid}: lineup missing/additional source names: " +
                             repr(set(observed) ^ expected_names))
        for team in spec:
            idx = 0
            for rec in source_rows:
                if rec["team"] == team and "pitching" in rec:
                    rec["pitching_appearance_index"] = idx
                    idx += 1
        for rec in source_rows:
            key=(rec["game_id"], rec["player_id"])
            if key in existing_keys:
                raise ValueError("Duplicate preexisting player stat " + str(key))
            existing_keys.add(key)
        game["verification"] = "official_boxscore_verified"
        game["official_boxscore_status"] = "verified"
        game["score_provenance"] = "official_boxscore"
        source_audit["lineups_verified"] = True
        source_audit["lineup_replacements"] = replacements
        source_audit["player_rows"] = len(source_rows)
        source_audit["official_date"] = game["date"]
        audit.append(source_audit)
        new_records.extend(source_rows)

    records.extend(new_records)
    records.sort(key=lambda r:(r["game_id"],r["team"],r.get("batting_slot",99),
                               r.get("batting_sub_index",99),
                               r.get("pitching_appearance_index",99),r["player_id"]))
    report["official_player_boxscores_imported"] = sum(g["verification"] == "official_boxscore_verified" for g in games)
    report["official_scoreboard_player_lines_pending"] = sum(g["verification"] == "official_scoreboard_verified" for g in games)
    report["attendance_only_pending_official_verification"] = sum(g["verification"] == "attendance_only" for g in games)
    report["player_stat_rows"] = len(records)
    report["unique_player_ids"] = len({r["player_id"] for r in records})
    report["remaining_official_boxscore_work"] = report["official_scoreboard_player_lines_pending"]
    report["latest_verified_batch"] = "SEC Tournament 2026 May 20–22 official individual box-score imports"
    report["warning"] = ("All 444 attended games preserved in unpublished draft. "
       f"{report['official_player_boxscores_imported']} official complete player box scores; "
       f"{report['official_scoreboard_player_lines_pending']} official score-only; "
       f"{report['attendance_only_pending_official_verification']} attendance-only. "
       "Unmatched 2026 games have no invented player stats.")
    report["sec_tournament_four_sidearm_audit"] = "data/2026_sec_tournament_player_audit.json"
    report["latest_verified_game_ids"] = list(SOURCES)
    for item in report.get("latest_verified_batch_games",[]):
        if item.get("status") == "official_scoreboard_verified":
            item["status"] = by_id[next(x for x in SOURCES if by_id[x]["source_worksheet_row"] == item["worksheet_row"])]["verification"] if any(by_id[x]["source_worksheet_row"] == item["worksheet_row"] for x in SOURCES) else item["status"]

    (DATA/"games.json").write_text(json.dumps(games,ensure_ascii=False,indent=2)+"\n")
    (DATA/"player_stats.json").write_text(json.dumps(records,ensure_ascii=False,indent=2)+"\n")
    (DATA/"import_report.json").write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n")
    (DATA/"2026_sec_tournament_player_audit.json").write_text(
       json.dumps({"status":"PASS","verified_games":len(audit),
                   "player_game_rows_added":len(new_records),
                   "games":audit},ensure_ascii=False,indent=2)+"\n")
    print("PASS",len(audit),"official SEC gamebooks,",len(new_records),"added player-game rows;",
          len(records),"total rows across",report["official_player_boxscores_imported"],
          "verified games",flush=True)

if __name__ == "__main__":
    main()
