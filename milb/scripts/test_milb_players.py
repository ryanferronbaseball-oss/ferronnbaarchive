#!/usr/bin/env python3
"""Basic live-browser parity checks for MiLB's MLB-style player leaderboards."""
import functools
import http.server
import json
import pathlib
import socketserver
import threading
from playwright.sync_api import sync_playwright

ROOT=pathlib.Path(__file__).resolve().parents[2]
DATA=ROOT/"milb"/"data"
rows=json.loads((DATA/"player_stats.json").read_text(encoding="utf8"))
games=json.loads((DATA/"games.json").read_text(encoding="utf8"))
assert len(games)>=10 and len(rows)>=100
assert all("game_id" in x and "player_id" in x for x in rows)
assert all(x["game_id"] in {g["id"] for g in games} for x in rows)
assert any((x.get("batting") or {}).get("h",0)>0 for x in rows)
assert any((x.get("pitching") or {}).get("so",0)>0 for x in rows)
hitter=next(x["name"] for x in rows if (x.get("batting") or {}).get("h",0)>0)

handler=functools.partial(http.server.SimpleHTTPRequestHandler,directory=str(ROOT))
class ReuseServer(socketserver.ThreadingTCPServer):allow_reuse_address=True
server=ReuseServer(("127.0.0.1",0),handler)
thread=threading.Thread(target=server.serve_forever,daemon=True)
thread.start()
url=f"http://127.0.0.1:{server.server_address[1]}/milb/stats.html"
try:
 with sync_playwright() as p:
  browser=p.chromium.launch(headless=True)
  page=browser.new_page(viewport={"width":1360,"height":860})
  errors=[]
  observed=[]
  page.on("pageerror",lambda e:errors.append(str(e)))
  page.on("request",lambda r:observed.append(r.url))
  page.goto(url,wait_until="networkidle")
  assert page.locator("h1").inner_text()=="Players & leaderboards."
  assert page.locator("#category").count()==1
  assert page.locator("#stat").count()==1
  assert page.locator("#query").count()==1
  assert page.locator("#limit").count()==1
  assert page.locator(".metrics .metric").count()==4
  assert page.locator("#board table tbody tr").count()>0, "No batting rows"
  assert page.locator("#boardHeading").inner_text()=="Hits · Batting"
  assert page.locator("#board tbody tr a").first.get_attribute("href").startswith("./player.html?id=")
  page.locator("#query").fill(hitter)
  assert page.locator("#board tbody tr").count()>=1, f"Search failed for {hitter}"
  page.locator("#query").fill("")
  page.locator("#category").select_option("pitching")
  assert page.locator("#boardHeading").inner_text()=="Strikeouts · Pitching"
  assert page.locator("#board tbody tr").count()>0, "No pitcher rows"
  page.locator("#stat").select_option("inningsPitched")
  assert page.locator("#board tbody tr").count()>0, "Pitching innings table empty"
  page.locator("#limit").select_option("25")
  assert page.locator("#board tbody tr").count()<=25
  page.locator("#query").fill("unfindable-player-xyz")
  assert "No verified MiLB player statistics" in page.locator("#board").inner_text()
  assert not any("/mlb/data/" in url or "/college-baseball/data/" in url for url in observed), "Cross-sport data request found"
  assert not errors, "JS errors: "+repr(errors)
  browser.close()
 print("PASS: MiLB leaderboard matches MLB structure, filters & rankings; requests only MiLB datasets")
finally:
 server.shutdown()
 server.server_close()
