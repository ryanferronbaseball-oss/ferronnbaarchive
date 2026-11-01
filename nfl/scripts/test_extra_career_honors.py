#!/usr/bin/env python3
"""Verify NFL career honor identity, award distinctions, and clickable profile UI."""
import json
import re
import subprocess
import tempfile
import threading
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
try:
    from playwright.sync_api import sync_playwright
except ImportError:
    sync_playwright = None

ROOT = Path(__file__).resolve().parents[2]
extra = json.loads((ROOT / "nfl/data/extra_career_honors.json").read_text())
base = json.loads((ROOT / "nfl/data/career_awards.json").read_text())
rows = json.loads((ROOT / "nfl/data/player_stats.json").read_text())
profiles = {str(row["athlete_id"]): row["player"] for row in rows if row.get("athlete_id") is not None}
players = extra["players"]
assert players and set(players).issubset(profiles)
pro_bowl_players = {athlete_id for athlete_id, awards in base["players"].items() if awards.get("pro_bowl_count", 0)}
yearly_pro_bowl_players = {athlete_id for athlete_id, awards in players.items() if "pro_bowl_years" in awards}
assert yearly_pro_bowl_players == pro_bowl_players, (yearly_pro_bowl_players ^ pro_bowl_players)
for athlete_id, awards in players.items():
    assert profiles[athlete_id] == awards["name"], (athlete_id, awards["name"])
    for award, entries in awards.items():
        if award == "name":
            continue
        assert isinstance(entries, list) and entries, (athlete_id, award)
        if award == "pro_bowl_years":
            assert len(entries) == base["players"][athlete_id]["pro_bowl_count"]
            assert entries == sorted(set(entries)) and all(1990 <= year <= 2025 for year in entries)
        elif award == "all_decade":
            assert all(e["decade"] in ("1990s", "2000s", "2010s") for e in entries)
        else:
            assert all(isinstance(e["year"], int) for e in entries), (athlete_id, award)
for athlete_id, expected in {
    "1682": {"super_bowl", "super_bowl_mvp", "walter_payton", "franchise_honor"},
    "5528": {"nfl_100", "all_decade", "retired_number", "franchise_honor", "walter_payton"},
    "10455": {"ap_droy", "all_decade"},
    "1755": {"ap_oroy", "all_decade"},
    "3043078": {"ap_opoy"},
    "4697": {"super_bowl"},
}.items():
    assert expected.issubset(players[athlete_id])
assert [e["year"] for e in players["4697"]["super_bowl"]] == [2003, 2004]
assert players["5528"]["retired_number"] == [{"year": 2026, "team": "Arizona Cardinals", "number": "11"}]
assert players["668"]["ap_comeback"][0]["year"] == 1999
assert players["2971282"]["pro_bowl_years"] == [2018, 2021, 2023]
assert players["2299"]["pro_bowl_years"] == [2003, 2006]
print(f"PASS NFL honor data joins exact archive athlete IDs; all {len(pro_bowl_players)} Pro Bowl players have year lists matching their career counts")

page_source = (ROOT / "nfl/player.html").read_text()
script = re.findall(r"<script>([\s\S]*?)</script>", page_source)[0]
with tempfile.NamedTemporaryFile(mode="w", suffix=".js") as temp:
    temp.write(script)
    temp.flush()
    result = subprocess.run(["node", "--check", temp.name], capture_output=True, text=True)
    assert result.returncode == 0, result.stderr
print("PASS NFL profile JavaScript syntax")
if sync_playwright is None:
    print("SKIP browser interaction checks: local Playwright is unavailable (run separately in the browser)")
    raise SystemExit(0)


class QuietHandler(SimpleHTTPRequestHandler):
    def log_message(self, *_args):
        pass


server = ThreadingHTTPServer(("127.0.0.1", 0), partial(QuietHandler, directory=str(ROOT)))
threading.Thread(target=server.serve_forever, daemon=True).start()
origin = f"http://127.0.0.1:{server.server_address[1]}/nfl/player.html?id="


def inspect(page, athlete_id, badge_text, tab_text, year_text):
    page.goto(origin + athlete_id, wait_until="domcontentloaded")
    page.wait_for_function("document.getElementById('careerHonors').hidden === false")
    badge = page.locator("#awardBadges .award-badge.visible").filter(has_text=badge_text)
    assert badge.count() == 1, (athlete_id, badge_text)
    badge.click()
    selected = page.locator('#honorTabs button[aria-selected="true"]')
    assert tab_text in selected.inner_text(), (athlete_id, selected.inner_text())
    panel_id = selected.get_attribute("aria-controls")
    assert year_text in page.locator("#" + panel_id).inner_text(), (athlete_id, year_text)
    assert page.evaluate("document.documentElement.scrollWidth<=window.innerWidth+2"), athlete_id


try:
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True, args=["--no-sandbox"])
        for width in (1360, 390):
            page = browser.new_page(viewport={"width": width, "height": 900})
            errors = []
            page.on("pageerror", lambda error: errors.append(str(error)))
            inspect(page, "1682", "SUPER BOWL MVP", "Super Bowl MVP", "1999 · Super Bowl XXXIV · St. Louis Rams")
            inspect(page, "5528", "RETIRED NUMBER", "Retired Number", "2026 · Arizona Cardinals · No. 11")
            inspect(page, "5528", "NFL 100", "NFL 100", "2019")
            inspect(page, "5528", "RING OF HONOR", "Franchise Honor", "2026 · Arizona Cardinals · Ring of Honor")
            inspect(page, "10455", "DEFENSIVE ROOKIE", "Defensive Rookie", "2007 · San Francisco 49ers")
            inspect(page, "3043078", "OFFENSIVE PLAYER", "Offensive Player", "2020 · Tennessee Titans")
            inspect(page, "4697", "SUPER BOWL CHAMPION", "Super Bowl Champion", "2004 · Super Bowl XXXIX")
            inspect(page, "8479", "ALL-DECADE", "All-Decade", "2010s")
            inspect(page, "2612", "PRO BOWL", "Pro Bowl", "2006")
            inspect(page, "5528", "PRO BOWL", "Pro Bowl", "2013")
            inspect(page, "2971282", "PRO BOWL", "Pro Bowl", "2023")
            inspect(page, "2299", "PRO BOWL", "Pro Bowl", "2006")
            inspect(page, "668", "COMEBACK", "Comeback Player", "1999 · San Francisco 49ers")
            page.goto(origin + "4036134", wait_until="domcontentloaded")
            page.wait_for_function("document.getElementById('playerName').textContent !== 'Player profile'")
            assert page.locator("#awardBadges .award-badge.visible").count() == 0
            assert not errors, (width, errors)
            print(f"PASS {width}px NFL tag click-through, correct year details, empty-honors suppression, no JS errors")
            page.close()
        browser.close()
finally:
    server.shutdown()
