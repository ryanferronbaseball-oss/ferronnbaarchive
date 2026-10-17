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
check(len(attended) == len(committed) == 444, "All 444 user-supplied college baseball games preserved")
check({g["id"] for g in attended} == {g["id"] for g in committed},
      "Official site attendance identities match normalized uploaded spreadsheet")
check(all(g["verification"] == "attendance_only" for g in committed),
      "No submitted college games falsely treated as officially verified")
check(sum(g["game_number"] is not None for g in committed) == 26,
      "Thirteen same-day doubleheader pairs remain 26 distinct entries")
check(len([g for g in committed if g["date"] == "2024-03-30" and g["away"] == "South Alabama" and g["home"] == "Old Dominion"]) == 1,
      "South Alabama at Old Dominion corrected to 2024-03-30")
check(len([g for g in committed if "NEEDS MATCH REVIEW" in (g.get("notes") or "")]) == 1,
      "Ambiguous Auburn–Milwaukee source entry is flagged, not silently substituted")
check(json.loads((SITE / "data" / "player_stats.json").read_text()) == [],
      "No invented historical college baseball box scores")
check(json.loads((SITE / "data" / "mlb_crosswalk.json").read_text()) == [],
      "No false college-to-MLB player identity matches")
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
    (empty_root / "import_report.json").write_text(json.dumps(make_report([])))
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
                check(page.locator('#cb-game-details a[href="./player.html?id=synthetic-athlete"]').count() == 2,
                      f"{width} two-way player links from batting and pitching tables")
                visit(page, host, "stats.html", "#cb-player-board .cb-table")
                check("Test Player" in page.locator("#cb-player-board").inner_text(),
                      f"{width} batting leaderboard includes fictional test player")
                page.locator("#cb-role").select_option("pitch")
                check("4" in page.locator("#cb-player-board").inner_text(),
                      f"{width} pitching leaderboard includes four witnessed strikeouts")
                visit(page, host, "player.html?id=synthetic-athlete", "#app .metrics")
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
            browser.close()
    finally:
        server.shutdown()
print("PASS college baseball foundation, no fabricated attendance, import and responsive browser QA")
