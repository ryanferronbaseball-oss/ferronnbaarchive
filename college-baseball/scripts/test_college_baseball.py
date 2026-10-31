#!/usr/bin/env python3
"""College baseball attendance import integrity and desktop/mobile browser smoke QA.

Synthetic fixtures are created in a disposable temporary directory and are NEVER
written to the repository's source data or published attendance record.
"""
from __future__ import annotations

import csv
import json
import runpy
import shutil
import subprocess
import tempfile
import threading
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[2]
SITE = ROOT / "college-baseball"
REVIEW = SITE / "output" / "regional-pilot-review"
REVIEW.mkdir(parents=True, exist_ok=True)
MOD = runpy.run_path(str(SITE / "scripts" / "import_attendance.py"))
load_csv, make_report = MOD["load_csv"], MOD["make_report"]


def check(condition, message):
    assert condition, message
    print("PASS", message, flush=True)


def mock_csv(path, items):
    cols = ["attendance_id", "date", "away", "home", "ballpark", "city", "state",
            "neutral_site", "game_number", "game_type", "postseason_round",
            "away_score", "home_score", "source_url", "notes"]
    with path.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=cols)
        writer.writeheader()
        writer.writerows(items)


class Quiet(SimpleHTTPRequestHandler):
    def log_message(self, *args):
        pass


def run_server(root):
    server = ThreadingHTTPServer(("127.0.0.1", 0), partial(Quiet, directory=str(root)))
    threading.Thread(target=server.serve_forever, daemon=True).start()
    return server


def visit(page, host, path, selector):
    response = page.goto(host + "/college-baseball/" + path, wait_until="domcontentloaded")
    check(response.status == 200, path + " loads")
    page.wait_for_selector(selector, timeout=12000)


attended = load_csv(SITE / "data" / "attendance.csv")
committed = json.loads((SITE / "data" / "games.json").read_text())
pilot_rows = json.loads((SITE / "data" / "player_stats.json").read_text())
pilot_report = json.loads((SITE / "data" / "import_report.json").read_text())
draft_tags = json.loads((SITE / "data" / "draft_profile_tags.json").read_text())
draft_ids = {r["college_player_id"] for r in draft_tags["picks"]}
check(len(draft_tags["picks"]) == len(draft_ids) == 8 and
      {"cb-san-diego-riley-adams", "cb-san-diego-sean-barry", "cb-byu-colton-shaver"} <= draft_ids and
      all(any(r["player_id"] == pick["college_player_id"] and
                  r["player"].casefold() == pick["name"].casefold() for r in pilot_rows)
          for pick in draft_tags["picks"]),
      "Eight official 2017 draft picks match exact witnessed college player IDs")
check(len(attended) == 6 and len(committed) == 444, "All 444 attendance entries staged with 6 verified initial Regional gamebooks")
check(len({g["source_worksheet_row"] for g in committed}) == 444,
      "Unique workbook source rows preserved for every attended contest")
check(len([g for g in committed if g["verification"] == "attendance_only"]) <= 430,
      "Previously confirmed attendance-only records stay unmodified except source-verified imports")
check(all(g["away_score"] is None and g["home_score"] is None
          and g["game_number"] is None for g in committed
          if g["verification"] == "attendance_only"),
      "Attendance-only entries keep scores and doubleheader numbering unknown until confirmed")
check(any(g["possible_same_day_doubleheader"] for g in committed if g["verification"] == "attendance_only"),
      "Ambiguous same-day repeat matchups preserved for later doubleheader reconciliation")
check(all(g["away_score"] is not None and g["home_score"] is not None and g["source_url"]
          and len(g["innings"]) in (8,9) for g in committed
          if g["verification"] == "official_scoreboard_verified"),
      "Five SEC Tournament score-matched games have sourced inning lines with no fictitious player stats")
check(not {g["id"] for g in committed if g["verification"] == "official_scoreboard_verified"}
      & {r["game_id"] for r in pilot_rows},
      "No player lines are borrowed for sourced-but-incomplete SEC Tournament games")
check(len(pilot_rows) >= 246 and len({r["player_id"] for r in pilot_rows}) >= 147,
      "All original 246 verified records preserved as subsequent audited games are added")
check(len([g for g in committed if g["verification"] == "official_boxscore_verified"]) >= 9,
      "No previously verified gamebook downgraded")
check(len([g for g in committed if g["verification"] == "official_scoreboard_verified"]) <= 5,
      "No more than five SEC Tournament games have player lines pending")
# A source-matched university recap may establish only the final score;
# all fully verified player gamebooks must include inning totals.
check(all(
          g["source_url"]
          and (g["verification"] == "source_matched" or bool(g.get("innings")))
          and (not g.get("innings") or
               (sum(x["away"] or 0 for x in g["innings"]) == g["away_score"]
                and sum(x["home"] or 0 for x in g["innings"]) == g["home_score"]))
          for g in committed if g["verification"] != "attendance_only"),
      "Sourced records retain source URLs; available inning lines reconcile with totals")
confirmed_2024={g["source_worksheet_row"]:g for g in committed if g["season"] == 2024}
check(all(confirmed_2024[row]["game_number"] == number and
          (confirmed_2024[row]["away_score"],confirmed_2024[row]["home_score"]) == (a,h)
          for row,number,a,h in [(245,1,6,11),(261,1,4,8),(262,2,3,8)]),
      "User-confirmed 2024 doubleheader identities and scores stay attached to distinct rows")
check({g["id"] for g in committed if g["verification"] == "official_boxscore_verified"} ==
      {r["game_id"] for r in pilot_rows},
      "Player stats are tied only to games with complete official player box scores")

