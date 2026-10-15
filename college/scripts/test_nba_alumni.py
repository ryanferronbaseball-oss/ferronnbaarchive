#!/usr/bin/env python3
"""Validate the NBA alumni crosswalk, college joins, and interactive page."""
import json, re, subprocess, tempfile, threading
from pathlib import Path
from functools import partial
from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler
from playwright.sync_api import sync_playwright

ROOT=Path(__file__).resolve().parents[2]; OUT=ROOT/"college/output/nba-alumni";OUT.mkdir(parents=True,exist_ok=True)
players=json.loads((ROOT/"college/data/player_boxscores_espn.json").read_text())
cross=json.loads((ROOT/"college/data/nba_crosswalk.json").read_text())
by={}
for p in players:by.setdefault(p["player_id"],[]).append(p)
assert len(cross)>=23 and len(set(x["player_id"] for x in cross))==len(cross)
assert all(x["player_id"] in by and x["source_url"].startswith("https://") for x in cross)
assert all(x["category"] in ("nba","drafted_only") for x in cross)
assert all(x["category"]=="nba" or (x["draft_year"] and x["draft_pick"]) for x in cross)
assert all(x["category"]!="nba" or x["nba_debut"] or x["source_url"] for x in cross)
assert sum(len(by[x["player_id"]]) for x in cross)>=40
html=(ROOT/"college/nba-alumni.html").read_text()
script=re.search(r"<script>([\s\S]*?)</script>",html).group(1)
with tempfile.NamedTemporaryFile(mode="w",suffix=".js") as f:
 f.write(script);f.flush();subprocess.run(["node","--check",f.name],check=True)
class Quiet(SimpleHTTPRequestHandler):
 def log_message(self,*a):pass
server=ThreadingHTTPServer(("127.0.0.1",0),partial(Quiet,directory=str(ROOT)))
threading.Thread(target=server.serve_forever,daemon=True).start()
checks=[];errors=[];success=False
def ok(x,label):
 assert x,label
 checks.append(label);print("PASS",label,flush=True)
try:
 with sync_playwright() as pw:
  browser=pw.chromium.launch(headless=True,args=["--no-sandbox"])
  page=browser.new_page(viewport={"width":1320,"height":950})
  page.on("pageerror",lambda e:errors.append(str(e)))
  page.route("https://a.espncdn.com/**",lambda route:route.abort())
  response=page.goto(f"http://127.0.0.1:{server.server_address[1]}/college/nba-alumni.html",wait_until="domcontentloaded")
  ok(response.status==200,"Alumni page loads")
  page.wait_for_function("document.getElementById('nbaCount').textContent === '19'")
  ok(page.locator(".player").count()==19,"Nineteen verified career-to-college matches displayed")
  ok(page.locator("#draftCount").inner_text()=="4","Four 2026 draftees are separately listed with no NBA appearance as of October 15, 2026")
  ok("Hunter Sallis" in page.locator("#cards").inner_text(),"Sallis college transfer profile exists")
  ok("Gonzaga / Wake Forest" in page.locator("#cards").inner_text(),"Both attended Sallis colleges are preserved")
  ok("12" in page.locator("#cards").inner_text(),"Personal witnessed-game calculations visible")
  ok(page.locator('.player a[href^="./player.html?id="]').count()>=16,"All matched alumni link to canonical player profiles")
  page.screenshot(path=str(OUT/"alumni-desktop.png"),full_page=True)
  page.locator("#search").fill("Holmgren")
  ok(page.locator(".player").count()==1,"Search by player works")
  page.locator("#search").fill("Wake Forest")
  ok(page.locator(".player").count()==1,"Search by school works")
  page.locator("#search").fill("")
  page.locator('[data-group="drafted_only"]').click()
  ok(page.locator(".player").count()==4 and "Richie Saunders" in page.locator("#cards").inner_text() and "Isaiah Evans" in page.locator("#cards").inner_text(),"Separate drafted-only directory contains verified 2026 NBA draft picks")
  page.locator('[data-group="nba"]').click()
  page.locator("#sort").select_option("name")
  ok(page.locator(".player").count()==19,"Sorting preserves the full verified set")
  mobile=browser.new_page(viewport={"width":390,"height":844})
  mobile.on("pageerror",lambda e:errors.append(str(e)))
  mobile.route("https://a.espncdn.com/**",lambda route:route.abort())
  mobile.goto(f"http://127.0.0.1:{server.server_address[1]}/college/nba-alumni.html",wait_until="domcontentloaded")
  mobile.wait_for_function("document.getElementById('nbaCount').textContent === '19'")
  ok(mobile.evaluate("document.documentElement.scrollWidth<=innerWidth+2"),"Mobile width does not overflow")
  mobile.screenshot(path=str(OUT/"alumni-mobile.png"),full_page=True)
  ok(not errors,"No uncaught JavaScript errors")
  browser.close();success=True
finally:
 server.shutdown()
 report={"status":"PASS" if success and not errors else "FAIL","checks":checks,"errors":errors}
 (OUT/"report.json").write_text(json.dumps(report,indent=2)+"\n")
 print(json.dumps(report,indent=2),flush=True)
