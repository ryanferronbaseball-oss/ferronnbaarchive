#!/usr/bin/env python3
"""CFB archive data integrity + desktop/mobile parity with NFL."""
import json,re,subprocess,tempfile,threading
from functools import partial
from http.server import SimpleHTTPRequestHandler,ThreadingHTTPServer
from pathlib import Path
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[2]
D=ROOT/"cfb/data"
games=json.loads((D/"games.json").read_text())
rows=json.loads((D/"player_stats.json").read_text())
scores=json.loads((D/"scoring_plays.json").read_text())
fantasy=json.loads((D/"fantasy_ppr.json").read_text())["performances"]
report=json.loads((D/"import_report.json").read_text())
def check(x,label):
 assert x,label
 print("PASS",label,flush=True)
check(len(games)==5,"Five attended college football games kept intact")
check(len(rows)>=300,"Official gamebooks imported at least 300 player-category rows")
check(all(x["game_id"] in {g["id"] for g in games} for x in rows),"All players belong to an attended game")
check(all(x["game_id"] in {g["id"] for g in games} for x in fantasy),"All fantasy scores originate from attended games")
check(all(g["id"] in scores for g in games),"All five games have scoring timelines")
for g in games:
 p=scores[g["id"]]["plays"]
 check(bool(p) and p[-1]["away_score"]==g["away_score"] and p[-1]["home_score"]==g["home_score"],
       g["id"]+" scoring chronology reconciles to final")
 check(sum(x["points"] for x in p)==g["away_score"]+g["home_score"],g["id"]+" scoring points reconcile")
check(len([x for x in report if x["status"]=="complete"])==4,"Four complete official source gamebooks plus a documented partial")
check(report[0]["status"]=="partial","Western New Mexico missing defense remains explicitly partial")
check(all(x["game_id"]!=games[0]["id"] for x in fantasy),"Unverified partial 2017 WNM game has no fabricated Full-PPR score")
bandy=next(x for x in fantasy if x["game_id"]==games[2]["id"] and x["player"]=="Michael Bandy")
check(bandy["fantasy_ppr"]==66.4,"Michael Bandy 10-324-4 computes exactly to 66.40 PPR")
check(any(x["player"]=="Anthony Lawrence" and x["game_id"]==games[2]["id"] for x in rows),
      "2017-18 schoolbook aliases unify Anthony Lawrence")
for file in ["assets/archive.js","index.html","game.html","stats.html","player.html","records.html","touchdowns.html","highlights.html"]:
 txt=(ROOT/"cfb"/file).read_text()
 scripts=[txt] if file.endswith(".js") else re.findall(r"<script(?: [^>]*)?>([\s\S]*?)</script>",txt)
 for script in scripts:
  if not script.strip():continue
  with tempfile.NamedTemporaryFile(mode="w",suffix=".js") as tmp:
   tmp.write(script);tmp.flush()
   proc=subprocess.run(["node","--check",tmp.name],capture_output=True,text=True)
   check(proc.returncode==0,file+" scripts parse "+proc.stderr[:160])
class Quiet(SimpleHTTPRequestHandler):
 def log_message(self,*args):pass
