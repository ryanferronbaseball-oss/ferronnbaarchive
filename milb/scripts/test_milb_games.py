#!/usr/bin/env python3
"""MiLB Games matches MLB viewer: selectable games, sides, lineups, profiles.
   Verify independent MiLB data and preserve detail.html backward-compatibility.
"""
import functools,http.server,json,pathlib,socketserver,threading
from playwright.sync_api import sync_playwright
ROOT=pathlib.Path(__file__).resolve().parents[2]
games=json.loads((ROOT/"milb/data/games.json").read_text())
rows=json.loads((ROOT/"milb/data/player_stats.json").read_text())
assert len(games)>=10 and len(rows)>=100
target=next(g for g in games if g["date"]=="2021-05-18")
other=next(g for g in games if g["date"]=="2014-05-24")
class Reuse(socketserver.ThreadingTCPServer):allow_reuse_address=True
server=Reuse(("127.0.0.1",0),functools.partial(http.server.SimpleHTTPRequestHandler,directory=str(ROOT)))
thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
origin=f"http://127.0.0.1:{server.server_address[1]}"
try:
 with sync_playwright() as p:
  browser=p.chromium.launch(headless=True)
  for route in ["/milb/game.html?id="+target["id"],"/milb/detail.html?id="+target["id"]]:
   page=browser.new_page(viewport={"width":1360,"height":900})
   errors=[];req=[]
   page.on("pageerror",lambda err:errors.append(str(err)))
   page.on("request",lambda request:req.append(request.url))
   page.goto(origin+route,wait_until="networkidle")
   assert page.locator("h1").inner_text()=="Game details."
   assert page.locator("#gameSelect option").count()==len(games)
   assert page.locator("#gameSelect").input_value()==target["id"]
   assert target["away_team"] in page.locator(".mlb-score .side").first.inner_text()
   assert target["home_team"] in page.locator(".mlb-score .side").last.inner_text()
   assert page.locator(".mlb-score .final").inner_text()==f'{target["away_score"]} – {target["home_score"]}'
   assert page.locator("#playerOfGame").count()==1
   assert page.locator("#playerOfGame a[href^='./player.html?id=']").count()>0
   assert page.locator("#pitchingDecisions [data-decision]").count()==3
   assert page.locator("#innings").count()==1
   assert page.locator("#gameStats #box .mlb-team-box").count()==2
   assert page.locator('#box .mlb-team-box[data-side="away"] h3').inner_text()==target["away_team"]
   assert page.locator('#box .mlb-team-box[data-side="home"] h3').inner_text()==target["home_team"]
   assert page.locator("#box .mlb-lineup-row").count()>=16
   assert page.locator('#box a[href^="./player.html?id="]').count()>=16
   assert [x.inner_text() for x in page.locator("#gameStats .mlb-nav-tabs button").all()]==["Batting","Pitching","Fielding"]
   page.locator('[data-cat="pitching"]').click()
   assert page.locator("#statTitle").inner_text()=="Pitching box score"
   assert page.locator('#box [data-category="pitching"]').count()==2
   assert page.locator("#box .mlb-lineup-row").count()>=4
   assert "IP" in page.locator("#box table thead").first.inner_text()
   page.locator('[data-cat="fielding"]').click()
   assert page.locator("#statTitle").inner_text()=="Fielding box score"
   assert page.locator('#box [data-category="fielding"]').count()==2
   assert "PO" in page.locator("#box table thead").first.inner_text()
   page.locator('[data-cat="batting"]').click()
   assert page.locator("#statTitle").inner_text()=="Batting box score"
   page.locator("#gameSelect").select_option(other["id"])
   assert other["away_team"] in page.locator(".mlb-score .side").first.inner_text()
   assert page.locator("#gameSelect").input_value()==other["id"]
   assert "game.html?id="+other["id"] in page.url
   assert page.locator("#box .mlb-lineup-row").count()>=16
   assert page.locator("#scoringSection").count()==1
   assert not any("/mlb/data/" in url or "/college-baseball/data/" in url for url in req)
   assert not errors,errors
   page.close()
  mobile=browser.new_page(viewport={"width":390,"height":844},is_mobile=True,has_touch=True)
  mobile.goto(origin+"/milb/game.html?id="+other["id"],wait_until="networkidle")
  assert mobile.locator("#gameSelect").is_visible()
  assert mobile.locator(".mlb-score .side").count()==2
  assert mobile.locator("#box .mlb-team-box").count()==2
  browser.close()
 print("PASS: MiLB games show MLB-style scoreboard, both team boxes, tabs, player links, old URLs, selectors and independent datasets")
finally:
 server.shutdown();server.server_close()
