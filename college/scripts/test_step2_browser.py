#!/usr/bin/env python3
"""Real HTTP/Chromium end-to-end checks for the two NCAA Courtside Archive pages.

CI installs Playwright/Chromium explicitly. Run after Step 1 exported college
data has been committed to college/data on the development branch.
"""
import json
import threading
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[2]
OUTPUT = ROOT / "college" / "output" / "step2-browser"
OUTPUT.mkdir(parents=True, exist_ok=True)
class SilentHandler(SimpleHTTPRequestHandler):
    def log_message(self, *_):
        return

server = ThreadingHTTPServer(("127.0.0.1", 0), partial(SilentHandler, directory=str(ROOT)))
threading.Thread(target=server.serve_forever, daemon=True).start()
url = f"http://127.0.0.1:{server.server_address[1]}/college/"

checks = []
errors = []
completed = False
def check(condition, label):
    if not condition:
        raise AssertionError(label)
    checks.append(label)
    print("PASS", label, flush=True)

def record(page):
    page.on("pageerror", lambda err: errors.append(str(err)))
    # Portrait image requests do not have to succeed for a historical player;
    # the existing NBA component has an intentional portrait fallback.
    page.route("https://a.espncdn.com/**", lambda route: route.abort())

try:
    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=True, args=["--no-sandbox"])
        page = browser.new_page(viewport={"width": 1440, "height": 1080}, device_scale_factor=1)
        record(page)
        response = page.goto(url + "stats.html", wait_until="domcontentloaded")
        check(response.status == 200, "College leaderboard loads over real HTTP")
        page.wait_for_function("document.getElementById('players').textContent === '1034'")
        counts = {s: page.locator("#" + s).inner_text() for s in ("games", "appears", "players")}
        check(counts == {"games": "94", "appears": "1825", "players": "1034"},
              "All 94 games, 1,825 player lines and 1,034 players appear")
        check(page.locator("#rows tr").count() == 1034, "All traditional leaderboard rows load")
        check(page.evaluate("getComputedStyle(document.body).backgroundColor") == "rgb(250, 248, 242)",
              "NBA canonical ivory editorial theme matches exactly")
        page.screenshot(path=str(OUTPUT / "college-stats-desktop.png"))
        page.locator('[data-view="advanced"]').click()
        check(page.locator("#advancedPanel").is_visible(), "Advanced tab functions")
        page.locator('[data-view="per36"]').click()
        check(page.locator("#advancedPanel").is_visible(), "Per 36 tab functions")
        page.locator('[data-view="traditional"]').click()
        page.locator("#q").fill("Jase Townsend")
        check(page.locator("#rows tr").count() == 1, "Search isolates Townsend")
        check(page.locator('#rows [data-id]').first.get_attribute("data-id") ==
              "official:san-diego:jase-townsend", "Leaderboard uses canonical Townsend identity")
        check("170" in page.locator("#rows tr").first.inner_text(),
              "Townsend's attended-point total is 170")
        page.locator("#rows [data-id]").first.click()
        page.wait_for_url("**/college/player.html?id=*")
        page.wait_for_function("document.getElementById('name').textContent === 'Jase Townsend'")
        check("14 attended games" in page.locator("#seen").inner_text(),
              "Clicking Jase opens his 14-game profile via real URL navigation")
        page.screenshot(path=str(OUTPUT / "townsend-profile-desktop.png"), full_page=True)
        page.locator('[data-tab="games"]').click()
        check(page.locator("#gamelog tr").count() == 14,
              "All Townsend attended games appear in the chronological game log")
        check(page.locator("#schoolFilterWrap").is_hidden(),
              "Single-school player does not show school filter")
        check(page.locator("#gamelog a").first.get_attribute("href").startswith(
            "./game.html?id="),
            "Boxscore links open verified internal Courtside Archive game pages")

        page.goto(url + "player.html?id=espn%3A4433281", wait_until="domcontentloaded")
        page.wait_for_function("document.getElementById('name').textContent === 'Hunter Sallis'")
        check("4 attended games" in page.locator("#seen").inner_text(),
              "Hunter Sallis has one four-game transfer profile")
        page.locator('[data-tab="games"]').click()
        check(page.locator("#schoolFilterWrap").is_visible(), "Multi-school selector appears")
        options = page.locator("#schoolFilter option").all_text_contents()
        check("Gonzaga" in options and "Wake Forest" in options,
              "Both verified schools appear in dropdown")
        check(page.locator("#gamelog tr").count() == 4,
              "All-school option displays four games")
        for school, count in (("Gonzaga", 1), ("Wake Forest", 3)):
            value = page.locator("#schoolFilter option", has_text=school).get_attribute("value")
            page.locator("#schoolFilter").select_option(value)
            check(page.locator("#gamelog tr").count() == count,
                  f"{school} school filter displays {count} games")
        page.locator("#schoolFilter").select_option("all")
        page.screenshot(path=str(OUTPUT / "sallis-multi-school-gamelog.png"), full_page=True)

        mobile = browser.new_page(viewport={"width": 390, "height": 844}, device_scale_factor=1)
        record(mobile)
        mobile.goto(url + "stats.html", wait_until="domcontentloaded")
        mobile.wait_for_function("document.getElementById('players').textContent === '1034'")
        check(mobile.locator("#rows tr").count() == 1034,
              "Mobile-width leaderboard populates the entire roster")
        check(mobile.evaluate("document.documentElement.scrollWidth <= innerWidth + 2"),
              "Mobile player leaderboard has no document-level horizontal overflow")
        mobile.screenshot(path=str(OUTPUT / "college-stats-mobile.png"))
        check(not errors, "No unhandled browser JavaScript errors")
        browser.close()
        completed = True
finally:
    server.shutdown()
    report = {"checks_passed": len(checks), "checks": checks, "page_errors": errors,
              "status": "PASS" if completed and not errors else "FAIL",
              "environment": "Playwright Chromium over HTTP, checked-in validated college JSON"}
    (OUTPUT / "report.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2), flush=True)