server=ThreadingHTTPServer(("127.0.0.1",0),partial(Quiet,directory=str(ROOT)))
threading.Thread(target=server.serve_forever,daemon=True).start()
base=f"http://127.0.0.1:{server.server_address[1]}/"
try:
 with sync_playwright() as pw:
  browser=pw.chromium.launch(headless=True,args=["--no-sandbox"])
  for width in [1280,390]:
   page=browser.new_page(viewport={"width":width,"height":900})
   errors=[]
   page.on("pageerror",lambda err:errors.append(str(err)))
   def visit(path):
    resp=page.goto(base+path,wait_until="domcontentloaded")
    check(resp and resp.status==200,f"{width} {path} loads")
   def fits(place):
    check(page.evaluate("document.documentElement.scrollWidth <= innerWidth + 2"),f"{width} {place} fits viewport")
   visit("cfb/index.html")
   page.wait_for_function("document.getElementById('gameCount').textContent==='5'")
   check(page.locator("#games .game-card").count()==3,f"{width} overview has three recent game cards")
   check(page.locator("#gameHistoryRows tr").count()==5,f"{width} five-game history")
   check("Michael Bandy" in page.locator("#leaders").inner_text(),f"{width} signature records populate")
   fits("overview")
   visit("cfb/game.html?id=cfb-2018-11-10-davidson-usd")
   page.wait_for_function("document.querySelectorAll('#scoring .play').length===16")
   check("Michael Bandy" in page.locator("#playerOfGame").inner_text() and "66.40" in page.locator("#playerOfGame").inner_text(),f"{width} Bandy is 2018 PPR Player of Game")
   check("Lawrence" in page.locator("#boxscore").inner_text(),f"{width} historic USD offense box score")
   check(page.locator("#pprLeaders .impact-board tbody tr").count()==5,f"{width} 2018 Top Five PPR table")
   page.get_by_role("tab",name="Defense").click()
   check("Tackles & Defense" in page.locator("#boxscore").inner_text(),f"{width} defensive box scores")
   page.get_by_role("tab",name="Special Teams").click()
   check("Kicking" in page.locator("#boxscore").inner_text(),f"{width} kicking and returns")
   page.locator("#gameSelect").select_option("cfb-2025-09-11-ncs-wfu")
   page.wait_for_function("document.querySelectorAll('#scoring .play').length===10")
   check("Barnes" in page.locator("#scoring").inner_text(),f"{width} 2025 Wake Forest scoring chronology")
   fits("game detail")
   visit("cfb/stats.html")
   page.wait_for_function("document.querySelectorAll('#board tbody tr').length>0")
   check("Lawrence" in page.locator("#board").inner_text(),f"{width} cumulative passing stats")
   page.get_by_role("tab",name="Fantasy PPR").click()
   check("Michael Bandy" in page.locator("#board").inner_text(),f"{width} fantasy leaderboard includes Bandy")
   fits("leaderboards")
   visit("cfb/player.html?id=cfb-usd-anthony-lawrence")
   page.wait_for_function("document.getElementById('playerName').textContent==='Anthony Lawrence'")
   check(page.locator("#games .game-card").count()>=3,f"{width} Lawrence's schoolbook aliases aggregate")
   fits("player profile")
   visit("cfb/records.html")
   page.wait_for_function("document.querySelectorAll('#recordCards .records-card').length===13")
   check(page.locator("#mainTabs [role=tab]").count()==4,f"{width} NFL-equivalent four Records tabs")
   check("556" in page.locator("#recordCards").inner_text(),f"{width} Lawrence 556 passing record")
   check(page.locator("#recordTop10 tr").count()==10,f"{width} ten ranked single-game passing performances")
   page.get_by_role("tab",name="Milestones").click()
   page.locator("#milestoneStat").select_option("ppr40")
   check(int(page.locator("#milestoneCount").inner_text())>=2,f"{width} 40+ PPR milestone list")
   page.get_by_role("tab",name="Team & Game Records").click()
   check("108" in page.locator("#teamCards").inner_text(),f"{width} Davidson 108 point combined scoring record")
   page.get_by_role("tab",name="Legendary Performances").click()
   check("Michael Bandy" in page.locator("#feats").inner_text(),f"{width} Bandy legendary statistical feat")
   check(page.locator("#moments tr").count()>0,f"{width} iconic scoring moments")
   fits("Records")
   visit("cfb/touchdowns.html")
   fits("Touchdown History")
   visit("index.html")
   page.wait_for_function("document.getElementById('allGames').textContent==='133'")
   check(page.locator("a[href='./cfb/index.html']").count()>0,f"{width} portal includes college football")
   fits("master portal")
   check(not errors,f"{width} zero JavaScript page errors: {errors}")
   page.close()
  browser.close()
finally:
 server.shutdown()
print("PASS college football source and desktop/mobile QA")