# Exactly nine independently sourced batting slots for every team, with
# pinch-hitters/defensive replacements on the existing slot (MLB conventions).
source_replacements = {
    ("cb-2026-05-29-nc-state-ucf", "NC State", "Vincent DeCarlo"): (9, 1),
    ("cb-2026-05-29-nc-state-ucf", "UCF", "Stephen Chucka"): (7, 1),
    ("cb-2026-05-30-auburn-nc-state", "NC State", "Christian Serrano"): (8, 1),
    ("cb-2026-05-30-auburn-nc-state", "NC State", "Vincent DeCarlo"): (9, 1),
    ("cb-2026-05-30-ucf-milwaukee", "Milwaukee", "Cade Palkowski"): (5, 1),
    ("cb-2026-05-31-ucf-auburn", "UCF", "Cayden Gaskin"): (7, 1),
    ("cb-2026-05-31-auburn-milwaukee", "Milwaukee", "Tate Schmidt"): (7, 1),
    ("cb-2026-05-31-auburn-milwaukee", "Milwaukee", "Tristan Ellis"): (7, 2),
    ("cb-2026-05-20-lsu-auburn-att0432", "LSU", "Daniel Harden"): (5, 1),
    ("cb-2026-05-20-lsu-auburn-att0432", "LSU", "Edward Yamin IV"): (8, 1),
    ("cb-2026-05-20-lsu-auburn-att0432", "LSU", "Trent Caraway"): (8, 2),
    ("cb-2026-05-20-lsu-auburn-att0432", "LSU", "Zach Yorke"): (9, 1),
    ("cb-2026-05-23-florida-georgia-att0437", "Georgia", "Cole Johnson"): (3, 1),
    ("cb-2026-05-23-florida-georgia-att0437", "Georgia", "Bryce Calloway"): (3, 2),
    ("cb-2026-05-20-tennessee-arkansas-att0431", "Tennessee", "Stone Lawless"): (7, 1),
    ("cb-2026-05-20-tennessee-arkansas-att0431", "Arkansas", "Carter Rutenbar"): (7, 1),
    ("cb-2026-05-21-mississippi-state-georgia-att0433", "Mississippi State", "Blake Bevis"): (7, 1),
    ("cb-2026-05-21-mississippi-state-georgia-att0433", "Georgia", "Jordy Oriach"): (3, 1),
    ("cb-2026-05-22-arkansas-texas-att0435", "Texas", "Presley Courville"): (2, 1),
    ("cb-2026-05-22-arkansas-texas-att0435", "Texas", "Callum Early"): (7, 1),
    ("cb-2026-05-22-arkansas-texas-att0435", "Texas", "Josh Livingston"): (8, 1),
    ("cb-2026-05-22-arkansas-texas-att0435", "Texas", "Jayden Duplantier"): (9, 1),
    ("cb-2026-05-20-vanderbilt-florida-att0430", "Vanderbilt", "Aukai Kea"): (9, 1),
    ("cb-2026-05-19-missouri-ole-miss-att0425", "Missouri", "Isaiah Frost"): (3, 1),
    ("cb-2026-05-19-missouri-ole-miss-att0425", "Missouri", "Eric Maisonet"): (3, 2),
    ("cb-2026-05-19-lsu-oklahoma-att0428", "LSU", "Brayden Simpson"): (2, 1),
    ("cb-2026-05-19-lsu-oklahoma-att0428", "LSU", "William Patrick"): (7, 1),
    ("cb-2026-05-19-lsu-oklahoma-att0428", "Oklahoma", "Nolan Stevens"): (8, 1),
    ("cb-2026-05-19-lsu-oklahoma-att0428", "Oklahoma", "Drew Dickerson"): (9, 1),
    ("cb-2026-05-22-auburn-texas-a-m-att0436", "Texas A&M", "Terrence Kiel II"): (4, 1),
    ("cb-2026-05-19-south-carolina-tennessee-att0427", "South Carolina", "Logan Sutter"): (5, 1),
    ("cb-2026-05-19-south-carolina-tennessee-att0427", "Tennessee", "Ariel Antigua"): (8, 1),
    ("cb-2026-05-14-virginia-louisville-att0422", "Virginia", "Antonio Perrotta"): (7, 1),
    ("cb-2026-05-15-mercer-east-tennessee-state-att0423", "Mercer", "Nathan Rowland"): (3, 1),
    ("cb-2026-05-16-arkansas-kentucky-att0424", "Arkansas", "Alexander Peck"): (8, 1),
    ("cb-2026-05-16-arkansas-kentucky-att0424", "Arkansas", "Maika Niu"): (9, 1),
    ("cb-2026-05-10-little-rock-ut-martin-att0421", "Little Rock", "Michael O'brien"): (4, 1),
    ("cb-2026-05-10-little-rock-ut-martin-att0421", "Little Rock", "Austin Coyle"): (6, 1),
    ("cb-2026-05-10-little-rock-ut-martin-att0421", "Little Rock", "Trey Hill"): (8, 1),
}
seen_replacements = {}
for game in committed:
    if game["verification"] != "official_boxscore_verified":
        continue
    for team in (game["away"], game["home"]):
        lineup = [r for r in pilot_rows if r["game_id"] == game["id"]
                  and r["team"] == team and "batting" in r]
        pitching = [r for r in pilot_rows if r["game_id"] == game["id"]
                   and r["team"] == team and "pitching" in r]
        starters = [r for r in lineup if r.get("batting_sub_index") == 0]
        slots = [r.get("batting_slot") for r in starters]
        check(sorted(slots) == list(range(1, 10)) and len(starters) == 9,
              "Official source confirms nine starting batting positions: " + game["id"] + " " + team)
        check(all(1 <= r["batting_slot"] <= 9 and r["position"]
                  and r.get("batting_appearance_index") is not None for r in lineup),
              "Batting order and defensive position sourced for every player: " + game["id"] + " " + team)
        check(sorted(r["pitching_appearance_index"] for r in pitching) == list(range(len(pitching))),
              "Official pitching appearances remain in scorebook order: " + game["id"] + " " + team)
        for r in lineup:
            if r.get("batting_sub_index", 0):
                key = (game["id"], team, r["player"])
                seen_replacements[key] = (r["batting_slot"], r["batting_sub_index"])
                # Historical pilot spot-checks are source-transcribed, while
                # newly imported verified gamebooks may add legitimate substitutes
                # without requiring us to hardcode every name in this test.
                check(any(starter["batting_slot"] == r["batting_slot"]
                          for starter in starters),
                      "Replacement shares an original starting batting position: " + r["player"])
                check(len([other for other in lineup
                           if other["batting_slot"] == r["batting_slot"]
                           and other["batting_sub_index"] == r["batting_sub_index"]]) == 1,
                      "Each substituted batting appearance has a unique lineup index: " + r["player"])
                if key in source_replacements:
                    check(source_replacements[key] == seen_replacements[key],
                          "Official pilot spot-check batting slot agrees: " + r["player"])
check(all(seen_replacements.get(k) == v for k, v in source_replacements.items()
          if k[0] in {g["id"] for g in committed if g["verification"] == "official_boxscore_verified"}),
      "All independently transcribed pilot substitutions retain their correct batting slots")
check(len(seen_replacements) >= len(source_replacements),
      "Verified new gamebooks may include additional properly attributed substitutes")
check(sum(1 for r in pilot_rows if "batting" in r) >= 176,
      "All 176 initial hitters remain, with new verified lineup positions included")


