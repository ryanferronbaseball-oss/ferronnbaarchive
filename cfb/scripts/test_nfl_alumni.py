#!/usr/bin/env python3
"""Audit verified college-football-to-NFL crosswalk and desktop/mobile alumni view."""
import json
import re
import subprocess
import tempfile
import threading
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / "cfb" / "data"
games = json.loads((DATA / "games.json").read_text())
rows = json.loads((DATA / "player_stats.json").read_text())
cross = json.loads((DATA / "nfl_crosswalk.json").read_text())
by_id = {}
for row in rows:
    by_id.setdefault(row["athlete_id"], []).append(row)
ids = {g["id"] for g in games}
expected = {
    "cfb-usd-dalton-kincaid": ("nfl", 25, 2),
    "cfb-usd-michael-bandy": ("nfl", None, 2),
    "cfb-usd-ross-dwelley": ("nfl", None, 1),
    "cfb-wfu-demond-claiborne": ("nfl", 198, 1),
    "cfb-wfu-karon-prunty": ("nfl", 171, 1),
    "cfb-ncs-justin-joly": ("nfl", 152, 1),
    "cfb-usd-reid-sinnett": ("roster_only", None, 2),
}

def check(condition, message):
    assert condition, message
    print("PASS", message, flush=True)

check(len(games) == 5, "Existing five CFB attendance games intact")
check(len(cross) == len(expected), "All seven independently identified NFL links are included")
check(len(set(x["athlete_id"] for x in cross)) == len(cross), "No duplicate football player IDs")
check(set(x["athlete_id"] for x in cross) == set(expected), "NFL crosswalk uses exact CFB gamebook IDs")
check(all(p["source_url"].startswith("https://") for p in cross), "NFL appearance evidence links provided")
check(all(p["category"] in ("nfl", "roster_only") for p in cross), "Rosters not conflated with game appearances")
check(sum(p["category"] == "nfl" for p in cross) == 6, "Six verified NFL appearance alumni")
check(sum(p["category"] == "roster_only" for p in cross) == 1, "One separately labeled NFL roster/preseason player")
check(sum(p.get("draft_pick") is not None for p in cross) == 4, "Four verified NFL draft picks")
check(sum(p.get("draft_pick") is not None and p["draft_pick"] <= 32 for p in cross) == 1,
      "One first-round pick: Dalton Kincaid")
seen = set()
for person in cross:
    pid = person["athlete_id"]
    category, pick, count = expected[pid]
    appearances = {r["game_id"] for r in by_id[pid]}
    check(len(appearances) == count and appearances <= ids and person["category"] == category
          and person["draft_pick"] == pick, pid + " source-verified game and draft mapping")
    seen.update(appearances)
check(len(seen) == 4, "Exactly four attended games involve confirmed pathway players")
check(next(x for x in cross if "kincaid" in x["athlete_id"])["draft_school"] == "Utah",
      "San Diego-to-Utah transfer preserved in draft metadata")
check(next(x for x in cross if "joly" in x["athlete_id"])["draft_team"] == "Denver Broncos"
      and next(x for x in cross if "joly" in x["athlete_id"])["nfl_team"] == "Miami Dolphins",
      "Justin Joly drafting team distinct from later NFL team")

page_html = (ROOT / "cfb/nfl-alumni.html").read_text()
inline = re.findall(r"<script(?: [^>]*)?>([\s\S]*?)</script>", page_html)
for script in inline:
    if not script.strip():
        continue
    with tempfile.NamedTemporaryFile("w", suffix=".js") as f:
        f.write(script)
        f.flush()
        res = subprocess.run(["node", "--check", f.name], text=True, capture_output=True)
        check(res.returncode == 0, "Alumni JavaScript syntax valid: " + res.stderr[:300])
nav = (ROOT / "cfb/assets/archive.js").read_text()
check('["nfl-alumni.html","To the NFL","nfl"]' in nav, "CFB archive includes To the NFL tab")
class Quiet(SimpleHTTPRequestHandler):
    def log_message(self, *args):
        pass

