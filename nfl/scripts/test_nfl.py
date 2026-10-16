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
P=json.loads((ROOT/"nfl/data/fantasy_ppr.json").read_text())
audit=json.loads((ROOT/"nfl/data/import_report.json").read_text())
checks=[]
def check(cond,label):
 assert cond,label
 checks.append(label)
 print("PASS",label,flush=True)
check(len(G)==3 and len(R)==253 and audit["all_games_fully_imported"],"Three complete historical game imports, 253 statistical category rows")
check(len(P["performances"])==59,"59 eligible offensive fantasy player-game records")
check(P["audit"]["milestones"]=={"10":25,"20":5,"25":4,"30":2,"40":1},"Known 10/20/25/30/40 Full-PPR milestones")
check(P["performances"][0]["player"]=="Frank Gore" and P["performances"][0]["fantasy_ppr"]==44.4,"Frank Gore 44.40 PPR: 116 rushing, two rushing TDs, 11 catches, 98 receiving")
check(P["performances"][1]["player"]=="Larry Fitzgerald" and P["performances"][1]["fantasy_ppr"]==36.6,"Larry Fitzgerald 36.60 PPR: nine catches, 156 yards, two receiving TDs")
check(all(round(sum(x["ppr_components"].values()),2)==x["fantasy_ppr"] for x in P["performances"]),"PPR component arithmetic reconciles for every player-game")
check(all(x["game_id"] in {g["id"] for g in G} for x in P["performances"]),"Fantasy records join exact attended NFL IDs")

check(set(S)==set(g["id"] for g in G),"Every imported game has a scoring-play timeline")
check([len(S[g["id"]]["plays"]) for g in G]==[11,8,13],"Scoring play counts: 11, 8, 13")
for g in G:
 plays=S[g["id"]]["plays"]
 check(sum(p["points"] for p in plays)==g["away_score"]+g["home_score"],g["id"]+" scoring sum matches final score")
 check(plays[-1]["away_score"]==g["away_score"] and plays[-1]["home_score"]==g["home_score"],g["id"]+" scoring timeline ends at verified final score")
 check(all(p["description"] and p["clock"] and p["team"] for p in plays),g["id"]+" plays include original description and clock")
