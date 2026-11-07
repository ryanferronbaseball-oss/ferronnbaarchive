#!/usr/bin/env python3
"""Verify MLB-design parity on MiLB player profiles without merging league data."""
import functools
import http.server
import json
import pathlib
import socketserver
import threading
from playwright.sync_api import sync_playwright

ROOT=pathlib.Path(__file__).resolve().parents[2]
ROWS=json.loads((ROOT/"milb/data/player_stats.json").read_text())
GAMES=json.loads((ROOT/"milb/data/games.json").read_text())
assert len(GAMES)>=10 and len(ROWS)>100
batter=next(r for r in ROWS if r.get("batting") and r["batting"].get("h",0)>0)
pitcher=next(r for r in ROWS if r.get("pitching") and r["pitching"].get("ip") not in (None,"0.0"))
class Server(socketserver.ThreadingTCPServer):allow_reuse_address=True
server=Server(("127.0.0.1",0),functools.partial(http.server.SimpleHTTPRequestHandler,directory=str(ROOT)))
thread=threading.Thread(target=server.serve_forever,daemon=True)
thread.start()
origin=f"http://127.0.0.1:{server.server_address[1]}"
try:
 with sync_playwright() as p:
  browser=p.chromium.launch(headless=True)
  for entry in [batter,pitcher]:
   page=browser.new_page(viewport={"width":1360,"height":900})
   errors=[]
   requests=[]
   page.on("pageerror",lambda err:errors.append(str(err)))
   page.on("request",lambda req:requests.append(req.url))
   page.goto(f"{origin}/milb/player.html?id={entry['player_id']}",wait_until="networkidle",timeout=45000)
   assert page.locator(".mlb-profile-identity h1").inner_text()==entry["name"]
   assert page.locator(".mlb-profile-hero .mlb-profile-photo").count()==1
   assert page.locator(".mlb-profile-headline-stats .mlb-profile-stat").count()==6
   assert [x.inner_text() for x in page.locator("#profileTabs .mlb-profile-tab").all()]==["Overview","Advanced","Game Log","Milestones"]
   assert page.locator("#profile-overview").is_visible()
   assert page.locator("#profile-advanced").is_hidden()
   assert "MiLB" in page.title()
   page.locator('[data-profile-tab="advanced"]').click()
   assert page.locator("#profile-advanced").is_visible()
   assert page.locator("#profile-overview").is_hidden()
   page.locator('[data-profile-tab="games"]').click()
   assert page.locator("#profile-games").is_visible()
   assert page.locator("#logs table tbody tr").count()>=1
   assert page.locator('#logs a[href^="./game.html?id="]').count()>0
   page.locator('[data-side="pitching"]').click()
   if entry.get("pitching"):
    assert page.locator("#logs table tbody tr").count()>=1
   else:
    assert "No verified pitching" in page.locator("#logs").inner_text()
   page.locator('[data-side="batting"]').click()
   if entry.get("batting"):
    assert page.locator("#logs table tbody tr").count()>=1
   else:
    assert "No verified batting" in page.locator("#logs").inner_text()
   page.locator('[data-profile-tab="milestones"]').click()
   assert page.locator("#profile-milestones").is_visible()
   assert page.locator("#profile-milestones .mlb-profile-total").count()==7
   assert not errors, f"JS errors for {entry['name']}: {errors}"
   assert not any("/mlb/data/" in req or "/college-baseball/data/" in req for req in requests), "Cross-league stats request found"
   page.close()
  mobile=browser.new_page(viewport={"width":390,"height":844},is_mobile=True,has_touch=True)
  mobile.goto(f"{origin}/milb/player.html?id={batter['player_id']}",wait_until="networkidle",timeout=45000)
  assert mobile.locator(".mlb-profile-identity h1").is_visible()
  assert mobile.locator(".mlb-profile-headline-stats .mlb-profile-stat").count()==6
  browser.close()
 print("PASS: MiLB profiles match MLB hero, six stat cards, four tabs, game logs, milestones and mobile behavior; only MiLB datasets loaded")
finally:
 server.shutdown()
 server.server_close()
