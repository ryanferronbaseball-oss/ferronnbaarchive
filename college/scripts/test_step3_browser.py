#!/usr/bin/env python3
"""Real HTTP/Chromium end-to-end regressions for all seven NCAA archive pages."""
import json
import threading
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from playwright.sync_api import sync_playwright

ROOT=Path(__file__).resolve().parents[2]
OUTPUT=ROOT/"college/output/step3-browser"
OUTPUT.mkdir(parents=True,exist_ok=True)

class Silent(SimpleHTTPRequestHandler):
    def log_message(self,*_):pass

server=ThreadingHTTPServer(("127.0.0.1",0),partial(Silent,directory=str(ROOT)))
threading.Thread(target=server.serve_forever,daemon=True).start()
url=f"http://127.0.0.1:{server.server_address[1]}/college/"
checks=[]
errors=[]

def check(ok,label):
    if not ok:raise AssertionError(label)
    checks.append(label)
    print("PASS",label,flush=True)

def setup(page):
    page.on("pageerror",lambda err:errors.append(str(err)))
    page.route("https://a.espncdn.com/**",lambda route:route.abort())

def navigate(page,path):
    resp=page.goto(url+path,wait_until="domcontentloaded")
    check(resp is not None and resp.status==200,path+" loads over real HTTP")