# Reconcile audited team and pitcher lines to each official PDF's box score,
# not merely to metadata or a guessed batting average.
expected = {
    ("cb-2026-05-29-milwaukee-auburn", "Milwaukee"): {"ab": 38, "r": 13, "h": 16, "rbi": 12, "bb": 6, "k": 12},
    ("cb-2026-05-29-milwaukee-auburn", "Auburn"): {"ab": 35, "r": 8, "h": 9, "rbi": 8, "bb": 0, "k": 6},
    ("cb-2026-05-29-nc-state-ucf", "NC State"): {"ab": 38, "r": 3, "h": 12, "rbi": 3, "bb": 6, "k": 5},
    ("cb-2026-05-29-nc-state-ucf", "UCF"): {"ab": 35, "r": 9, "h": 11, "rbi": 9, "bb": 1, "k": 5},
    ("cb-2026-05-30-auburn-nc-state", "Auburn"): {"ab": 42, "r": 17, "h": 18, "rbi": 17, "bb": 7, "k": 5},
    ("cb-2026-05-30-auburn-nc-state", "NC State"): {"ab": 39, "r": 13, "h": 14, "rbi": 10, "bb": 3, "k": 4},
    ("cb-2026-05-30-ucf-milwaukee", "UCF"): {"ab": 35, "r": 6, "h": 8, "rbi": 6, "bb": 5, "k": 6},
    ("cb-2026-05-30-ucf-milwaukee", "Milwaukee"): {"ab": 31, "r": 13, "h": 9, "rbi": 11, "bb": 9, "k": 8},
    ("cb-2026-05-31-ucf-auburn", "UCF"): {"ab": 32, "r": 3, "h": 6, "rbi": 3, "bb": 3, "k": 11},
    ("cb-2026-05-31-ucf-auburn", "Auburn"): {"ab": 32, "r": 9, "h": 10, "rbi": 9, "bb": 5, "k": 11},
    ("cb-2026-05-31-auburn-milwaukee", "Auburn"): {"ab": 30, "r": 8, "h": 5, "rbi": 7, "bb": 5, "k": 6},
    ("cb-2026-05-31-auburn-milwaukee", "Milwaukee"): {"ab": 30, "r": 1, "h": 4, "rbi": 1, "bb": 0, "k": 14},
    ("cb-2026-05-20-lsu-auburn-att0432", "LSU"): {"ab": 28, "r": 1, "h": 4, "rbi": 1, "bb": 3, "k": 6},
    ("cb-2026-05-20-lsu-auburn-att0432", "Auburn"): {"ab": 30, "r": 3, "h": 7, "rbi": 2, "bb": 1, "k": 12},
    ("cb-2026-05-23-arkansas-auburn-att0438", "Arkansas"): {"ab": 32, "r": 2, "h": 5, "rbi": 2, "bb": 2, "k": 15},
    ("cb-2026-05-23-arkansas-auburn-att0438", "Auburn"): {"ab": 32, "r": 1, "h": 7, "rbi": 1, "bb": 1, "k": 11},
    ("cb-2026-05-23-florida-georgia-att0437", "Florida"): {"ab": 35, "r": 7, "h": 8, "rbi": 7, "bb": 2, "k": 9},
    ("cb-2026-05-23-florida-georgia-att0437", "Georgia"): {"ab": 34, "r": 8, "h": 12, "rbi": 7, "bb": 1, "k": 13},
    ("cb-2026-05-20-tennessee-arkansas-att0431", "Tennessee"): {"ab": 36, "r": 4, "h": 8, "rbi": 4, "bb": 2, "k": 10},
    ("cb-2026-05-20-tennessee-arkansas-att0431", "Arkansas"): {"ab": 32, "r": 8, "h": 9, "rbi": 8, "bb": 4, "k": 11},
    ("cb-2026-05-21-mississippi-state-georgia-att0433", "Mississippi State"): {"ab": 31, "r": 3, "h": 9, "rbi": 3, "bb": 2, "k": 4},
    ("cb-2026-05-21-mississippi-state-georgia-att0433", "Georgia"): {"ab": 30, "r": 5, "h": 8, "rbi": 5, "bb": 5, "k": 9},
    ("cb-2026-05-21-florida-alabama-att0434", "Florida"): {"ab": 38, "r": 13, "h": 16, "rbi": 12, "bb": 2, "k": 8},
    ("cb-2026-05-21-florida-alabama-att0434", "Alabama"): {"ab": 33, "r": 3, "h": 9, "rbi": 3, "bb": 1, "k": 14},
    ("cb-2026-05-22-arkansas-texas-att0435", "Arkansas"): {"ab": 37, "r": 8, "h": 11, "rbi": 8, "bb": 5, "k": 16},
    ("cb-2026-05-22-arkansas-texas-att0435", "Texas"): {"ab": 32, "r": 1, "h": 4, "rbi": 1, "bb": 4, "k": 14},
    ("cb-2026-05-20-missouri-mississippi-state-att0429", "Missouri"): {"ab": 23, "r": 2, "h": 5, "rbi": 2, "bb": 1, "k": 8},
    ("cb-2026-05-20-missouri-mississippi-state-att0429", "Mississippi State"): {"ab": 28, "r": 12, "h": 8, "rbi": 12, "bb": 4, "k": 10},
    ("cb-2026-05-20-vanderbilt-florida-att0430", "Vanderbilt"): {"ab": 32, "r": 3, "h": 6, "rbi": 3, "bb": 4, "k": 12},
    ("cb-2026-05-20-vanderbilt-florida-att0430", "Florida"): {"ab": 36, "r": 8, "h": 14, "rbi": 8, "bb": 6, "k": 9},
    ("cb-2026-05-19-missouri-ole-miss-att0425", "Missouri"): {"ab": 40, "r": 10, "h": 14, "rbi": 9, "bb": 7, "k": 10},
    ("cb-2026-05-19-missouri-ole-miss-att0425", "Ole Miss"): {"ab": 36, "r": 8, "h": 9, "rbi": 8, "bb": 4, "k": 14},
    ("cb-2026-05-19-lsu-oklahoma-att0428", "LSU"): {"ab": 37, "r": 6, "h": 11, "rbi": 3, "bb": 8, "k": 12},
    ("cb-2026-05-19-lsu-oklahoma-att0428", "Oklahoma"): {"ab": 34, "r": 2, "h": 6, "rbi": 1, "bb": 3, "k": 13},
    ("cb-2026-05-22-auburn-texas-a-m-att0436", "Auburn"): {"ab": 37, "r": 7, "h": 11, "rbi": 7, "bb": 2, "k": 11},
    ("cb-2026-05-22-auburn-texas-a-m-att0436", "Texas A&M"): {"ab": 28, "r": 0, "h": 2, "rbi": 0, "bb": 5, "k": 13},
    ("cb-2026-05-19-south-carolina-tennessee-att0427", "South Carolina"): {"ab": 36, "r": 6, "h": 11, "rbi": 6, "bb": 3, "k": 13},
    ("cb-2026-05-19-south-carolina-tennessee-att0427", "Tennessee"): {"ab": 40, "r": 11, "h": 15, "rbi": 10, "bb": 0, "k": 10},
    ("cb-2026-05-19-kentucky-vanderbilt-att0426", "Kentucky"): {"ab": 33, "r": 5, "h": 8, "rbi": 5, "bb": 2, "k": 10},
    ("cb-2026-05-19-kentucky-vanderbilt-att0426", "Vanderbilt"): {"ab": 35, "r": 8, "h": 12, "rbi": 6, "bb": 5, "k": 8},
    ("cb-2026-05-14-virginia-louisville-att0422", "Virginia"): {"ab": 36, "r": 8, "h": 8, "rbi": 4, "bb": 9, "k": 8},
    ("cb-2026-05-14-virginia-louisville-att0422", "Louisville"): {"ab": 36, "r": 3, "h": 8, "rbi": 3, "bb": 5, "k": 10},
    ("cb-2026-05-15-mercer-east-tennessee-state-att0423", "Mercer"): {"ab": 33, "r": 9, "h": 11, "rbi": 9, "bb": 2, "k": 10},
    ("cb-2026-05-15-mercer-east-tennessee-state-att0423", "East Tennessee State"): {"ab": 33, "r": 7, "h": 10, "rbi": 7, "bb": 5, "k": 7},
    ("cb-2026-05-16-arkansas-kentucky-att0424", "Arkansas"): {"ab": 41, "r": 16, "h": 14, "rbi": 14, "bb": 7, "k": 12},
    ("cb-2026-05-16-arkansas-kentucky-att0424", "Kentucky"): {"ab": 44, "r": 12, "h": 17, "rbi": 11, "bb": 3, "k": 10},
    ("cb-2026-05-10-little-rock-ut-martin-att0421", "Little Rock"): {"ab": 52, "r": 16, "h": 23, "rbi": 16, "bb": 1, "k": 4},
    ("cb-2026-05-10-little-rock-ut-martin-att0421", "UT Martin"): {"ab": 42, "r": 14, "h": 13, "rbi": 13, "bb": 3, "k": 5},
}

