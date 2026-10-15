#!/usr/bin/env python3
import json,re,subprocess,tempfile,threading
from http.server import ThreadingHTTPServer,SimpleHTTPRequestHandler
from functools import partial
from pathlib import Path
from playwright.sync_api import sync_playwright
root=Path(__file__).resolve().parents[2]
games=json.loads((root/"nfl/data/games.json").read_text())
rows=json.loads((root/"nfl/data/player_stats.json").read_text())
report=json.loads((root/"nfl/data/import_report.json").read_text())
assert len(games)==3 and len(rows)>=250 and report["all_games_fully_imported"]
assert all(x["full_boxscore_imported"] for x in report["games"])
assert set(x["game_id"] for x in rows)==set(g["id"] for g in games)
assert all(len(x["stat_values"])==len(x["stat_labels"]) and x["player"] and x["athlete_id"] for x in rows)
for category in ("passing","rushing","receiving","defensive","interceptions","kicking","puntReturns","kickReturns","punting","fumbles"):
 assert any(x["category"]==category for x in rows),category
for path in ("index.html","nfl/index.html"):
 html=(root/path).read_text()
 for code in re.findall(r"<script>([\s\S]*?)</script>",html):
  with tempfile.NamedTemporaryFile(mode="w",suffix=".js") as f:
   f.write(code);f.flush();subprocess.run(["node","--check",f.name],check=True)
class Quiet(SimpleHTTPRequestHandler):
 def log_message(self,*args):pass
server=ThreadingHTTPServer(("127.0.0.1",0),partial(Quiet,directory=str(root)))
threading.Thread(target=server.serve_forever,daemon=True).start()
try:
 with sync_playwright() as pw:
  browser=pw.chromium.launch(headless=True,args=["--no-sandbox"])
  for width in (1280,390):
   page=browser.new_page(viewport={"width":width,"height":840})
   errors=[];page.on("pageerror",lambda error:errors.append(str(error)))
   page.goto(f"http://127.0.0.1:{server.server_address[1]}/nfl/index.html",wait_until="domcontentloaded")
   page.wait_for_function("document.getElementById('statCount').textContent === '253'")
   assert page.locator(".game").count()==3
   assert page.locator("#tbody tr").count()>0
   page.locator("#category").select_option("defensive")
   assert "Patrick Willis" in page.locator("#tbody").inner_text()
   page.locator("#search").fill("Warner")
   page.locator("#category").select_option("passing")
   assert "Kurt Warner" in page.locator("#tbody").inner_text()
   page.locator("#search").fill("")
   page.locator("#gameChoice").select_option("nfl-2023-12-03-ind-ten")
   assert "Gardner Minshew" in page.locator("#tbody").inner_text()
   assert page.evaluate("document.documentElement.scrollWidth<=innerWidth+2"),"Mobile overflow"
   assert not errors,errors
   page.goto(f"http://127.0.0.1:{server.server_address[1]}/index.html",wait_until="domcontentloaded")
   page.wait_for_function("document.getElementById('allGames').textContent === '128'")
   assert page.locator('a[href="./nfl/index.html"]').count()>=1
   assert not errors,errors
   page.close()
  browser.close()
finally:server.shutdown()
print("PASS: Three verified NFL games, 253 player statistical category rows, full browser leaderboard and mobile checks")
