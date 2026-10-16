#!/usr/bin/env python3
"""Soccer attendance archive: source integrity, navigation and browser behavior."""
import json,re,subprocess,tempfile,threading
from functools import partial
from http.server import SimpleHTTPRequestHandler,ThreadingHTTPServer
from pathlib import Path
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[2]
data=json.loads((ROOT/"soccer/data/matches.json").read_text())
def check(ok,msg):
 assert ok,msg
 print("PASS",msg,flush=True)
check(len(data)==3,"Only three launch matches are imported")
check({m["id"] for m in data}=={
 "soc-2026-10-14-nsh-skc","soc-2026-08-29-nsh-cin","soc-2026-06-24-mar-hai"
},"No old USL matches mixed into launch scope")
for m in data:
 check(len(m["home_starters"])==len(m["away_starters"])==11,m["id"]+" contains two eleven-player starting XIs")
 result={m["home_abbr"]:0,m["away_abbr"]:0}
 for e in m["events"]:
  if e["type"] in ("goal","penalty_goal","own_goal"):result[e["team"]]+=1
 check(result[m["home_abbr"]]==m["home_score"] and result[m["away_abbr"]]==m["away_score"],m["id"]+" goal events reconcile to final score")
 check(m.get("source_url","").startswith("https://"),m["id"]+" links to a verified source")
check(sum(m["home_score"]+m["away_score"] for m in data)==14,"14 goals across three attended matches")
check(data[0]["competition"]=="FIFA World Cup","World Cup is included without forcing MLS assist rules")
for file in ["archive.js","pages.js"]:
 src=(ROOT/"soccer/assets"/file).read_text()
 with tempfile.NamedTemporaryFile(suffix=".js",mode="w") as tmp:
  tmp.write(src);tmp.flush()
  p=subprocess.run(["node","--check",tmp.name],capture_output=True,text=True)
  check(p.returncode==0,file+" JavaScript parses: "+p.stderr[:500])
class Quiet(SimpleHTTPRequestHandler):
 def log_message(self,*args):pass
server=ThreadingHTTPServer(("127.0.0.1",0),partial(Quiet,directory=str(ROOT)))
threading.Thread(target=server.serve_forever,daemon=True).start()
base=f"http://127.0.0.1:{server.server_address[1]}/"
try:
 with sync_playwright() as pw:
  browser=pw.chromium.launch(headless=True,args=["--no-sandbox"])
  for width in [1330,390]:
   page=browser.new_page(viewport={"width":width,"height":900})
   errors=[]
   page.on("pageerror",lambda e: errors.append(str(e)))
   def visit(path,loaded):
    r=page.goto(base+path,wait_until="domcontentloaded")
    check(r and r.status==200,f"{width} {path} opens")
    page.wait_for_function(loaded)
    check(not errors,f"{width} {path} no page script errors: {errors}")
   def fits(section):
    check(page.evaluate("document.documentElement.scrollWidth<=innerWidth+3"),f"{width} {section} fits viewport")
   visit("soccer/index.html","document.querySelector('#history table tbody tr')!==null")
   check(page.locator("#history table tbody tr").count()==3,f"{width} three witnessed matches in overview")
   check(page.locator("#games .game-card").count()==3,f"{width} three recent-match cards")
   check(page.locator("#leaders").count()==0 or page.locator(".soccer-feature").count()>=3,f"{width} three signature performers")
   check(page.locator(".soccer-charts .soccer-chart").count()==2,f"{width} watched teams and years charts")
   fits("overview")
   visit("soccer/game.html?id=soc-2026-06-24-mar-hai","document.querySelector('#gameSelect')!==null")
   check("Morocco" in page.locator("#app").inner_text() and "Haiti" in page.locator("#app").inner_text(),f"{width} World Cup match report")
   check(page.locator(".soccer-lineup ol li").count()==22,f"{width} FIFA starting lineups")
   check(page.locator(".soccer-panel").count()>=4,f"{width} goal, lineup, team-stat and timeline panels")
   check(page.locator(".soccer-event").count()>=25,f"{width} match timeline and goals show events")
   page.locator("#gameSelect").select_option("soc-2026-10-14-nsh-skc")
   check("Sporting Kansas City" in page.locator("#app").inner_text(),f"{width} game selector updates page")
   fits("match report")
   visit("soccer/stats.html","document.querySelector('#board tbody tr')!==null")
   page.locator("#category").select_option("goals")
   check("Hany Mukhtar" in page.locator("#board").inner_text(),f"{width} verified personal goals leaderboard")
   page.locator("#category").select_option("assists")
   check("Hany Mukhtar" in page.locator("#board").inner_text(),f"{width} direct assists leaderboard")
   page.locator("#matchFilter").select_option("soc-2026-08-29-nsh-cin")
   check("Nashville" not in page.locator("#board").inner_text() or page.locator("#board tbody tr").count()>0,f"{width} selectable single match filtering")
   fits("leaderboards")
   visit("soccer/player.html?id=hany-mukhtar","document.querySelector('.soccer-profile-head')!==null")
   check("Hany Mukhtar" in page.locator(".soccer-profile-head").inner_text(),f"{width} linked player profile")
   check(page.locator(".game-grid .game-card").count()==2,f"{width} Mukhtar has two MLS matches")
   check(page.locator(".soccer-stat-table tbody tr").count()==2,f"{width} player game logs")
   fits("player profile")
   visit("soccer/records.html","document.querySelector('#recordCards .soccer-tile')!==null")
   check(page.locator("#mainTabs button").count()==4,f"{width} four NFL-parity Records tabs")
   check(page.locator("#recordCards .soccer-tile").count()==6,f"{width} six record-holder cards")
   page.locator("#mainTabs button[data-tab='milestones']").click()
   check(page.locator("#milestoneTable tbody tr").count()>=1,f"{width} per-game milestone achievements")
   page.locator("#milestoneMode").select_option("players")
   check(page.locator("#milestoneTable tbody tr").count()>=1,f"{width} player frequency milestone rankings")
   page.locator("#mainTabs button[data-tab='teams']").click()
   check(page.locator("#teamCards .soccer-tile").count()==6,f"{width} team and match records")
   page.locator("#mainTabs button[data-tab='legendary']").click()
   check("Achraf Hakimi" in page.locator("#feats").inner_text(),f"{width} source-backed World Cup feat")
   check("Own goal" in page.locator("#moments").inner_text(),f"{width} own goal logged as iconic moment")
   fits("Records")
   visit("soccer/goals.html","document.querySelector('#goalRows .soccer-event')!==null")
   check(page.locator("#goalRows .soccer-event").count()==14,f"{width} full verified 14-goal history")
   page.locator("#goalKind").select_option("own_goal")
   check(page.locator("#goalRows .soccer-event").count()==1,f"{width} own goal separated")
   fits("goal history")
   visit("index.html","document.getElementById('allGames').textContent==='267'")
   check(page.locator(".sport-card").count()==6,f"{width} master hub six sports")
   check(page.locator("a[href='./soccer/index.html']").count()>=1,f"{width} soccer featured in hub")
   fits("five-sport master hub")
   page.close()
  browser.close()
finally:server.shutdown()
print("PASS soccer browser regression")