try:
  with sync_playwright() as pw:
    browser=pw.chromium.launch(headless=True,args=["--no-sandbox"])
    page=browser.new_page(viewport={"width":1440,"height":1024},device_scale_factor=1)
    setup(page)
    navigate(page,"index.html")
    page.wait_for_function("document.getElementById('gameCount').textContent === '94'")
    check(page.locator("#games tr").count()==94,"Homepage lists all 94 NCAA attendance games")
    check(page.locator("#teamCount").inner_text()=="75","Homepage counts 75 distinct school teams")
    check(page.locator("#boxCoverage").inner_text()=="94/94","Homepage reports 94 fully imported box scores")
    check(page.locator("#features .ca-feature").count()==3,"Homepage generates three verified signature performances")
    check("Not yet verified" in page.locator("#games").inner_text(),
          "Homepage does not invent missing arena names")
    page.screenshot(path=str(OUTPUT/"college-home-desktop.png"),full_page=True)
    page.locator("#yearFilter").select_option("2022")
    check(0<page.locator("#games tr").count()<94,"Homepage filters by year")
    page.locator("#yearFilter").select_option("")
    page.locator("#search").fill("Utah State")
    check(0<page.locator("#games tr").count()<94,"Homepage searches actual matchups")
    page.locator("#search").fill("")

    navigate(page,"game.html?id=59")
    page.wait_for_function("document.querySelectorAll('#game .score').length === 2")
    check(page.locator("#game .score").all_text_contents()==["91","89"],
          "Overtime Utah State at San Diego final score matches 91–89")
    check(page.locator("#game .team").count()==2,"Both NCAA opponent labels render")
    check(page.locator("#game .player-link").count()>15,"Complete NCAA player tables load")
    check("Jenny Craig Pavilion" in page.locator("#game").inner_text(),
          "Game page renders official WCC-sourced 2022 San Diego arena")
    check(page.locator("#gameSelect option").count()==94,"All 94 games are selectable")
    check("mens-college-basketball" in page.locator("#game a[target='_blank']").first.get_attribute("href"),
          "Game's outbound boxscore link uses the NCAA endpoint")
    page.screenshot(path=str(OUTPUT/"college-game-details.png"),full_page=True)
    page.get_by_role("link",name="Jase Townsend").first.click()
    page.wait_for_url("**/college/player.html?id=*")
    page.wait_for_function("document.getElementById('name').textContent === 'Jase Townsend'")
    check("14 attended games" in page.locator("#seen").inner_text(),
          "Game boxscore player link opens Townsend's unified 14-game profile")

    navigate(page,"game.html?id=25")
    page.wait_for_function("document.querySelectorAll('#game .score').length === 2")
    check("Venue not yet verified" in page.locator("#game").inner_text(),
          "An unverified arena remains visibly unknown, not inferred from a home school")
    navigate(page,"game.html?id=82")
    page.wait_for_function("document.querySelectorAll('#game .score').length === 2")
    check("First Horizon Coliseum" in page.locator("#game").inner_text(),
          "Specific sourced neutral-site arena displayed on game page")
    check("Neutral site" in page.locator("#game").inner_text(),
          "Neutral venue badge differentiates designated home from true home")
    navigate(page,"records.html")
    page.wait_for_function("document.querySelectorAll('#cards .card').length === 6")
    check(page.locator("#cards .card").count()==6,
          "Six original single-game records cards render from NCAA data")
    check(page.locator("#table tr").count()>0,
          "Single-game leaderboards populate with real performances")
    page.locator("#search").fill("Jase Townsend")
    check(page.locator("#table tr").count()>0 and
          "Jase Townsend" in page.locator("#table").inner_text(),
          "Record search finds officially supplemented NCAA players")
    page.screenshot(path=str(OUTPUT/"college-single-game-records.png"),full_page=True)

    navigate(page,"milestones.html")
    page.wait_for_function("document.getElementById('coverage').textContent.includes('94 games attended')")
    check(page.locator("#recordCards .record").count()==6,
          "Original six milestone record cards load")
    check(page.locator("#teamGames tr").count()==94,
          "Milestones include exactly 94 distinct NCAA game results")
    page.locator('[data-tab="milestones"]').click()
    check(page.locator("#milestonesTab").is_visible(),"Statistical milestone tab works")
    page.locator("#milestone").select_option(index=1)
    check(page.locator("#milestoneCount").inner_text().isdigit(),"Milestone filter updates counts")
    page.locator('[data-tab="teams"]').click()
    check(page.locator("#teamsTab").is_visible(),"Team record tab works")
    page.locator('[data-tab="legendary"]').click()
    check(page.locator("#legendaryTab").is_visible(),"Legendary performance tab works")
    page.screenshot(path=str(OUTPUT/"college-milestones.png"),full_page=True)

    navigate(page,"insights.html")
    page.wait_for_function("document.querySelectorAll('#metrics .tile').length === 8")
    check(page.locator("#metrics .tile").count()==8,"Attendance insights original KPI grid loads")
    check(page.locator("#teamTable tr").count()==75,"Team records include all 75 witnessed schools")
    check("94" in page.locator("#metrics").inner_text(),"Attendance dashboard includes 94 attended games")
    check("Lenovo Center" in page.locator("#arenaTable").inner_text(),
          "Arena rankings combine PNC and Lenovo naming-rights eras")
    check("34 games" in page.locator("#arenaBars").inner_text(),
          "Venue warning correctly excludes 34 still-unverified locations")
    check(any("Verified arenas" in tile.inner_text() and "14" in tile.inner_text()
              for tile in page.locator("#metrics .tile").all()),
          "14 distinct physical arenas counted from 15 dated names")

    page.locator("#period").select_option("calendar")
    check(page.locator("#timeline .timeline-item").count()>1,
          "Timeline switches from college seasons to calendar years")
    page.locator("#teamSort").select_option("wpct")
    check(page.locator("#teamTable tr").count()==75,"Team records sorting works")
    page.locator("#experienceFilter").select_option("high")
    check(page.locator("#experienceRows tr").count()>0,"College 170+ combined points filter works")
    check(page.locator("#playerTable tr").count()>0,"Most-watched college player profiles load")
    page.screenshot(path=str(OUTPUT/"college-attendance-insights.png"),full_page=True)

    mobile=browser.new_page(viewport={"width":390,"height":844},device_scale_factor=1)
    setup(mobile)
    navigate(mobile,"index.html")
    mobile.wait_for_function("document.getElementById('gameCount').textContent === '94'")
    check(mobile.locator("#games tr").count()==94,"College homepage renders all attendance rows on mobile")
    mobile.screenshot(path=str(OUTPUT/"college-home-mobile.png"))
    navigate(mobile,"insights.html")
    mobile.wait_for_function("document.querySelectorAll('#metrics .tile').length===8")
    check(mobile.locator("#teamTable tr").count()==75,"NCAA insights works on mobile")
    mobile.screenshot(path=str(OUTPUT/"college-insights-mobile.png"))
    check(not errors,"No unhandled JavaScript errors in seven-page navigation")
    browser.close()
finally:
  server.shutdown()
  report={"status":"PASS" if not errors else "ERROR","passed_checks":len(checks),
          "checks":checks,"page_errors":errors,
          "environment":"Playwright Chromium, real HTTP, checked-in NCAA data and original NBA shared assets"}
  (OUTPUT/"report.json").write_text(json.dumps(report,indent=2)+"\n",encoding="utf8")
  print(json.dumps(report,indent=2),flush=True)