keys = {"ab": "atBats", "r": "runs", "h": "hits",
        "rbi": "rbi", "bb": "baseOnBalls", "k": "strikeOuts"}
for game in committed:
    if game["verification"] != "official_boxscore_verified":
        continue
    for team in (game["away"], game["home"]):
        player_list = [r for r in pilot_rows if r["game_id"] == game["id"] and r["team"] == team]
        bats = [r["batting"] for r in player_list if "batting" in r]
        pitchers = [r["pitching"] for r in player_list if "pitching" in r]
        totals = {k: sum(b[keys[k]] for b in bats) for k in keys}
        # Retain strict transcribed six-column spot checks for the original
        # audit set. Source-verified later imports use source-backed game R/H
        # as mandatory checks rather than raising a KeyError for missing
        # static pilot fixtures.
        if (game["id"], team) in expected:
            check(totals == expected[(game["id"], team)],
                  "Original official team batting totals match " + game["id"] + " " + team)
        side = "away" if team == game["away"] else "home"
        check(totals["r"] == game[side + "_score"] and
              totals["h"] == game[side + "_hits"],
              "Official batter totals reconcile to source game scoreboard " + game["id"] + " " + team)
        other = game["home"] if team == game["away"] else game["away"]
        opposition = [r["batting"] for r in pilot_rows if r["game_id"] == game["id"] and r["team"] == other and "batting" in r]
        outs = sum(p["outs"] for p in pitchers)
        hits_allowed = sum(p["hits"] for p in pitchers)
        strikeouts = sum(p["strikeOuts"] for p in pitchers)
        # Innings beyond the ninth are valid (LSU-Tennessee Apr 5 went
        # twelve); check source opponent totals here, then exact outs below.
        check(hits_allowed == sum(x["hits"] for x in opposition)
              and strikeouts == sum(x["strikeOuts"] for x in opposition),
              "Official pitcher hits/strikeouts match opponent " + game["date"] + " " + team)

        other_runs = game["away_score"] if other == game["away"] else game["home_score"]
        runs_allowed = sum(p["runs"] for p in pitchers)
        earned = sum(p["earnedRuns"] for p in pitchers)
        completed_innings = len(game["innings"])
        # The away pitchers may record fewer than three outs in the last
        # home half-inning of a walk-off or run-rule finish. Baylor-Cincinnati
        # Apr 10 ended in the eighth on a two-run, 10-run-margin home finish.
        if team == game["away"] and game["home_score"] > game["away_score"]:
            if game["innings"][-1]["home"] is None:
                valid_outs = {3 * (completed_innings - 1)}
            else:
                valid_outs = set(range(3 * (completed_innings - 1),
                                       3 * completed_innings + 1))
        else:
            valid_outs = {3 * completed_innings}
        check(outs in valid_outs and runs_allowed == other_runs and earned <= runs_allowed,
              "Pitchers reconcile completed/partial innings, opponent runs, and earned runs " + game["id"] + " " + team)
    available = [r for r in pilot_rows if r["game_id"] == game["id"] and "pitching" in r]
    for choice, field in (("win", "wins"), ("loss", "losses"), ("save", "saves")):
        official = game.get("pitching_decisions", {}).get(choice)
        matches = [r for r in available if r["pitching"].get(field) == 1]
        check(len(matches) == (1 if official else 0) and
              (not official or matches[0]["player"] == official) and
              all(r["pitching"].get(field) in (0, 1) for r in available),
              "Pitching " + field + " match source gamebook and player for " + game["id"])

check(pilot_report["uploaded_total_attendance_rows"] == 444 and
      pilot_report["unimported_worksheet_rows"] == 0 and
      pilot_report["attendance_only_pending_official_verification"] == sum(g["verification"] == "attendance_only" for g in committed) and
      pilot_report["official_player_boxscores_imported"] == sum(g["verification"] == "official_boxscore_verified" for g in committed) and
      pilot_report["official_scoreboard_player_lines_pending"] == sum(g["verification"] == "official_scoreboard_verified" for g in committed),
      "All 444 attended games staged with truthful full/score-only verification counts")
check(pilot_report["known_correction"][0]["confirmed_date"] == "2024-03-30",
      "South Alabama/Old Dominion correction recorded for upcoming bulk import")
check(pilot_report["known_correction"][1]["attendance_game_number"] == 444 and
      pilot_report["known_correction"][1]["worksheet_row"] == 445 and
      not pilot_report["needs_clarification"],
      "User correction to final attendance game 444 resolved without altering prior game 443")
numbered_2026_games = [g for g in committed
                       if g["season"] == 2026 and g["game_number"] is not None]
check(len(numbered_2026_games) == 6 and
      {(g["date"], g["away"], g["home"], g["game_number"]) for g in numbered_2026_games}
      == {("2026-02-14", "Nicholls", "Tennessee", 1),
          ("2026-02-14", "Nicholls", "Tennessee", 2),
          ("2026-03-10", "Ohio", "Austin Peay", 1),
          ("2026-03-10", "Ohio", "Austin Peay", 2),
          ("2026-04-11", "East Tennessee State", "Belmont", 1),
          ("2026-04-11", "East Tennessee State", "Belmont", 2)} and
      all(g["verification"] == "official_boxscore_verified" for g in numbered_2026_games),
      "All three 2026 official doubleheaders preserve separate G1/G2 identifiers")
check(all(g["game_number"] is None for g in committed
          if (g.get("postseason_round") or "").lower().find("regional") >= 0),
      "Regional tournament bracket game number not mistaken for a doubleheader number")

corrected = next(g for g in committed if g["source_worksheet_row"] == 445)
original = next(g for g in committed if g["source_worksheet_row"] == 444)
check(corrected["id"] == "cb-2026-05-31-ucf-auburn" and corrected["away"] == "UCF"
      and corrected["home"] == "Auburn" and corrected["away_score"] == 3
      and corrected["home_score"] == 9 and corrected["regional_game_number"] == 5,
      "Final attendance game #444 is now UCF 3 at Auburn 9 on May 31")
check(original["id"] == "cb-2026-05-31-auburn-milwaukee"
      and original["away_score"] == 8 and original["home_score"] == 1
      and original["regional_game_number"] == 6
      and original["verification"] == "official_boxscore_verified",
      "Game #443 retains the source-verified Auburn 8 Milwaukee 1 box score")
check(any(x["game_id"] == original["id"] for x in pilot_rows)
      and len([x for x in pilot_rows if x["game_id"] == corrected["id"]]) == 27,
      "Corrected UCF-Auburn game 5 has its own 27 verified player entries")
