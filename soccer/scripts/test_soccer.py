#!/usr/bin/env python3
"""Soccer attendance archive: source integrity, navigation and browser behavior."""
import json,re,subprocess,tempfile,threading
from functools import partial
from http.server import SimpleHTTPRequestHandler,ThreadingHTTPServer
from pathlib import Path
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[2]
data=json.loads((ROOT/"soccer/data/matches.json").read_text())
nationalities=json.loads((ROOT/"soccer/data/nationalities.json").read_text())
def check(ok,msg):
 assert ok,msg
 print("PASS",msg,flush=True)
names={name for m in data for key in ("home_starters","away_starters","home_subs_used","away_subs_used") for name in m.get(key,[])}
names.update(name for m in data for e in m["events"] for key in ("player","out","assist","secondary_assist") if (name:=e.get(key)))
assigned=[name for group in nationalities.values() for name in group]
check(set(assigned)==names and len(assigned)==len(names),f"All {len(names)} soccer players have one nationality tag")
check("Ahmed Qasem" in nationalities["IQ"] and "Samuel Gidi" in nationalities["SK"],"National-team affiliation overrides birthplace for dual-national players")
check(len(data)==3,"Only three launch matches are imported")
honors=json.loads((ROOT/"soccer/data/career_honors.json").read_text())
honored=honors["players"]
slug=lambda s:re.sub(r"[^a-z0-9]+","-",__import__("unicodedata").normalize("NFKD",s).encode("ascii","ignore").decode().lower()).strip("-")
check(len(honored)>=10,"Focused verified career-honor recipient registry")
check(all(row["name"] in names and slug(row["name"])==key for key,row in honored.items()),"Every career honor belongs to a witnessed player identity")
check(all(v.get("source_url","").startswith("https://") for row in honored.values() for key in ("world_cup","league_titles","mls_cup","supporters_shield","mls_awards") for v in row.get(key,[])),"Every career award has a source URL")
check(all(not any(w in str(a.get("award","")).lower() for w in ("save of the year","goal of the year","all-star")) for row in honored.values() for a in row.get("mls_awards",[])),"Exclude fan-voted MLS honors")
check(any(a["award"]=="MLS Most Valuable Player" for a in honored["hany-mukhtar"]["mls_awards"]),"Hany Mukhtar's 2022 MLS MVP")
check(any(a["season"]=="2025-26" for a in honored["achraf-hakimi"]["league_titles"]),"2026 Ligue 1 title verified")
check(not any(a.get("year")==2026 for row in honored.values() for a in row.get("mls_awards",[])),"2026 end-of-year awards not prematurely awarded")

