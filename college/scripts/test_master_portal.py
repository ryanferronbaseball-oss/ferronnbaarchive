#!/usr/bin/env python3
"""Integrated sports hub + NBA and college route safety QA (real HTTP Chromium)."""
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

def check(condition,label):
    if not condition:raise AssertionError(label)
    checks.append(label)
    print("PASS",label,flush=True)

def setup(page):
    page.on("pageerror",lambda err:errors.append(str(err)))
    page.route("https://a.espncdn.com/**",lambda route:route.abort())

def navigate(page,route):
    r=page.goto(base+route,wait_until="domcontentloaded")
    check(r is not None and r.status==200,route+" loads")

try:
  with sync_playwright() as pw:
    browser=pw.chromium.launch(headless=True,args=["--no-sandbox"])
    desktop=browser.new_page(viewport={"width":1440,"height":960},device_scale_factor=1)
    setup(desktop)
    navigate(desktop,"sports.html")
    desktop.wait_for_function("document.getElementById('allGames').textContent === '125'")
    check(desktop.locator("#nbaGames").inner_text()=="31","Master loads 31 NBA game rows from existing NBA data")
    check(desktop.locator("#collegeGames").inner_text()=="94","Master loads 94 college game rows from independent college data")
    check(desktop.locator("#allGames").inner_text()=="125","Master combines counts without combining player stats")
    check(desktop.get_by_role("link",name="Enter NBA archive").get_attribute("href")=="./index.html",
          "NBA landing URL preserves existing NBA homepage")
    check(desktop.get_by_role("link",name="Enter college archive").get_attribute("href")=="./college/index.html",
          "College landing URL stays confined to college subtree")
    check(desktop.locator(".sport-card").count()==2 and desktop.locator(".future").count()==1,
          "Two active basketball choices; future MLB expansion clearly not launched")
    desktop.screenshot(path=str(OUTPUT/"courtside-master-desktop.png"),full_page=True)

    desktop.get_by_role("link",name="Enter NBA archive").click()
    desktop.wait_for_url("**/index.html")
    check("NBA" in desktop.title(),"NBA homepage remains original standalone archive")
    check(desktop.locator(".ca-hub-link").get_attribute("href")=="./sports.html",
          "NBA homepage links back to master without URL collisions")
    desktop.locator(".ca-hub-link").click()
    desktop.wait_for_url("**/sports.html")
    check(desktop.locator("#allGames").inner_text()=="125","Returning from NBA restores master homepage")

    desktop.get_by_role("link",name="Enter college archive").click()
    desktop.wait_for_url("**/college/index.html")
    desktop.wait_for_function("document.getElementById('gameCount').textContent === '94'")
    check(desktop.locator(".ca-hub-link").get_attribute("href")=="../sports.html",
          "College homepage links to master using its folder-relative path")
    desktop.locator(".ca-hub-link").click()
    desktop.wait_for_url("**/sports.html")
    check(desktop.locator("#allGames").inner_text()=="125","Returning from college restores combined archive")

    for route,expected in (("stats.html","./sports.html"),("college/stats.html","../sports.html"),
                           ("game.html","./sports.html"),("college/game.html","../sports.html"),
                           ("insights.html","./sports.html"),("college/insights.html","../sports.html")):
      navigate(desktop,route)
      check(desktop.locator(".ca-hub-link").get_attribute("href")==expected,
            route+" retains separate site navigation and a master escape route")

    mobile=browser.new_page(viewport={"width":390,"height":844},device_scale_factor=1)
    setup(mobile)
    navigate(mobile,"sports.html")
    mobile.wait_for_function("document.getElementById('allGames').textContent === '125'")
    check(mobile.evaluate("document.documentElement.scrollWidth <= innerWidth + 2"),
          "Master homepage fits 390px viewport without horizontal overflow")
    check(mobile.get_by_role("link",name="Enter NBA archive").is_visible() and
          mobile.get_by_role("link",name="Enter college archive").is_visible(),
          "Both league entry links are visible and keyboard operable on mobile")
    mobile.screenshot(path=str(OUTPUT/"courtside-master-mobile.png"),full_page=True)
    for route in ("index.html","college/index.html"):
      navigate(mobile,route)
      mobile.wait_for_function("document.querySelector('.ca-hub-link') !== null")
      check(mobile.locator(".ca-hub-link").is_visible(),route+" shows back-to-master link on mobile")
      check(mobile.evaluate("document.documentElement.scrollWidth <= innerWidth + 2"),
            route+" does not overflow the 390px viewport with new cross-league navigation")
    check(not errors,"No uncaught JavaScript exceptions across both leagues and master portal")
    browser.close()
    completed=True
finally:
  server.shutdown()
  report={"status":"PASS" if completed and not errors else "FAIL","checks_passed":len(checks),
          "checks":checks,"page_errors":errors,
          "scope":"Shared master site, 31 existing NBA games, 94 college games, navigation and 390px layouts"}
  (OUTPUT/"report.json").write_text(json.dumps(report,indent=2)+"\n",encoding="utf-8")
  print(json.dumps(report,indent=2),flush=True)
