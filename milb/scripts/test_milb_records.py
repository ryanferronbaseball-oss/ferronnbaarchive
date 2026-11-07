#!/usr/bin/env python3
"""Verify MiLB Records MLB-style tabs, accurate ranking and separate statistics."""
import functools,http.server,json,pathlib,socketserver,threading
from playwright.sync_api import sync_playwright
ROOT=pathlib.Path(__file__).resolve().parents[2]
games=json.loads((ROOT/"milb/data/games.json").read_text())
rows=json.loads((ROOT/"milb/data/player_stats.json").read_text())
innings=json.loads((ROOT/"milb/data/inning_scores.json").read_text())
assert len(games)>=10 and len(rows)>=100
assert all(g.get("source_game_id") is not None for g in games)
most_hits=max(int(r["batting"]["h"]) for r in rows if r.get("batting") and r["batting"].get("h") is not None)
most_so=max(int(r["pitching"]["so"]) for r in rows if r.get("pitching") and r["pitching"].get("so") is not None)
qualifying=sum((r.get("batting") or {}).get("h",0)>=3 for r in rows)
extra=sum(any(int(i["inning"])>9 for i in innings.get(str(g["source_game_id"]),[])) for g in games)
class Reuse(socketserver.ThreadingTCPServer):allow_reuse_address=True
server=Reuse(("127.0.0.1",0),functools.partial(http.server.SimpleHTTPRequestHandler,directory=str(ROOT)))
t=threading.Thread(target=server.serve_forever,daemon=True);t.start()
origin=f"http://127.0.0.1:{server.server_address[1]}"
try:
 with sync_playwright() as p:
  browser=p.chromium.launch(headless=True)
  page=browser.new_page(viewport={"width":1360,"height":860})
  errors=[];urls=[]
  page.on("pageerror",lambda e:errors.append(str(e)))
  page.on("request",lambda r:urls.append(r.url))
  page.goto(origin+"/milb/records.html",wait_until="networkidle",timeout=45000)
  assert page.locator("h1").inner_text()=="The best I've witnessed."
  assert page.locator('#mainTabs button').count()==4
  assert [x.inner_text() for x in page.locator("#mainTabs button").all()]==["Record Book","Milestones","Team & Game Records","Legendary Performances"]
  assert page.locator("#recordsTab").is_visible()
  assert page.locator("#milestonesTab").is_hidden()
  assert page.locator("#recordCards .mlb-record").count()==6
  assert str(most_hits)==page.locator("#recordCards .mlb-record").first.locator("strong").inner_text()
  assert page.locator("#recordTop tbody tr").count()<=10
  assert page.locator("#recordTop tbody tr").count()>0
  assert page.locator('#recordTop a[href^="./player.html?id="]').count()>0
  assert page.locator('#recordTop a[href^="./game.html?id="]').count()>0
  page.locator("#recordCategory").select_option("pitching:so")
  assert str(most_so)==page.locator("#recordTop tbody tr").first.locator("strong").inner_text()
  page.locator('[data-tab="milestones"]').click()
  assert page.locator("#milestonesTab").is_visible()
  assert page.locator("#recordsTab").is_hidden()
  numbers=[int(x.replace(",","")) for x in page.locator("#milestoneMetrics .metric strong").all_inner_texts()]
  assert numbers[0]==qualifying,(numbers[0],qualifying)
  assert numbers[3]==len(games)
  page.locator("#milestoneView").select_option("players")
  assert "Times reached" in page.locator("#milestoneTable").inner_text()
  page.locator("#milestoneStat").select_option("pitching:outs:21")
  assert page.locator("#milestoneMetrics .metric").count()==4
  page.locator('[data-tab="teams"]').click()
  assert page.locator("#teamsTab").is_visible()
  assert page.locator("#teamCards .mlb-record").count()==6
  assert str(extra)==page.locator("#teamCards .mlb-record").nth(2).locator("strong").inner_text()
  assert page.locator("#teamGameTable tbody tr").count()==len(games)
  assert page.locator('#teamGameTable a[href^="./game.html?id="]').count()==len(games)*2
  page.locator('[data-tab="legendary"]').click()
  assert page.locator("#legendaryTab").is_visible()
  assert page.locator("#moments tbody tr").count()==len(games)
  assert page.locator('#moments a[href^="./game.html?id="]').count()==len(games)
  assert not any("/mlb/data/" in u or "/college-baseball/data/" in u for u in urls),urls
  assert not errors,errors
  mobile=browser.new_page(viewport={"width":390,"height":844},is_mobile=True,has_touch=True)
  mobile.goto(origin+"/milb/records.html",wait_until="networkidle")
  assert mobile.locator("h1").is_visible()
  assert mobile.locator("#mainTabs button").count()==4
  mobile.locator('[data-tab="milestones"]').click()
  assert mobile.locator("#milestoneMetrics .metric").count()==4
  browser.close()
 print("PASS: MiLB Records MLB design, record holders, milestone totals, team history, feats, mobile and league separation")
finally:server.shutdown();server.server_close()
