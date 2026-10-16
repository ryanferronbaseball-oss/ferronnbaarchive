#!/usr/bin/env python3
"""Live-HTTP test of canonical master /, /nba/ and /college/, plus legacy NBA links."""
import json
import threading
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from playwright.sync_api import sync_playwright

ROOT=Path(__file__).resolve().parents[2]
OUTPUT=ROOT/"college/output/master-portal"
OUTPUT.mkdir(parents=True,exist_ok=True)

class Silent(SimpleHTTPRequestHandler):
    def log_message(self,*_):pass

server=ThreadingHTTPServer(("127.0.0.1",0),partial(Silent,directory=str(ROOT)))
threading.Thread(target=server.serve_forever,daemon=True).start()
base=f"http://127.0.0.1:{server.server_address[1]}/"
checks=[]
errors=[]
completed=False
PAGES=("index.html","game.html","stats.html","player.html",
       "records.html","milestones.html","insights.html")

def check(ok,label):
    if not ok:raise AssertionError(label)
    checks.append(label)
    print("PASS",label,flush=True)

def setup(page):
    page.on("pageerror",lambda err:errors.append(str(err)))
    page.route("https://a.espncdn.com/**",lambda route:route.abort())

def navigate(page,route):
    r=page.goto(base+route,wait_until="domcontentloaded")
    check(r is not None and r.status==200,route+" loads over HTTP")