individual=json.loads((ROOT/"soccer/data/individual_honors.json").read_text())
ind=individual["players"]
award_families=("global","uefa","domestic","international")
check(individual["_meta"]["reviewed_unique_soccer_players"]==len(names),"Global awards reviewed against entire witnessed soccer pool")
check("The Best FIFA Men's Player" in individual["_meta"]["recognition_catalog"]["global"],"The Best FIFA Men's Player included in award catalog")
check(all(row["name"] in names and slug(row["name"])==key for key,row in ind.items()),"Individual accolades never tag unwitnessed players")
check(all(row["award"] and row["source_url"].startswith("https://") for p in ind.values() for family in award_families for row in p.get(family,[])),"Every individual accolade verified with award label and source")
check(sum(len(p.get(family,[])) for p in ind.values() for family in award_families)>=25,"Major European and global awards are populated")
check({a["year"] for a in ind["achraf-hakimi"]["global"] if a["award"]=="FIFPRO Men's World XI"}=={2022,2025,2026},"Hakimi historic and current FIFPRO World XI years")
check(any(a["award"]=="The Best FIFA Men's 11" for a in ind["achraf-hakimi"]["global"]),"The Best FIFA 2025 Men XI")
check(any(a["award"]=="CAF African Player of the Year" for a in ind["achraf-hakimi"]["international"]),"Hakimi CAF Player of Year")
check({a["year"] for a in ind["yassine-bounou"]["international"] if a["award"]=="CAF African Goalkeeper of the Year"}=={2023,2025},"Bounou two CAF Goalkeeper awards")
check(any(a["award"]=="AFCON Golden Boot" and a["year"]==2025 for a in ind["brahim-diaz"]["international"]),"Brahim Diaz AFCON top scorer")
check(any(a["award"]=="Eredivisie Player of the Year" for a in ind["ismael-saibari"]["domestic"]),"Saibari domestic player of year")
check(any(a["award"]=="UEFA Europa Conference League Player of the Season" for a in ind["ayoub-el-kaabi"]["uefa"]),"El Kaabi Conference League Player of Season")
check(all("Save of the Year" not in a["award"] and "Goal of the Year" not in a["award"] for p in ind.values() for family in award_families for a in p.get(family,[])),"Exclude low-value novelty goals and saves")


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
   check(page.locator(".soccer-lineup li .soccer-flag").count()==32,f"{width} every World Cup lineup player has a flag")
   check(page.locator(".soccer-panel").count()>=4,f"{width} goal, lineup, team-stat and timeline panels")
   check(page.locator(".soccer-event").count()>=25,f"{width} match timeline and goals show events")
   page.locator("#gameSelect").select_option("soc-2026-10-14-nsh-skc")
   check("Sporting Kansas City" in page.locator("#app").inner_text(),f"{width} game selector updates page")
   fits("match report")
   visit("soccer/stats.html","document.querySelector('#board tbody tr')!==null")
   page.locator("#category").select_option("goals")
   check("Hany Mukhtar" in page.locator("#board").inner_text(),f"{width} verified personal goals leaderboard")
   check(page.locator("#board tbody tr .soccer-flag").count()>0,f"{width} leaderboard players show flags")
   page.locator("#category").select_option("assists")
   check("Hany Mukhtar" in page.locator("#board").inner_text(),f"{width} direct assists leaderboard")
   page.locator("#matchFilter").select_option("soc-2026-08-29-nsh-cin")
   check("Nashville" not in page.locator("#board").inner_text() or page.locator("#board tbody tr").count()>0,f"{width} selectable single match filtering")
   fits("leaderboards")
   visit("soccer/player.html?id=hany-mukhtar","document.querySelector('.soccer-profile-head')!==null")
   check("Hany Mukhtar" in page.locator(".soccer-profile-head").inner_text(),f"{width} linked player profile")
   check(page.locator(".soccer-profile-head h1 .soccer-flag[aria-label='Germany']").count()==1,f"{width} player profile shows nationality")
   check(page.locator(".game-grid .game-card").count()==2,f"{width} Mukhtar has two MLS matches")
   check(page.locator(".soccer-stat-table tbody tr").count()==2,f"{width} player game logs")
   fits("player profile")
   check(page.locator(".soccer-career-badge").count()>=1,f"{width} Hany Mukhtar verified MLS award tag")
   check("MLS Most Valuable Player" in page.locator("#soccerCareerHonors").inner_text(),f"{width} Mukhtar MVP displays")
   check("MLS Golden Boot" in page.locator("#soccerCareerHonors").inner_text(),f"{width} Mukhtar Golden Boot displays")
   visit("soccer/player.html?id=achraf-hakimi","document.querySelector('#soccerCareerHonors')!==null")
   check("2018" in page.locator("#soccerCareerHonors").inner_text() and "2026" in page.locator("#soccerCareerHonors").inner_text(),f"{width} historical and attended World Cup years")
   check("2025-26" in page.locator("#soccerCareerHonors").inner_text(),f"{width} 2026 European league title displays")
   fits("Achraf Hakimi career honors")
   visit("soccer/player.html?id=roman-celentano","document.querySelector('#soccerCareerHonors')!==null")
   check("Supporters' Shield" in page.locator("#soccerCareerHonors").inner_text(),f"{width} Shield is distinct from MLS Cup")
   check("Save of the Year" not in page.locator("#app").inner_text(),f"{width} fan-voted Save of the Year excluded")
   fits("Roman Celentano career honors")
   visit("soccer/player.html?id=achraf-hakimi","document.querySelector('#soccerCareerHonors')!==null")
   check("FIFPRO MEN'S WORLD XI" in page.locator(".soccer-career-badges").inner_text(),f"{width} Hakimi FIFPRO World XI badge")
   check("THE BEST FIFA MEN'S 11" in page.locator(".soccer-career-badges").inner_text(),f"{width} Hakimi Best FIFA Men XI badge")
   check("CAF AFRICAN PLAYER OF THE YEAR" in page.locator(".soccer-career-badges").inner_text(),f"{width} Hakimi CAF African Player tag")
   fits("Hakimi global awards")
   visit("soccer/player.html?id=yassine-bounou","document.querySelector('#soccerCareerHonors')!==null")
   check("CAF AFRICAN GOALKEEPER OF THE YEAR" in page.locator(".soccer-career-badges").inner_text(),f"{width} Bounou CAF goalkeeper tag")
   check("ZAMORA TROPHY" in page.locator(".soccer-career-badges").inner_text(),f"{width} Bounou Zamora tag")
   fits("Bounou individual honors")
   visit("soccer/player.html?id=ayoub-el-kaabi","document.querySelector('#soccerCareerHonors')!==null")
   check("UEFA EUROPA CONFERENCE LEAGUE PLAYER OF THE SEASON" in page.locator(".soccer-career-badges").inner_text(),f"{width} El Kaabi UEFA Player of Season tag")
   fits("El Kaabi individual honors")
   visit("soccer/player.html?id=ismael-saibari","document.querySelector('#soccerCareerHonors')!==null")
   check("EREDIVISIE PLAYER OF THE YEAR" in page.locator(".soccer-career-badges").inner_text(),f"{width} Saibari Dutch league player of year tag")
   fits("Saibari domestic awards")
   visit("soccer/records.html","document.querySelector('#recordCards .soccer-tile')!==null")
   check(page.locator("#mainTabs button").count()==4,f"{width} four NFL-parity Records tabs")
   check(page.locator("#recordCards .soccer-tile").count()==6,f"{width} six record-holder cards")
   check(page.locator("#recordCards .soccer-flag").count()==6,f"{width} record-holder players show flags")
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
   check(page.locator("#goalRows .soccer-flag").count()>=14,f"{width} goals and assists show nationality flags")
   page.locator("#goalKind").select_option("own_goal")
   check(page.locator("#goalRows .soccer-event").count()==1,f"{width} own goal separated")
   fits("goal history")
   visit("index.html","Number((document.getElementById('allGames')?.textContent||'').replace(/,/g,''))>0")
   check(page.locator(".sport-card").count()==8,f"{width} master hub eight sports including MiLB")
   check(page.locator("a[href='./college-baseball/index.html']").count()>=1,f"{width} college baseball now listed in hub")
   check(page.locator("a[href='./soccer/index.html']").count()>=1,f"{width} soccer featured in hub")
   fits("eight-sport master hub")
   page.close()
  browser.close()
finally:server.shutdown()
print("PASS soccer browser regression")
