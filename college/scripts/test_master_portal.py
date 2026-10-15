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
    desktop.wait_for_function("document.getElementById('allGames').textContent === '125'")
    check(desktop.locator("#nbaGames").inner_text()=="31","Master reads 31 NBA game rows")
    check(desktop.locator("#collegeGames").inner_text()=="94","Master reads 94 separate college rows")
    check(desktop.locator("#allGames").inner_text()=="125","Master shows 125 combined game visits")
    check(desktop.get_by_role("link",name="Enter NBA archive").get_attribute("href")=="./nba/index.html",
          "Master routes NBA through a dedicated /nba/ path")
    check(desktop.get_by_role("link",name="Enter college archive").get_attribute("href")=="./college/index.html",
          "Master routes college through a dedicated /college/ path")
    check(desktop.locator(".sport-card").count()==2 and desktop.locator(".future").count()==1,
          "Two basketball archives are active; MLB stays future-only")
    desktop.screenshot(path=str(OUTPUT/"courtside-master-desktop.png"),full_page=True)

    desktop.get_by_role("link",name="Enter NBA archive").click()
    desktop.wait_for_url("**/nba/index.html")
    check("NBA" in desktop.title(),"NBA homepage remains an independent archive")
    check(desktop.locator(".ca-hub-link").get_attribute("href")=="../index.html",
          "NBA homepage returns to the master root")
    desktop.locator(".ca-hub-link").click()
    desktop.wait_for_url("**/index.html")
    check(desktop.locator("#allGames").inner_text()=="125","NBA-to-master return works")

    desktop.get_by_role("link",name="Enter college archive").click()
    desktop.wait_for_url("**/college/index.html")
    desktop.wait_for_function("document.getElementById('gameCount').textContent === '94'")
    check(desktop.locator(".ca-hub-link").get_attribute("href")=="../index.html",
          "College homepage returns to master root")
    desktop.locator(".ca-hub-link").click()
    desktop.wait_for_url("**/index.html")
    check(desktop.locator("#allGames").inner_text()=="125","College-to-master return works")

    for sport in ("nba","college"):
      for filename in PAGES:
        route=f"{sport}/{filename}"
        navigate(desktop,route)
        check(desktop.locator(".ca-hub-link").get_attribute("href")=="../index.html",
              route+" points back to root master")
        nav=desktop.locator(".ca-nav a[data-nav]").first.get_attribute("href")
        check(nav=="./index.html",route+" retains relative league-scoped navigation")
        check(desktop.evaluate("getComputedStyle(document.body).backgroundColor")=="rgb(250, 248, 242)",
              route+" preserves the canonical ivory NBA editorial theme")

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
      desktop.goto(base+oldroute,wait_until="domcontentloaded")
      print("LEGACY ROUTE CHECK",oldroute,"current",desktop.url,flush=True)
      check(desktop.url.endswith(newroute),"Legacy /"+oldroute+" redirects without losing query to /"+newroute)

    mobile=browser.new_page(viewport={"width":390,"height":844},device_scale_factor=1)
    setup(mobile)
    navigate(mobile,"index.html")
    mobile.wait_for_function("document.getElementById('allGames').textContent === '125'")
    check(mobile.evaluate("document.documentElement.scrollWidth <= innerWidth + 2"),
          "Master site does not overflow 390px viewport")
    check(mobile.get_by_role("link",name="Enter NBA archive").is_visible() and
          mobile.get_by_role("link",name="Enter college archive").is_visible(),
          "Both league entrances are visible on mobile")
    mobile.screenshot(path=str(OUTPUT/"courtside-master-mobile.png"),full_page=True)
    for route in ("nba/index.html","college/index.html"):
      navigate(mobile,route)
      mobile.wait_for_function("document.querySelector('.ca-hub-link') !== null")
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
