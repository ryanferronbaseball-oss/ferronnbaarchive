#!/usr/bin/env python3
"""Deterministically assemble college attendance + source-verified scorebook batches.

The original attendance CSV is canonical for what the user says they attended.
Verified_batches are official results and must exactly match a recorded date and
game identity; no player-level box score is implied by a verified final score.
"""
from __future__ import annotations
import argparse
import json
from pathlib import Path
from import_attendance import load_csv, make_report

ROOT=Path(__file__).resolve().parents[1]
DATA=ROOT/"data"
BATCHES=DATA/"verified_batches"

def assemble():
    attended=load_csv(DATA/"attendance.csv")
    by_id={g["id"]:g for g in attended}
    if len(by_id)!=len(attended):
        raise ValueError("Duplicate attendance identity")
    reports=[]
    seen=set()
    for path in sorted(BATCHES.glob("*.json")):
        batch=json.loads(path.read_text(encoding="utf-8"))
        items=batch["games"]
        if not items:raise ValueError(f"{path}: empty verified batch")
        for item in items:
            pk=item["id"]
            if pk in seen:raise ValueError(f"Duplicate verified game across batches: {pk}")
            seen.add(pk)
            if pk not in by_id:raise ValueError(f"{path}: verified game not in attendance: {pk}")
            original=by_id[pk]
            for fld in ("date","away","home"):
                if item[fld]!=original[fld]:
                    raise ValueError(f"Official source mismatch {pk}, {fld}: {item[fld]!r} != {original[fld]!r}")
            if not item["source_url"].startswith("https://"):raise ValueError(f"{pk}: official source URL missing")
            if item["verification"] not in ("official_scoreboard_verified","official_boxscore_verified"):
                raise ValueError(f"{pk}: unsupported source status")
            if item["verification"]=="official_boxscore_verified" and item.get("official_boxscore_status")!="verified":
                raise ValueError(f"{pk}: cannot claim complete college box score without verified player records")
            innings=item["away_innings"],item["home_innings"]
            if len(innings[0])!=len(innings[1]) or not 7<=len(innings[0])<=18:
                raise ValueError(f"{pk}: invalid innings")
            if any(x is not None and (not isinstance(x,int) or x<0) for arr in innings for x in arr):
                raise ValueError(f"{pk}: inning runs invalid")
            for key,values in [("away_score",innings[0]),("home_score",innings[1])]:
                if sum(x or 0 for x in values)!=item[key]:
                    raise ValueError(f"{pk}: {key} doesn't reconcile with innings")
            for key in ("away_hits","home_hits","away_errors","home_errors"):
                if not isinstance(item[key],int) or item[key]<0:
                    raise ValueError(f"{pk}: invalid R/H/E {key}")
            assert original["score_provenance"] is None or original["score_provenance"]=="user_attendance_log"
            original.update({
                "ballpark":item["venue"],"city":item["city"],"state":item["state"],
                "away_score":item["away_score"],"home_score":item["home_score"],
                "away_hits":item["away_hits"],"home_hits":item["home_hits"],
                "away_errors":item["away_errors"],"home_errors":item["home_errors"],
                "score_provenance":"official_boxscore",
                "source_url":item["source_url"],
                "verification":item["verification"],
                "official_boxscore_status":item["official_boxscore_status"],
                "innings":[{"inning":i+1,"away":a,"home":h} for i,(a,h) in enumerate(zip(*innings))],
                "pitching_decisions":{"winner":item["winner"],"loser":item["loser"],"save":item["save"]},
                "game_type":item["game_type"],"postseason_round":item["postseason_round"],
                "ncaa_regional_game_number":item["official_game_no"],
                "first_pitch_local":item.get("first_pitch"),
                "source_attendance":item.get("attendance_at_venue"),
                "completion_date":item.get("completion_date"),
                "attendance_segment_confirmation_pending":item.get("attendance_segment_confirmation_pending",False),
            })
            if item.get("notes"):
                original["notes"]=(original.get("notes") or "")+" "+item["notes"]
        reports.append({"batch":path.name,"games":len(items),"verification":"scoreboard checked against linked university athletic box scores"})
    attended.sort(key=lambda g:(g["date"],g["id"]))
    report=make_report(attended)
    report.update({
        "status":"attendance_imported_pilot_scores_verified",
        "official_scoreboards_verified":len(seen),
        "official_boxscores_imported":0,
        "player_stat_rows":0,
        "source_file":"NCAAB Games.xlsx / Sheet1",
        "source_duplicate_matchups":13,
        "source_corrections":["Sheet1 row 267: 2034-03-30 corrected to official 2024-03-30, with user confirmation"],
        "review_queue":[
            "Sheet1 row 444: Auburn at Milwaukee dated May 31, 2026 does not match the official Auburn Regional schedule; possible Auburn–UCF May 31 or Milwaukee–Auburn June 1. User confirmation required.",
            "Sheet1 row 441: NC State at UCF started May 29 but finished May 30 due to suspension; user attendance in resumed segment unconfirmed."
        ],
        "verified_batches":reports,
        "warning":"The five pilot final scores, R/H/E, innings and pitching decisions are source-verified. Full player batting/pitching scorebooks have not yet been reconciled; do not label them as complete."
    })
    return attended,report

def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--validate-only",action="store_true")
    args=ap.parse_args()
    games,report=assemble()
    if not args.validate_only:
        (DATA/"games.json").write_text(json.dumps(games,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
        (DATA/"import_report.json").write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print("assembled",len(games),"attended games,",report["official_scoreboards_verified"],"verified game scores;",
          report["player_stat_rows"],"player stat rows",flush=True)

if __name__=="__main__":main()