for name in ("nfl/assets/archive.js","nfl/index.html","nfl/game.html","nfl/stats.html","nfl/player.html","nfl/milestones.html","nfl/records.html"):
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
  for width in (1330,390):
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
   check(page.locator("#leaders .ca-feature").count()==3 and "Kurt Warner" in page.locator("#leaders").inner_text(),str(width)+" three passing/rushing/receiving signature cards render on overview")
   noOverflow("overview")
   visit("nfl/game.html?id=nfl-2023-12-03-ind-ten")
   page.wait_for_function("document.querySelectorAll('#scoring .play').length===13")
   check("M.Pittman" in page.locator("#scoring").inner_text(),str(width)+" detailed 2023 game-winning scoring description")
   check("Gardner Minshew" in page.locator("#boxscore").inner_text(),str(width)+" 2023 offense box score")
   check(page.locator("#boxscore").bounding_box()["y"]+page.locator("#boxscore").bounding_box()["height"] <= page.locator("#scoring").bounding_box()["y"],
         str(width)+" scoring plays appear below the entire offensive box score")
   check(page.locator("#pprLeaders").bounding_box()["y"] < page.locator("#boxscore").bounding_box()["y"],
         str(width)+" fantasy ranking stays above NFL player box score")
   nfl_styles=page.evaluate("""() => {
     const selectors={"heading":"#pprLeaders h2","player":"#pprLeaders .impact-player a",
       "team":"#pprLeaders .impact-player small","score":"#pprLeaders .impact-number strong",
       "header":"#pprLeaders .impact-board th","stats":"#pprLeaders .impact-board td:nth-child(3)"};
     return Object.fromEntries(Object.entries(selectors).map(([name,selector])=>[name,getComputedStyle(document.querySelector(selector)).fontSize]));
   }""")
   top_gap=page.evaluate("""() => Math.round(
     document.querySelector('#pprLeaders .impact-scroll').getBoundingClientRect().top
      - document.querySelector('#pprLeaders .ppr-board-heading').getBoundingClientRect().bottom)""")
   check(10<=top_gap<=16,str(width)+" NFL top-fantasy panel has basketball-sized header-to-table spacing")
   visit("nba/game.html?id=1")
   page.wait_for_function("document.querySelectorAll('.impact-board tbody tr').length===5")
   nba_styles=page.evaluate("""() => {
     const selectors={"heading":"section.panel:has(.impact-board) h2","player":".impact-board .impact-player a",
       "team":".impact-board .impact-player small","score":".impact-board .impact-number strong",
       "header":".impact-board th","stats":".impact-board td:nth-child(3)"};
     return Object.fromEntries(Object.entries(selectors).map(([name,selector])=>[name,getComputedStyle(document.querySelector(selector)).fontSize]));
   }""")
   check(nfl_styles==nba_styles,str(width)+" NFL leaderboard font sizes match NBA player, team, score, header, stat and title")
   visit("nfl/game.html?id=nfl-2023-12-03-ind-ten")
   page.wait_for_function("document.querySelectorAll('#pprLeaders .impact-board tbody tr').length===5")
   check("Michael Pittman Jr." in page.locator("#pprLeaders").inner_text(),str(width)+" 2023 box score highlights top Full-PPR performers")
   check(page.locator("#pprLeaders .impact-board tbody tr").count()==5,str(width)+" Top fantasy performances matches the five-row basketball table")
   check(page.locator("#pprLeaders .impact-board th").all_text_contents()==["Player","PPR points","Receiving","Rushing","Passing"],str(width)+" Fantasy table preserves its original production columns")
   check(page.locator("#pprLeaders .impact-player small").count()==5,str(width)+" Five NFL players show teams below linked names")
   check(page.locator("#pprLeaders .impact-number strong").first.inner_text()=="27.50",str(width)+" 2023 fantasy leader displays highlighted PPR score")
   check(page.evaluate("getComputedStyle(document.querySelector('#pprLeaders .impact-board th')).textTransform")=="uppercase",str(width)+" Fantasy table headers use basketball leaderboard styling")
   check("Michael Pittman Jr." in page.locator("#playerOfGame").inner_text() and "27.50" in page.locator("#playerOfGame").inner_text(),str(width)+" 2023 Player of the Game uses highest Full-PPR score")
   check(page.locator("#playerOfGame").bounding_box()["y"]<page.locator("#scoring").bounding_box()["y"],str(width)+" Player of the Game sits above scoring chronology")
   page.get_by_role("tab",name="Defense").click()
   check("Tackles & Defense" in page.locator("#boxscore").inner_text(),str(width)+" grouped defensive box score")
   page.get_by_role("tab",name="Special Teams").click()
   check("Kicking" in page.locator("#boxscore").inner_text(),str(width)+" grouped kicking and returns box score")
   page.locator("#gameSelect").select_option("nfl-2007-11-25-sf-ari")
   page.wait_for_function("document.querySelectorAll('#scoring .play').length===11")
   check("Tully Banta-Cain" in page.locator("#scoring").inner_text(),str(width)+" 2007 overtime defensive walkoff appears")
   check("Frank Gore" in page.locator("#playerOfGame").inner_text() and "44.40" in page.locator("#playerOfGame").inner_text(),str(width)+" 2007 Player of the Game updates on selection")
   check("Frank Gore" in page.locator("#pprLeaders .impact-board tbody tr").first.inner_text() and "44.40" in page.locator("#pprLeaders .impact-number strong").first.inner_text(),str(width)+" 2007 fantasy table tracks selected game")
   page.locator("#gameSelect").select_option("nfl-2008-12-07-stl-ari")
   check("Larry Fitzgerald" in page.locator("#playerOfGame").inner_text() and "19.30" in page.locator("#playerOfGame").inner_text(),str(width)+" 2008 Player of the Game uses highest Full-PPR score")
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
   page.locator("#search").fill("")
   page.get_by_role("tab",name="Fantasy PPR").click()
   check("Larry Fitzgerald" in page.locator("#board tbody tr").first.inner_text(),str(width)+" cumulative PPR leaderboard ranks Fitzgerald's two performances first")
   check("55.90" in page.locator("#board tbody tr").first.inner_text(),str(width)+" two witnessed Fitzgerald scores correctly total 55.90 PPR")
   page.locator("#gameFilter").select_option("nfl-2007-11-25-sf-ari")
   check("44.40" in page.locator("#board tbody tr").first.inner_text(),str(width)+" per-game PPR leaderboard ranks Gore's 44.40")
   page.locator("#gameFilter").select_option("all")
   noOverflow("leaderboard")
   visit("nfl/player.html?id=1682")
   page.wait_for_function("document.getElementById('playerName').textContent==='Kurt Warner'")
   check(page.locator("#games .game-card").count()==2,str(width)+" Warner has two attended Arizona games")
   check(page.locator("#careerStats table").count()>0,str(width)+" player cumulative categories link to personal game logs")
   check(page.locator("#pprStats tbody tr").count()==2,str(width)+" Warner personal profile shows two fantasy game logs")
   visit("nfl/records.html")
   page.wait_for_function("document.querySelectorAll('#recordCards .records-card').length===13")
   check(page.locator('#mainTabs [role="tab"]').count()==4,str(width)+" four basketball-style NFL records tabs")
   check(page.locator('#recordCards .records-card').count()==13,str(width)+" offensive record book loads all player-category record cards")
   check(page.locator('#recordTop10 tr').count()==8,str(width)+" passing Top 10 lists eight actual player-games without fabricated entries")
   check(page.locator('#recordTop10 a[href^="./player.html?id="]').count()==8,str(width)+" all passing Top 10 performances link to verified player profiles")
   check("484" in page.locator("#recordCards").inner_text(),str(width)+" Kurt Warner 484-yard passing record")
   page.locator('#recordStat').select_option("4")
   check(page.locator('#recordTop10 tr').count()==10,str(width)+" rushing yards loads ten individual games")
   page.locator('#recordGroups button[data-group="defense"]').click()
   check(page.locator('#recordCards .records-card').count()==8 and page.locator('#recordTop10 tr').count()==10,
         str(width)+" defense record cards and Top 10 update together")
   page.locator('#recordGroups button[data-group="special"]').click()
   check(page.locator('#recordCards .records-card').count()==10,str(width)+" special teams record cards load")
   page.get_by_role("tab",name="Milestones").click()
   page.wait_for_function("document.querySelector('#milestoneCount').textContent !== '—'")
   page.locator('#milestoneStat').select_option("ppr30")
   check(page.locator('#milestoneCount').inner_text()=="2",str(width)+" integrated 30+ Full-PPR milestone has Gore and Fitzgerald")
   check("Frank Gore" in page.locator('#milestoneBody').inner_text(),str(width)+" milestone shows offense fantasy performances")
   page.locator('#milestoneModes button[data-mode="players"]').click()
   check(page.locator('#milestoneBody tr').count()==2,str(width)+" milestone player-frequency rankings work")
   page.locator('#milestoneModes button[data-mode="performances"]').click()
   page.locator('#milestoneGroups button[data-group="defense"]').click()
   page.locator('#milestoneStat').select_option("tackles10")
   check(page.locator('#milestoneBody tr').count()>=1,str(width)+" defensive tackle milestones work")
   page.locator('#milestoneGroups button[data-group="special"]').click()
   page.locator('#milestoneStat').select_option("fg3")
   check(page.locator('#milestoneBody tr').count()>=1,str(width)+" kicker milestones use actual made field goals")
   page.get_by_role("tab",name="Team & Game Records").click()
   check(page.locator('#teamCards .records-card').count()==6,str(width)+" six classic basketball-style team and game records")
   check(page.locator('#dramaCards .records-card').count()==7,str(width)+" quarter, half, comeback and game-drama records")
   check("68" in page.locator('#teamCards').inner_text(),str(width)+" witnessed 68-point SF-Arizona combined scoring record")
   check(page.locator('#teamGames tr').count()==3,str(width)+" complete attended NFL results list")
   page.locator('#scoringGroups button[data-group="defense"]').click()
   check("defensive touchdowns" in page.locator('#scoringCards').inner_text().lower(),str(width)+" defense touchdown scoring breakdown")
   page.locator('#scoringGroups button[data-group="special"]').click()
   check("blocked-kick touchdowns" in page.locator('#scoringCards').inner_text().lower(),str(width)+" special teams blocked-punt scoring breakdown")
   page.get_by_role("tab",name="Legendary Performances").click()
   check(page.locator('#feats tr').count()>=3,str(width)+" legendary statistical feats populate from attended players")
   check("Frank Gore" in page.locator('#feats').inner_text(),str(width)+" Gore 44.4 PPR legendary feat")
   check("99" in page.locator('#moments').inner_text(),str(width)+" 99-yard interception return iconic moment")
   check("Tully Banta-Cain" in page.locator('#moments').inner_text(),str(width)+" OT walk-off credited to original defender")
   page.locator('#featGroups button[data-group="offense"]').click()
   check("Frank Gore" in page.locator('#feats').inner_text(),str(width)+" offensive feat filter works")
   page.locator('#momentGroups button[data-group="special"]').click()
   check("Grant Stuard" in page.locator('#moments').inner_text(),str(width)+" special teams iconic blocked punt is attributed")
   check(page.locator('#momentGroups button[data-group="special"]').get_attribute("aria-pressed")=="true",
         str(width)+" statistical feat and iconic moment filters stay independent")
   check(page.locator('.archive-nav a[href="./records.html"]').get_attribute("aria-current")=="page",str(width)+" NFL primary navigation highlights unified Records page")
   check(page.locator('.archive-nav a[href="./milestones.html"]').count()==0 and page.locator('.archive-nav a[href="./highlights.html"]').count()==0,
         str(width)+" legacy milestones and highlights remain accessible without duplicate primary navigation")
   noOverflow("unified NFL records")
   out=ROOT/"nfl/output/records";out.mkdir(parents=True,exist_ok=True)
   page.screenshot(path=str(out/("records-"+str(width)+".png")),full_page=True)
   visit("nfl/milestones.html")
   page.wait_for_function("document.getElementById('playerGameCount').textContent==='59'")
   check(page.locator("#maxScore").inner_text()=="44.40",str(width)+" PPR milestones show best witnessed game")
   check(page.locator("#thirtyCount").inner_text()=="2" and page.locator("#twentyCount").inner_text()=="5",str(width)+" high-impact tier counts correct")
   check(page.locator("#performanceTable tbody tr").count()==59,str(width)+" all 59 player-game performances listed")
   page.get_by_role("button",name="30+ impact").click()
   check(page.locator("#performanceTable tbody tr").count()==2,str(width)+" 30+ impact filter selects Gore and Fitzgerald")
   page.get_by_role("button",name="40+ elite").click()
   check(page.locator("#performanceTable tbody tr").count()==1 and "Frank Gore" in page.locator("#performanceTable tbody").inner_text(),str(width)+" 40+ elite selects Gore")
   page.get_by_role("button",name="All",exact=True).click()
   page.locator("#gameFilter").select_option("nfl-2023-12-03-ind-ten")
   check(page.locator("#performanceTable tbody tr").count()==20,str(width)+" 2023 game has 20 source-qualified fantasy scorers")
   page.locator("#search").fill("Pittman")
   check(page.locator("#performanceTable tbody tr").count()==1,str(width)+" PPR milestone search works")
   page.locator("#search").fill("")
   page.locator("#gameFilter").select_option("all")
   noOverflow("milestones")
   out=ROOT/"nfl/output/ppr";out.mkdir(parents=True,exist_ok=True)
   page.screenshot(path=str(out/("milestones-"+str(width)+".png")),full_page=True)
   noOverflow("player profile")
   visit("index.html")
   page.wait_for_function("document.getElementById('allGames').textContent==='136'")
   check(page.locator('a[href="./nfl/index.html"]').count()>=1,str(width)+" master portal links to NFL")
   noOverflow("master portal")
   check(not errors,str(width)+" no uncaught JavaScript errors")
   page.close()
  browser.close()
finally:
 server.shutdown()
print("PASS",len(checks),"source validations, browser behaviors and mobile tests",flush=True)