server = ThreadingHTTPServer(("127.0.0.1", 0), partial(Quiet, directory=str(ROOT)))
threading.Thread(target=server.serve_forever, daemon=True).start()
base = f"http://127.0.0.1:{server.server_address[1]}"
errors = []
try:
    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=True, args=["--no-sandbox"])
        for width in (1280, 390):
            page = browser.new_page(viewport={"width": width, "height": 900})
            page.on("pageerror", lambda err: errors.append(str(err)))
            response = page.goto(base + "/cfb/nfl-alumni.html", wait_until="domcontentloaded")
            check(response.status == 200, f"{width} college to NFL page opens")
            page.wait_for_function("document.getElementById('nflCount').textContent === '6'",
                                   timeout=15000)
            check(page.locator("nav a[aria-current='page'][href='./nfl-alumni.html']").count() == 1,
                  f"{width} To the NFL navigation active")
            check(page.locator("#rosterCount").inner_text() == "1" and
                  page.locator("#seenCount").inner_text() == "4" and
                  page.locator("#firstCount").inner_text() == "1",
                  f"{width} verified career pathway summary totals")
            check(page.locator(".cards .player").count() == 6,
                  f"{width} all six independently verified NFL player cards display")
            check(page.locator('.player[data-player-id="cfb-usd-dalton-kincaid"]').count() == 1,
                  f"{width} Dalton Kincaid college player profile present")
            k = page.locator('.player[data-player-id="cfb-usd-dalton-kincaid"]')
            check("117" in k.inner_text() and "Utah" in k.inner_text()
                  and "Pick #25" in k.inner_text(),
                  f"{width} Kincaid witnessed yards, school transfer and first-round draft")
            check(k.locator('a[href="./game.html?id=cfb-2018-11-10-davidson-usd"]').count() >= 1,
                  f"{width} Kincaid witnessed college game deep link")
            check("371" in page.locator('.player[data-player-id="cfb-usd-michael-bandy"]').inner_text()
                  and "324" in page.locator('.player[data-player-id="cfb-usd-michael-bandy"]').inner_text(),
                  f"{width} Bandy 371 witnessed receiving yards, 324-yard single-game peak")
            check("35" in page.locator('.player[data-player-id="cfb-wfu-demond-claiborne"]').inner_text(),
                  f"{width} Claiborne witnessed rush yardage displayed")
            check(page.locator('.player[data-player-id="cfb-wfu-karon-prunty"] .line').inner_text().count("1") >= 1,
                  f"{width} Prunty defensive tackles accurately represented")
            check("Denver Broncos" in page.locator('.player[data-player-id="cfb-ncs-justin-joly"]').inner_text()
                  and "Miami Dolphins" in page.locator('.player[data-player-id="cfb-ncs-justin-joly"]').inner_text(),
                  f"{width} Joly drafted team and later club both visible")
            page.locator("#search").fill("Bandy")
            check(page.locator(".cards .player").count() == 1, f"{width} player search")
            page.locator("#search").fill("NC State")
            check(page.locator(".cards .player").count() == 1, f"{width} college search")
            page.locator("#search").fill("Utah")
            check(page.locator(".cards .player").count() == 1, f"{width} transfer/draft school search")
            page.locator("#search").fill("")
            page.locator("#sort").select_option("name")
            check(page.locator(".cards .player").count() == 6, f"{width} sorting keeps all alumni")
            page.locator('[data-group="roster_only"]').click()
            check(page.locator(".cards .player").count() == 1
                  and "Reid Sinnett" in page.locator(".cards").inner_text()
                  and "no verified regular-season" in page.locator(".cards").inner_text(),
                  f"{width} NFL roster-only category does not imply verified NFL games")
            page.locator('[data-group="nfl"]').click()
            check(page.locator(".cards .player").count() == 6, f"{width} tab switch returns all NFL alumni")
            check(page.evaluate("document.documentElement.scrollWidth<=innerWidth+3"),
                  f"{width} no horizontal overflow")
            check(not errors, f"{width} no uncaught JavaScript errors: {errors}")
            page.close()
        browser.close()
finally:
    server.shutdown()
print("PASS CFB-to-NFL initial verified crosswalk and desktop/mobile browser QA")