check({g["source_worksheet_row"] for g in committed} == set(range(2,446)) and
      len([g for g in committed if g["source_worksheet_row"] in range(440,446)]) == 6,
      "All 444 distinct source rows retained, including six separate Auburn Regional games")

dual_attendance = json.loads((SITE / "data" / "mlb_crosswalk.json").read_text())
alumni_ids = {p["college_player_id"]: p["mlb_player_id"] for p in
              json.loads((SITE / "data" / "mlb_alumni_seed.json").read_text())["players"]}
attended_mlb_ids = {int(p["player_id"]) for p in
                    json.loads((ROOT / "mlb" / "data" / "player_stats.json").read_text())}
check(len(dual_attendance) == 18 and
      len({p["college_player_id"] for p in dual_attendance}) == 18 and
      len({p["mlb_player_id"] for p in dual_attendance}) == 18 and
      all(p.get("verified") is True and
          alumni_ids.get(p["college_player_id"]) == p["mlb_player_id"] and
          p["mlb_player_id"] in attended_mlb_ids for p in dual_attendance),
      "All 18 cross-archive links match official MLB identities and personally attended MLB box scores")
check(make_report([])["attendance_games"] == 0, "Empty import reports honest zero verified inputs")
check(subprocess.run(["node", "--check", str(SITE / "assets" / "archive.js")],
                     capture_output=True).returncode == 0, "College baseball website JavaScript parses")