try:
  with sync_playwright() as pw:
    browser=pw.chromium.launch(headless=True,args=["--no-sandbox"])
    desktop=browser.new_page(viewport={"width":1440,"height":960},device_scale_factor=1)
    setup(desktop)
    navigate(desktop,"index.html")
    desktop.wait_for_function("document.getElementById('allGames').textContent === '128'")
    check(desktop.locator("#nbaGames").inner_text()=="31","Master reads 31 NBA game rows")
    check(desktop.locator("#collegeGames").inner_text()=="94","Master reads 94 separate college rows")
    check(desktop.locator("#allGames").inner_text()=="128","Master shows 128 combined game visits")
    check(desktop.get_by_role("link",name="Enter NBA archive").get_attribute("href")=="./nba/index.html",
          "Master routes NBA through a dedicated /nba/ path")
    check(desktop.get_by_role("link",name="Enter college archive").get_attribute("href")=="./college/index.html",
          "Master routes college through a dedicated /college/ path")
    check(desktop.locator(".sport-card").count()==3 and desktop.locator(".future").count()==1,
          "Three sports archives are active; MLB stays future-only")
    check(desktop.get_by_role("link",name="Enter NFL archive").get_attribute("href")=="./nfl/index.html","Master routes NFL through its dedicated /nfl/ path")
    desktop.screenshot(path=str(OUTPUT/"courtside-master-desktop.png"),full_page=True)

    desktop.get_by_role("link",name="Enter NBA archive").click()
    desktop.wait_for_url("**/nba/index.html")
    check("NBA" in desktop.title(),"NBA homepage remains an independent archive")
    check(desktop.locator(".ca-hub-link").get_attribute("href")=="../index.html",
          "NBA homepage returns to the master root")
    desktop.locator(".ca-hub-link").click()
    desktop.wait_for_url("**/index.html")
    check(desktop.locator("#allGames").inner_text()=="128","NBA-to-master return works")

    desktop.get_by_role("link",name="Enter college archive").click()
    desktop.wait_for_url("**/college/index.html")
    desktop.wait_for_function("document.getElementById('gameCount').textContent === '94'")
    check(desktop.locator(".ca-hub-link").get_attribute("href")=="../index.html",
          "College homepage returns to master root")
    desktop.locator(".ca-hub-link").click()
    desktop.wait_for_url("**/index.html")
    check(desktop.locator("#allGames").inner_text()=="128","College-to-master return works")

    for sport in ("nba","college"):
      for filename in PAGES:
        route=f"{sport}/{filename}"
        navigate(desktop,route)
        check(desktop.locator(".ca-hub-link").get_attribute("href")=="../index.html",
              route+" points back to root master")
        check(desktop.locator(".ca-header .ca-logo").inner_text()==
              "COURTSIDE ARCHIVE\nEVERY GAME HAS A STORY · "+("NBA" if sport=="nba" else "COLLEGE BASKETBALL"),
              route+" uses NFL-style text logo and sport-specific tagline")
        check(desktop.locator(".ca-header .ca-mark, .ca-header svg").count()==0,
              route+" has no masthead icon")
        check(desktop.evaluate("""() => {
          const css=getComputedStyle(document.querySelector('.ca-header .ca-hub-link'));
          return css.borderTopStyle==='none' && css.paddingLeft==='0px' &&
            css.paddingRight==='0px' && css.backgroundColor==='rgba(0, 0, 0, 0)';
        }"""),route+" has an unboxed All archives link")
        check(desktop.evaluate("""() => getComputedStyle(document.querySelector('.ca-header .ca-logo')).fontSize""")=="17px",
              route+" logo font matches NFL")
        nav=desktop.locator(".ca-nav a[data-nav]").first.get_attribute("href")
        check(nav=="./index.html",route+" retains relative league-scoped navigation")
        check(desktop.evaluate("getComputedStyle(document.body).backgroundColor")=="rgb(250, 248, 242)",
              route+" preserves the canonical ivory NBA editorial theme")

    # Standalone basketball directories share the same masthead, too.
    for sport,filename in (("nba","hall-of-fame.html"),("college","nba-alumni.html")):
      route=f"{sport}/{filename}"
      navigate(desktop,route)
      check(desktop.locator(".ca-header .ca-mark, .ca-header svg").count()==0 and
            desktop.locator(".ca-logo-text small").inner_text().endswith("NBA" if sport=="nba" else "COLLEGE BASKETBALL"),
            route+" uses the common logo-free header")
      check(desktop.locator(".ca-header .ca-hub-link").get_attribute("href")=="../index.html",
            route+" retains All archives navigation")

    # Basketball impact leaderboard mirrors each game's Player of the Game calculation.
    for sport,game_id in (("nba","1"),("college","59")):
      navigate(desktop,f"{sport}/game.html?id={game_id}")
      desktop.wait_for_function("document.querySelectorAll('.impact-board tbody tr').length === 5")
      box_heading=desktop.locator("#game .boxscore-section-heading h2")
      check(box_heading.count()==1 and box_heading.inner_text()=="Player box score",
            sport+" game labels both teams' box scores")
      check(desktop.evaluate("""() => {
        const heading=document.querySelector("#game .boxscore-section-heading");
        const prev=heading.previousElementSibling;
        const first=heading.nextElementSibling;
        const second=first?.nextElementSibling;
        return !!prev?.querySelector(".impact-board") && !!first?.querySelector("table") &&
               !!second?.querySelector("table") && heading.querySelector("h2")?.textContent==="Player box score";
      }"""),sport+" box-score heading appears between top-five rankings and team tables")
      board=desktop.locator(".impact-board")
      check(board.locator("thead th").all_text_contents()==
            ["Player","Impact score","PTS","REB","AST","STL","BLK"],
            sport+" game impact leaderboard has all seven requested columns")
      check(board.locator("tbody tr").count()==5,
            sport+" game ranks exactly five players by impact")
      scores=[int(x) for x in board.locator("tbody tr .impact-number strong").all_text_contents()]
      check(scores==sorted(scores,reverse=True),sport+" impact rankings are descending")
      check(scores[0]==int(desktop.locator(".pog-impact strong").inner_text()),
            sport+" top impact score agrees with Player of the Game")
      check(board.locator("tbody tr .impact-player small").count()==5 and
            board.locator("tbody tr .impact-player a").count()==5,
            sport+" game shows five linked player names and team labels")

    # Previously bookmarked NBA detail and leaderboard links must keep deep link queries.
    for oldroute,newroute in (
      ("game.html?id=1","nba/game.html?id=1"),
      ("player.html?id=espn%3A12345","nba/player.html?id=espn%3A12345"),
      ("stats.html?player=LeBron","nba/stats.html?player=LeBron"),
      ("milestones.html","nba/milestones.html"),
      ("insights.html","nba/insights.html"),
      ("records.html","nba/records.html"),
      ("sports.html","index.html")
    ):
      legacy=browser.new_page(viewport={"width":1280,"height":900})
      setup(legacy)
      legacy.goto(base+oldroute,wait_until="domcontentloaded")
      print("LEGACY ROUTE CHECK",oldroute,"current",legacy.url,flush=True)
      check(legacy.url.endswith(newroute),"Legacy /"+oldroute+" redirects without losing query to /"+newroute)
      legacy.close()

    mobile=browser.new_page(viewport={"width":390,"height":844},device_scale_factor=1)
    setup(mobile)
    navigate(mobile,"index.html")
    mobile.wait_for_function("document.getElementById('allGames').textContent === '128'")
    check(mobile.evaluate("document.documentElement.scrollWidth <= innerWidth + 2"),
          "Master site does not overflow 390px viewport")
    check(mobile.get_by_role("link",name="Enter NBA archive").is_visible() and
          mobile.get_by_role("link",name="Enter college archive").is_visible() and
          mobile.get_by_role("link",name="Enter NFL archive").is_visible(),
          "All three sport entrances are visible on mobile")
    mobile.screenshot(path=str(OUTPUT/"courtside-master-mobile.png"),full_page=True)
    for route in ("nba/index.html","college/index.html"):
      navigate(mobile,route)
      mobile.wait_for_function("document.querySelector('.ca-hub-link') !== null")
      check(mobile.locator(".ca-header .ca-logo-text small").is_visible() and
            mobile.locator(".ca-header .ca-mark").count()==0,
            route+" mobile header shows its sport with no icon")
      check(mobile.locator(".ca-hub-link").is_visible(),
            route+" shows the return-to-master link")
      check(mobile.evaluate("document.documentElement.scrollWidth <= innerWidth + 2"),
            route+" retains mobile viewport layout")
    check(not errors,"No unhandled JavaScript errors across master/NBA/college migration")
    browser.close()
    completed=True
finally:
  server.shutdown()
  report={"status":"PASS" if completed and not errors else "FAIL",
          "checks_passed":len(checks),"checks":checks,"page_errors":errors,
          "scope":"Canonical / master, dedicated /nba/ and /college/, NBA legacy deep-link redirects"}
  (OUTPUT/"report.json").write_text(json.dumps(report,indent=2)+"\n",encoding="utf-8")
  print(json.dumps(report,indent=2),flush=True)
