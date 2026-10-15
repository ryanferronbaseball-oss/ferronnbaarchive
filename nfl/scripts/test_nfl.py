#!/usr/bin/env python3
"""Source/data identity, game chronology, leaderboards and desktop/mobile NFL page QA."""
import json,re,subprocess,tempfile,threading
from functools import partial
from http.server import ThreadingHTTPServer,SimpleHTTPRequestHandler
from pathlib import Path
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[2]
G=json.loads((ROOT/"nfl/data/games.json").read_text())
R=json.loads((ROOT/"nfl/data/player_stats.json").read_text())
S=json.loads((ROOT/"nfl/data/scoring_plays.json").read_text())
audit=json.loads((ROOT/"nfl/data/import_report.json").read_text())
checks=[]
def check(cond,label):
 assert cond,label
 checks.append(label)
 print("PASS",label,flush=True)
check(len(G)==3 and len(R)==253 and audit["all_games_fully_imported"],"Three complete historical game imports, 253 statistical category rows")
check(set(S)==set(g["id"] for g in G),"Every imported game has a scoring-play timeline")
check([len(S[g["id"]]["plays"]) for g in G]==[11,8,13],"Scoring play counts: 11, 8, 13")
for g in G:
 plays=S[g["id"]]["plays"]
 check(sum(p["points"] for p in plays)==g["away_score"]+g["home_score"],g["id"]+" scoring sum matches final score")
 check(plays[-1]["away_score"]==g["away_score"] and plays[-1]["home_score"]==g["home_score"],g["id"]+" scoring timeline ends at verified final score")
 check(all(p["description"] and p["clock"] and p["team"] for p in plays),g["id"]+" plays include original description and clock")
for name in ("nfl/assets/archive.js","nfl/index.html","nfl/game.html","nfl/stats.html","nfl/player.html"):
 txt=(ROOT/name).read_text()
 scripts=[txt] if name.endswith(".js") else re.findall(r"<script>([\s\S]*?)</script>",txt)
 for js in scripts:
  with tempfile.NamedTemporaryFile(mode="w",suffix=".js") as tmp:
   tmp.write(js);tmp.flush();p=subprocess.run(["node","--check",tmp.name],capture_output=True,text=True)
   check(p.returncode==0,name+" JavaScript syntax "+p.stderr[:100])
class Quiet(SimpleHTTPRequestHandler):
 def log_message(self,*args):pass
server=ThreadingHTTPServer(("127.0.0.1",0),partial(Quiet,directory=str(ROOT)))
threading.Thread(target=server.serve_forever,daemon=True).start()
base=f"http://127.0.0.1:{server.server_address[1]}/"
try:
 with sync_playwright() as pw:
  browser=pw.chromium.launch(headless=True,args=["--no-sandbox"])
  for width in (1280,390):
   page=browser.new_page(viewport={"width":width,"height":900})
   errors=[]
   page.on("pageerror",lambda e:errors.append(str(e)))
   def visit(url): 
    resp=page.goto(base+url,wait_until="domcontentloaded")
    check(resp.status==200,str(width)+" /"+url+" loads")
   def noOverflow(label):
    check(page.evaluate("document.documentElement.scrollWidth<=window.innerWidth+2"),str(width)+" "+label+" fits viewport")
   visit("nfl/index.html")
   page.wait_for_function("document.getElementById('scoringCount').textContent==='32'")
   check(page.locator(".game-card").count()==3,str(width)+" NFL overview lists all 3 games")
   check(page.locator("#statCount").inner_text()=="253",str(width)+" all ESPN player-category rows present")
   check("Kurt Warner" in page.locator("#leaders").inner_text(),str(width)+" historic passing leader visible")
   noOverflow("overview")
   visit("nfl/game.html?id=nfl-2023-12-03-ind-ten")
   page.wait_for_function("document.querySelectorAll('#scoring .play').length===13")
   check("M.Pittman" in page.locator("#scoring").inner_text(),str(width)+" detailed 2023 game-winning scoring description")
   check("Gardner Minshew" in page.locator("#boxscore").inner_text(),str(width)+" 2023 offense box score")
   page.get_by_role("tab",name="Defense").click()
   check("Tackles & Defense" in page.locator("#boxscore").inner_text(),str(width)+" grouped defensive box score")
   page.get_by_role("tab",name="Special Teams").click()
   check("Kicking" in page.locator("#boxscore").inner_text(),str(width)+" grouped kicking and returns box score")
   page.locator("#gameSelect").select_option("nfl-2007-11-25-sf-ari")
   page.wait_for_function("document.querySelectorAll('#scoring .play').length===11")
   check("Tully Banta-Cain" in page.locator("#scoring").inner_text(),str(width)+" 2007 overtime defensive walkoff appears")
   noOverflow("game detail")
   visit("nfl/stats.html")
   page.wait_for_function("document.querySelectorAll('#board tbody tr').length>=2")
   check("Kurt Warner" in page.locator("#board").inner_text(),str(width)+" cumulative passing leaderboard")
   page.get_by_role("tab",name="Defense").click()
   check("Patrick Willis" in page.locator("#board").inner_text(),str(width)+" defensive tackle leaderboard")
   page.get_by_role("tab",name="Special Teams").click()
   check("FG" in page.locator("#board").inner_text(),str(width)+" special teams leaderboard")
   page.get_by_role("tab",name="Offense").click()
   page.locator("#category").select_option("receiving")
   check("YDS" in page.locator("#board").inner_text(),str(width)+" selectable receiving leaders")
   page.locator("#search").fill("Fitzgerald")
   check("Larry Fitzgerald" in page.locator("#board").inner_text(),str(width)+" searchable individual player")
   noOverflow("leaderboard")
   visit("nfl/player.html?id=1682")
   page.wait_for_function("document.getElementById('playerName').textContent==='Kurt Warner'")
   check(page.locator("#games .game-card").count()==2,str(width)+" Warner has two attended Arizona games")
   check(page.locator("#careerStats table").count()>0,str(width)+" player cumulative categories link to personal game logs")
   noOverflow("player profile")
   visit("index.html")
   page.wait_for_function("document.getElementById('allGames').textContent==='128'")
   check(page.locator('a[href="./nfl/index.html"]').count()>=1,str(width)+" master portal links to NFL")
   noOverflow("master portal")
   check(not errors,str(width)+" no uncaught JavaScript errors")
   page.close()
  browser.close()
finally:
 server.shutdown()
print("PASS",len(checks),"source validations, browser behaviors and mobile tests",flush=True)