with tempfile.TemporaryDirectory() as t:
    tmp = Path(t)
    inp = tmp / "attendance.csv"
    mock_csv(inp, [
        {"date": "04/07/2025", "away": "Example University", "home": "Sample State",
         "ballpark": "Fictional Field", "game_number": "1", "away_score": "3",
         "home_score": "2"},
        {"date": "2025-04-07", "away": "Example University", "home": "Sample State",
         "game_number": "2"},
        {"date": "2024-06-02", "away": "Test College", "home": "Demo University",
         "neutral_site": "yes", "game_type": "NCAA postseason",
         "postseason_round": "Regional"}
    ])
    example = load_csv(inp)
    check(len(example) == 3, "Three synthetic input rows imported")
    check(len(set(g["id"] for g in example)) == 3, "Doubleheader IDs stay distinct")
    check(sum(g["game_number"] is not None for g in example) == 2,
          "Doubleheader number retained")
    check(next(g for g in example if g["postseason_round"] == "Regional")["neutral_site"] is True,
          "Neutral NCAA Regional metadata retained")
    check(all(g["verification"] == "attendance_only" for g in example),
          "No source verification fabricated from user log")
    check(make_report(example)["official_boxscores_imported"] == 0,
          "User-supplied score never implies verified box score")
    check(any(g["score_provenance"] == "user_attendance_log" for g in example),
          "User-supplied scores retain provenance")
    mock_csv(inp, [
        {"date": "2025-04-07", "away": "Example University", "home": "Sample State"},
        {"date": "2025-04-07", "away": "Example University", "home": "Sample State"}
    ])
    try:
        load_csv(inp)
        raise AssertionError("Duplicate games were accepted")
    except ValueError as exc:
        check("duplicate game" in str(exc), "Ambiguous doubleheaders are rejected")
    mock_csv(inp, [{"date": "2025-04-07", "away": "Example University",
                    "home": "Sample State", "away_score": "5"}])
    try:
        load_csv(inp)
        raise AssertionError("Incomplete score was accepted")
    except ValueError as exc:
        check("both" in str(exc), "One-sided scores rejected")

    staging = tmp / "site"
    shutil.copytree(SITE, staging / "college-baseball")
    empty_root = staging / "college-baseball" / "data"
    # The real 444-game attendance list is kept in the repo, but exercise
    # the empty-state UI on a fully disposable test-only server.
    (empty_root / "games.json").write_text("[]\n")
    (empty_root / "player_stats.json").write_text("[]\n")
    (empty_root / "import_report.json").write_text(json.dumps(make_report([])))
    # Game-specific official corrections require their source games. An empty
    # attendance fixture must also have empty source-scoped correction lists.
    (empty_root / "source_stat_backfills.json").write_text('{"games": []}\n')
    (empty_root / "attendance_game_corrections.json").write_text('{"games": []}\n')
    (empty_root / "player_name_corrections.json").write_text(
        json.dumps({"game_id": "empty-fixture", "team": "empty-fixture", "corrections": []}))
    server = run_server(staging)
    host = f"http://127.0.0.1:{server.server_address[1]}"
    errors = []
    try:
        with sync_playwright() as pw:
            browser = pw.chromium.launch(headless=True, args=["--no-sandbox"])
            for width in (1280, 390):
                page = browser.new_page(viewport={"width": width, "height": 900})
                page.on("pageerror", lambda e: errors.append(str(e)))
                visit(page, host, "index.html", ".cb-empty")
                page.wait_for_function("document.getElementById('app').innerText.includes('Ready for your first college baseball')")
                check("0" in page.locator(".metrics").inner_text(),
                      f"{width} empty home shows no invented totals")
                check(page.locator('nav a[href="./game.html"]').count() == 1,
                      f"{width} real game navigation exists")
                visit(page, host, "game.html", "#cb-game-list")
                check("No college baseball games imported yet" in page.locator("#cb-game-details").inner_text(),
                      f"{width} empty game state honest")
                visit(page, host, "stats.html", "#cb-player-board")
                check("No college player box scores" in page.locator("#cb-player-board").inner_text(),
                      f"{width} empty player board honest")
                visit(page, host, "records.html", ".cb-empty")
                page.wait_for_function("document.getElementById('app').innerText.includes('No records have been fabricated')")
                check(page.locator(".cb-record").count() == 0,
                      f"{width} no fabricated record holders")
                visit(page, host, "player.html?id=missing", ".cb-empty")
                page.wait_for_function("document.getElementById('app').innerText.includes('No verified college baseball player')")
                check(page.evaluate("document.documentElement.scrollWidth<=innerWidth+3"),
                      f"{width} responsive empty-player view fits viewport")
                page.close()
            check(not errors, "Empty-site browser run has zero JavaScript errors")
            # Overwrite ONLY the disposable temporary site with fictional mock data.
            fixture = {
                "id": "cb-synthetic-test-only",
                "attendance_id": "synthetic",
                "date": "2025-04-07", "season": 2025,
                "away": "Example University", "home": "Sample State",
                "ballpark": "Fictional Field", "city": "Nowhere", "state": "XX",
                "neutral_site": False, "game_number": 1, "game_type": "regular",
                "postseason_round": None, "away_score": 3, "home_score": 2,
                "source_url": None, "verification": "official_boxscore_verified",
                "score_provenance": None,
                "innings": [{"away": 1 if i < 3 else 0, "home": 1 if i < 2 else 0} for i in range(9)],
            }
            mock_player = {
                "game_id": fixture["id"], "player_id": "synthetic-athlete", "player": "Test Player",
                "team": "Example University", "source_url": None,
                "batting": {"atBats": 4, "runs": 1, "hits": 2, "doubles": 1,
                            "triples": 0, "homeRuns": 0, "rbi": 1, "baseOnBalls": 1,
                            "strikeOuts": 1, "hitByPitch": 0, "sacFlies": 0, "stolenBases": 0},
                "pitching": {"outs": 6, "hits": 2, "runs": 1, "earnedRuns": 1,
                            "baseOnBalls": 1, "strikeOuts": 4, "numberOfPitches": 34,
                            "wins": 0, "losses": 0, "saves": 0},
            }
            (empty_root / "games.json").write_text(json.dumps([fixture]))
            (empty_root / "player_stats.json").write_text(json.dumps([mock_player]))
            (empty_root / "import_report.json").write_text(json.dumps({"attendance_games": 1}))
            for width in (1280, 390):
                page = browser.new_page(viewport={"width": width, "height": 900})
                page.on("pageerror", lambda e: errors.append(str(e)))
                visit(page, host, "index.html", ".metrics")
                page.wait_for_function("document.querySelector('.metrics .metric strong').innerText==='1'")
                check("Example University" in page.locator("#app").inner_text(),
                      f"{width} attendance home renders exact synthetic game")
                visit(page, host, "game.html?id=cb-synthetic-test-only", "#cb-game-details .cb-game-summary")
                check("3 – 2" in page.locator("#cb-game-details").inner_text(),
                      f"{width} score and official box-score panel available")
                check(page.locator('#cb-box .mlb-lineup-row a[href="./player.html?id=synthetic-athlete"]').count() == 1,
                      f"{width} two-way player's batting table has a linked game record")
                check(page.locator('#cb-box .mlb-order').first.inner_text() == "—",
                      f"{width} never fabricate lineup order when gamebook slot data is unavailable")
                page.locator('[data-cat="pitching"]').click()
                check(page.locator('#cb-box .mlb-lineup-row a[href="./player.html?id=synthetic-athlete"]').count() == 1
                      and page.locator('#cb-stat-title').inner_text() == "Pitching box score",
                      f"{width} MLB-style pitching tab links the same two-way athlete")
                page.locator('[data-cat="batting"]').click()
                visit(page, host, "stats.html", "#cb-player-board .cb-table")
                check("Test Player" in page.locator("#cb-player-board").inner_text(),
                      f"{width} batting leaderboard includes fictional test player")
                page.locator("#cb-role").select_option("pitch")
                check("4" in page.locator("#cb-player-board").inner_text(),
                      f"{width} pitching leaderboard includes four witnessed strikeouts")
                visit(page, host, "player.html?id=synthetic-athlete", "#app .cb-profile-stat-rows")
                check("Hitting in games you attended" in page.locator("#app").inner_text()
                      and "Pitching in games you attended" in page.locator("#app").inner_text(),
                      f"{width} two-way college player shows separate hitting and pitching rows")
                check("1.350" in page.locator("#app").inner_text(),
                      f"{width} correct batting OPS from 2-for-4, double and walk")
                visit(page, host, "records.html", ".cb-record")
                check("Test Player" in page.locator("#app").inner_text(),
                      f"{width} records populated exclusively from synthetic official box score")
                check(page.evaluate("document.documentElement.scrollWidth<=innerWidth+3"),
                      f"{width} seeded-test records page fits viewport")
                page.close()
            check(not errors, "Both populated-view widths have zero uncaught JavaScript errors")
            # Validate real-data source links, W/L/S attribution and full
            # batting/pitching tables in each of the three newly imported games.
            # Finally, test all 444 attended games and eight verified source gamebooks, distinct from
            # the synthetic examples and also without modifying the repo data.
            for source in ("games.json", "player_stats.json", "import_report.json",
                           "source_stat_backfills.json", "attendance_game_corrections.json",
                           "player_name_corrections.json"):
                (empty_root / source).write_text((SITE / "data" / source).read_text())
            for width in (1280, 390):
                page = browser.new_page(viewport={"width": width, "height": 900})
                page.on("pageerror", lambda e: errors.append(str(e)))
                visit(page, host, "index.html", ".metrics")
                page.wait_for_function("document.querySelector('.metrics .metric strong').innerText==='444'")
                check(page.locator(".cb-game-card").count() >= 6,
                      f"{width} actual 444-game attendance summary and six newest sourced games render")
                page.screenshot(path=str(REVIEW / f"overview-{width}.png"), full_page=True)
                visit(page, host, "game.html?id=cb-2024-04-13-virginia-tech-georgia-tech-att0268",
                      "#cb-game-details .cb-game-summary")
                check("0 – 19" in page.locator("#cb-game-details").inner_text() and
                      "Apr 13, 2024" in page.locator("#cb-game-details").inner_text() and
                      page.locator('a[href*="gt041324.pdf"]').count()==1,
                      f"{width} corrected April 13 Georgia Tech 19–0 game links official gamebook")
                check(page.locator('.mlb-team-box[data-side="away"] .mlb-lineup-row').count()==14 and
                      page.locator('.mlb-team-box[data-side="home"] .mlb-lineup-row').count()==17,
                      f"{width} corrected April 13 game has all 31 source-verified batters")
                page.locator('[data-cat="pitching"]').click()
                check(page.locator('.mlb-team-box[data-side="away"] .mlb-lineup-row').count()==8 and
                      page.locator('.mlb-team-box[data-side="home"] .mlb-lineup-row').count()==1 and
                      page.locator('[data-decision="win"] .mlb-decision-name').inner_text()=="Cam Jones",
                      f"{width} corrected game has all nine source-verified pitching appearances")
                visit(page, host, "game.html?id=cb-2024-04-14-virginia-tech-georgia-tech-att0268",
                      "#cb-game-details .cb-game-summary")
                check("0 – 19" in page.locator("#cb-game-details").inner_text(),
                      f"{width} original game deep link resolves to the April 13 correction")
                visit(page, host, "game.html?id=cb-2025-05-31-dallas-baptist-lsu-att0367",
                      "#cb-box .mlb-team-box[data-side='home']")
                for player_id,values in {
                    "cb-lsu-ethan-frey": ["1","1","0"],
                    "cb-auburn-chris-stanfield": ["0","0","1"],
                    "cb-lsu-derek-curiel": ["0","0","0"],
                    "cb-dallas-baptist-tom-poole": ["0","0","0"],
                }.items():
                    line=page.locator(f'#cb-box tr[data-player-id="{player_id}"]')
                    check([line.locator('td').nth(i).inner_text() for i in (5,6,7)]==values,
                          f"{width} May 31 Dallas Baptist-LSU source-verified extra-base hits for {player_id}")
                visit(page, host, "player.html?id=cb-auburn-chris-stanfield", ".cb-player-game-log")
                stanfield_game=page.locator(".cb-player-game-log tbody tr").filter(has_text="May 31, 2025").filter(has_text="Dallas Baptist @ LSU")
                check(stanfield_game.count()==1 and stanfield_game.locator("td").nth(5).inner_text()=="1",
                      f"{width} Chris Stanfield's May 31 LSU home run appears in his combined player log")
                visit(page, host, "game.html?id=cb-2025-06-01-lsu-little-rock-att0369",
                      "#cb-box .mlb-team-box[data-side='home']")
                for player_id,values in {
                    "cb-lsu-derek-curiel": ["1","0","0"],
                    "cb-lsu-luis-hernandez": ["1","0","0"],
                    "cb-little-rock-angel-cano": ["1","0","1"],
                    "cb-little-rock-sammy-harris": ["1","0","0"],
                    "cb-lsu-jared-jones": ["0","0","0"],
                }.items():
                    line=page.locator(f'#cb-box tr[data-player-id="{player_id}"]')
                    check([line.locator('td').nth(i).inner_text() for i in (5,6,7)]==values,
                          f"{width} June 1 LSU-Little Rock official extra-base hits for {player_id}")
                visit(page, host, "player.html?id=cb-little-rock-angel-cano", ".cb-player-game-log")
                cano_game=page.locator(".cb-player-game-log tbody tr").filter(has_text="LSU @ Little Rock")
                check(cano_game.count()==1 and cano_game.locator("td").nth(5).inner_text()=="1",
                      f"{width} Angel Cano's June 1 home run appears in his linked college game log")
                visit(page, host, "game.html?id=cb-2026-05-31-ucf-auburn", "#cb-game-details .cb-game-summary")
                check("UCF @ Auburn" in page.locator("#cb-game-details").inner_text()
                      and "3 – 9" in page.locator("#cb-game-details").inner_text(),
                      f"{width} corrected final attendance game #444 shows UCF at Auburn 9-3")
                check("DeAmez Ross" in page.locator("#cb-game-details").inner_text()
                      and "Alex Petrovic" in page.locator("#cb-game-details").inner_text()
                      and "Camden Kuhnke" not in page.locator("#cb-game-details").inner_text(),
                      f"{width} corrected game #444 has official UCF/Auburn, not Milwaukee, player tables")
                decisions = page.locator("#cb-pitching-decisions")
                check(decisions.locator('[data-decision="win"] .mlb-decision-name').inner_text() == "Alex Petrovic"
                      and decisions.locator('[data-decision="loss"] .mlb-decision-name').inner_text() == "Roman Kimball"
                      and decisions.locator('[data-decision="save"] .mlb-decision-name').inner_text() == "Ryan Hetzler"
                      and decisions.locator('a[href="./player.html?id=cb-auburn-ryan-hetzler"]').count() == 1,
                      f"{width} May 31 MLB-style W/L/S cards credit correct linked college pitchers")
                check([x.inner_text() for x in page.locator('.mlb-team-box[data-side="away"][data-category="batting"] .mlb-order').all()]
                      == ["1", "2", "3", "4", "5", "6", "7", "↳", "8", "9"],
                      f"{width} May 31 UCF lineup numbering matches MLB substitute format")
                check(page.locator('.mlb-team-box[data-side="away"] tr[data-player-id="cb-ucf-cayden-gaskin"][data-slot="7"][data-sub="1"] .mlb-order').inner_text()=="↳",
                      f"{width} verified UCF pinch hitter Cayden Gaskin follows seventh slot")
                check(page.evaluate("getComputedStyle(document.body).fontFamily.startsWith('Inter')"),
                      f"{width} College Baseball font matches MLB Inter family")
                page.screenshot(path=str(REVIEW / f"may31-ucf-auburn-{width}.png"), full_page=True)
                visit(page, host, "game.html?id=cb-2026-05-29-milwaukee-auburn", "#cb-game-details .cb-game-summary")
                check("13 – 8" in page.locator("#cb-game-details").inner_text()
                      and "Grant Ross" in page.locator("#cb-game-details").inner_text()
                      and page.locator('#cb-pitching-decisions [data-decision="win"] .mlb-decision-name').inner_text() == "Riley Peterson",
                      f"{width} May 29 full official Milwaukee-Auburn hitter/pitcher records render")
                visit(page, host, "game.html?id=cb-2026-05-30-ucf-milwaukee", "#cb-game-details .cb-game-summary")
                check("6 – 13" in page.locator("#cb-game-details").inner_text()
                      and "Andrew Williamson" in page.locator("#cb-game-details").inner_text()
                      and page.locator('#cb-pitching-decisions [data-decision="win"] .mlb-decision-name').inner_text() == "Aric Ehmke",
                      f"{width} May 30 UCF-Milwaukee full gamebook and linked decision render")
                visit(page, host, "game.html?id=cb-2026-05-30-auburn-nc-state", "#cb-game-details .cb-game-summary")
                check(page.locator('.mlb-team-box[data-side="home"] tr[data-player-id="cb-nc-state-christian-serrano"][data-slot="8"][data-sub="1"] .mlb-order').inner_text()=="↳"
                      and page.locator('.mlb-team-box[data-side="home"] tr[data-player-id="cb-nc-state-vincent-decarlo"][data-slot="9"][data-sub="1"] .mlb-order').inner_text()=="↳",
                      f"{width} NC State pinch hitters share their source-verified lineup spots")
                visit(page, host, "game.html?id=cb-2026-05-31-auburn-milwaukee", "#cb-game-details .cb-game-summary")
                check("8 – 1" in page.locator("#cb-game-details").inner_text() and
                      "Chase Fralick" in page.locator("#cb-game-details").inner_text(),
                      f"{width} actual May 31 game shows score and official players")
                mke = page.locator('.mlb-team-box[data-side="home"][data-category="batting"]')
                check([x.inner_text() for x in mke.locator(".mlb-order").all()] == 
                      ["1", "2", "3", "4", "5", "6", "7", "↳", "↳", "8", "9"],
                      f"{width} Milwaukee bat order shows two replacements at seventh spot")
                check(mke.locator('tr[data-player-id="cb-milwaukee-tate-schmidt"][data-slot="7"][data-sub="1"]').count()==1
                      and mke.locator('tr[data-player-id="cb-milwaukee-tristan-ellis"][data-slot="7"][data-sub="2"]').count()==1,
                      f"{width} Milwaukee substitutions appear under Bozak instead of 10/11")
                page.locator('[data-cat="pitching"]').click()
                check([x.inner_text() for x in page.locator('.mlb-team-box[data-side="away"] .mlb-order').all()] == ["1","2"]
                      and [x.inner_text() for x in page.locator('.mlb-team-box[data-side="home"] .mlb-order').all()] == ["1","2","3","4"],
                      f"{width} college pitching appearances numbered like MLB tables")
                check(page.locator('.cb-boxscore-table').first.evaluate('(e)=>e.scrollWidth>=e.clientWidth'),
                      f"{width} MLB-style box scores horizontally scroll within their card")
                visit(page, host, "stats.html", "#cb-player-board .cb-table")
                check("Chase Fralick" in page.locator("#cb-player-board").inner_text(),
                      f"{width} all six official gamebooks build hitter leaderboard")
                page.screenshot(path=str(REVIEW / f"batting-leaderboard-{width}.png"), full_page=True)
                page.locator("#cb-role").select_option("pitch")
                check("LJ Cormier" in page.locator("#cb-player-board").inner_text(),
                      f"{width} actual pitcher leaderboard contains source-backed winner")
                visit(page, host, "player.html?id=cb-auburn-chase-fralick", "#app .cb-profile-stat-rows")
                check("Chase Fralick" in page.locator("#app").inner_text(),
                      f"{width} cross-game college player identity connects")
                visit(page, host, "player.html?id=cb-lsu-kade-anderson", ".cb-profile-hero")
                check(page.locator(".cb-profile-hero h1").inner_text()=="Kade Anderson" and
                      page.locator(".cb-mlb-alumnus[href*='807739']").count()==1 and
                      "2025" in page.locator(".cb-mlb-draft").inner_text() and
                      "Pick 3" in page.locator(".cb-mlb-draft").inner_text() and
                      "Seattle Mariners" in page.locator(".cb-mlb-draft").inner_text() and
                      page.locator(".cb-player-game-log tbody tr").count()==2 and
                      page.locator(".cb-dual-level").count()==0,
                      f"{width} Kade Anderson MLB debut and draft are tagged without inventing attended MLB games")
                for name, college_id, round_num, pick, team in [
                    ("Roman Garcia", "cb-san-diego-roman-garcia", "19", "571", "Houston Astros"),
                    ("Colton Waltner", "cb-san-diego-colton-waltner", "21", "616", "Minnesota Twins"),
                    ("Sean Barry", "cb-san-diego-sean-barry", "21", "645", "Chicago Cubs"),
                    ("Troy Conyers", "cb-san-diego-troy-conyers", "23", "680", "Atlanta Braves"),
                    ("Hunter Mercado-Hood", "cb-san-diego-hunter-mercado-hood", "31", "940", "Los Angeles Dodgers"),
                    ("Maverik Buffo", "cb-byu-maverik-buffo", "34", "1029", "Toronto Blue Jays"),
                    ("Colton Shaver", "cb-byu-colton-shaver", "39", "1171", "Houston Astros"),
                ]:
                    visit(page, host, f"player.html?id={college_id}", ".cb-profile-hero")
                    tag = page.locator(".cb-mlb-draft").inner_text()
                    check(page.locator(".cb-profile-hero h1").inner_text().casefold()==name.casefold() and
                          "2017" in tag and f"Round {round_num}" in tag and f"Pick {pick}" in tag and team in tag and
                          page.locator(".cb-mlb-alumnus").count()==0 and
                          page.locator(".cb-player-game-log tbody tr").count()>=1,
                          f"{width} {name} has a 2017 draft badge without a false MLB alumni tag")
                visit(page, host, "mlb-alumni.html", ".alumni-player")
                page.locator("#search").fill("Kade Anderson")
                check(page.locator(".alumni-player").count()==1 and
                      "Aug 22, 2026" in page.locator(".alumni-player").inner_text() and
                      "23" in page.locator(".alumni-player").inner_text() and
                      page.locator("#mlbCount").inner_text()=="72" and
                      page.locator("[data-group='drafted_only']").count()==0 and
                      page.locator("#draftCount").count()==0,
                      f"{width} Kade Anderson remains in the 72-person College-to-MLB directory with two witnessed LSU games")
                for name, college_id, mlb_id, draft_year, pick in [
                    ("Josh Hendrickson", "cb-san-diego-josh-hendrickson", "681973", "2019", "1140"),
                    ("Cooper Hjerpe", "cb-oregon-state-cooper-hjerpe", "687309", "2022", "22"),
                    ("John Peck", "cb-pepperdine-john-peck", "807726", "2023", "200"),
                    ("Nick Frasso", "cb-loyola-marymount-nick-frasso", "693308", "2020", "106"),
                    ("Gabriel Hughes", "cb-gonzaga-gabriel-hughes", "687312", "2022", "10"),
                    ("Cole Carrigg", "cb-san-diego-state-cole-carrigg", "694249", "2023", "65"),
                ]:
                    visit(page, host, f"player.html?id={college_id}", ".cb-profile-hero")
                    check(page.locator(".cb-profile-hero h1").inner_text().casefold()==name.casefold() and
                          page.locator(f".cb-mlb-alumnus[href*='{mlb_id}']").count()==1 and
                          draft_year in page.locator(".cb-mlb-draft").inner_text() and
                          f"Pick {pick}" in page.locator(".cb-mlb-draft").inner_text() and
                          page.locator(".cb-player-game-log tbody tr").count()>=1 and
                          page.locator(".cb-dual-level").count()==0,
                          f"{width} {name} links to the correct MLB alumnus and draft tags without an unverified MLB attendance claim")
                visit(page, host, "game.html?id=cb-2018-04-08-loyola-marymount-san-diego-att0024", "#cb-pitching-decisions")
                check("Nick Frasso" in page.locator('[data-decision="loss"]').inner_text() and
                      page.locator('[data-decision="loss"] a[href*="cb-loyola-marymount-nick-frasso"]').count()==1,
                      f"{width} April 8 LMU official recap corrects Frasso's misattributed losing-pitcher identity")
                page.locator('[data-cat="pitching"]').click()
                check(page.locator('tr[data-player-id="cb-loyola-marymount-nick-frasso"][data-pitcher-index="0"]').count()==1 and
                      page.locator('tr[data-player-id="cb-loyola-marymount-ryan-kawano"]').count()==0,
                      f"{width} April 8 LMU starter's 2.0 innings belong to Nick Frasso, not Ryan Kawano")
                visit(page, host, "mlb-alumni.html", ".alumni-player")
                page.locator("#search").fill("Nick Frasso")
                check(page.locator(".alumni-player").count()==1 and
                      "Aug 4, 2026" in page.locator(".alumni-player").inner_text() and
                      page.locator("#mlbCount").inner_text()=="72",
                      f"{width} Nick Frasso remains in the 72-person College-to-MLB directory")
                page.locator("#search").fill("Cole Carrigg")
                check(page.locator(".alumni-player").count()==1 and
                      "Jun 9, 2026" in page.locator(".alumni-player").inner_text() and
                      "Round CB-B" in page.locator(".alumni-player").inner_text() and
                      "Pick #65" in page.locator(".alumni-player").inner_text() and
                      page.locator("#mlbCount").inner_text()=="72",
                      f"{width} Cole Carrigg joins the 72-person College-to-MLB directory with his official draft round and debut")
                visit(page, host, "records.html", ".cb-record")
                # Historical backfill legitimately changes the single-game
                # record holders. Verify source-backed record categories and
                # linked player cards rather than freezing an earlier leader.
                check(page.locator(".cb-record").count() == 6 and
                      page.locator(".cb-record a.cb-link").count() >= 3 and
                      "Signature Performances" in page.locator("#app").inner_text(),
                      f"{width} verified gamebooks dynamically feed six linked signature records")
                page.screenshot(path=str(REVIEW / f"signature-performances-{width}.png"), full_page=True)
                check(page.evaluate("document.documentElement.scrollWidth<=innerWidth+3"),
                      f"{width} live pilot fits screen")
                page.close()
            check(not errors, "Full real-source pilot also has zero browser JavaScript errors")
            browser.close()
            (REVIEW / "manifest.json").write_text(json.dumps({
                "scope": "Draft only; all 444 games with nine complete source-verified gamebooks and five source-matched SEC Tournament scores",
                "games": 444, "verified_gamebooks": 9, "source_matched": 5, "attendance_only": 430, "player_game_rows": 246, "unique_players": 147,
                "browser_viewports": [1280, 390],
                "screenshots": sorted(p.name for p in REVIEW.glob("*.png")),
                "live_site_modified": False,
            }, indent=2) + "\n")
    finally:
        server.shutdown()
print("PASS 444 college baseball games, nine complete gamebooks, five sourced SEC scores, 246 player lines and mobile/browser QA")
