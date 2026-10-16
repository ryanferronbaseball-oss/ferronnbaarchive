#!/usr/bin/env python3
"""MLB Courtside Archive historical data integrity & desktop/mobile browser QA."""
import json,re,subprocess,tempfile,threading
from collections import Counter
from functools import partial
from http.server import SimpleHTTPRequestHandler,ThreadingHTTPServer
from pathlib import Path
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[2];D=ROOT/"mlb/data"
attendance=json.loads((D/"attendance.json").read_text())
games=json.loads((D/"games.json").read_text())
rows=json.loads((D/"player_stats.json").read_text())
scoring=json.loads((D/"scoring_plays.json").read_text())
report=json.loads((D/"import_report.json").read_text())
honors=json.loads((D/"career_awards.json").read_text())
honored=honors["players"]
hall_ids=[pid for pid,p in honored.items() if p.get("hall_of_fame")]
decisions=json.loads((D/"decisions.json").read_text())
def check(condition,msg):
 assert condition,msg
 print("PASS",msg,flush=True)
check(len(attendance)==len(games)==131,"131 attended games preserved")
check({g["attendance_id"] for g in games}==set(range(1,132)),"Original source entry numbers and IDs preserved")
check(report["matched"]==131 and len([g for g in games if g.get("game_pk")])==131,"All attended games matched to MLB StatsAPI")
check(report["player_rows"]==len(rows)>=3700,"All official historical player boxscores imported")
check(all(p["game_pk"] in {g["game_pk"] for g in games} for p in rows),"Every player line comes from an attended MLB game")
check(all(g["home_score"] is not None and g["away_score"] is not None for g in games),"Official final scores verified")
double=[g for g in games if g["date"]=="2022-08-02" and g["home"]=="San Diego Padres" and g["away"]=="Colorado Rockies"]
check(len(double)==2 and double[0]["game_pk"]!=double[1]["game_pk"],"2022 Rockies–Padres doubleheader uses distinct game IDs")
check(len({g["game_pk"] for g in games})==131,"No duplicate MLB game IDs")
check(len([g for g in games if g.get("innings")])==131,"All games have complete inning-level coverage")
check(len(scoring)>=131,"Scoring play data retained for every MLB game")
check(len(decisions)==131 and all(x["status"]=="verified" for x in decisions.values()),"Official W/L pitching decisions verified for all 131 MLB games")
check(all(x.get("winner",{}).get("id") and x.get("loser",{}).get("id") for x in decisions.values()),"Official winners and losers contain MLB player IDs")
check(sum(bool(x["save"]) for x in decisions.values())>=50,"Official saved/no-save game decisions independently identified")
check(decisions["15785"]["save"] is None and decisions["662250"]["save"] is None,"Confirmed no-save games are not fabricated")
check(decisions["662250"]["winner"]["name"]=="Yu Darvish","Official 2022 doubleheader decision recognizes Yu Darvish")
check(report.get("lineup_team_games_with_nine_spots")==262,"All 262 team box scores have nine official batting-order positions")
check(report.get("lineup_slot_rows",0)>3000,"Official batting slots imported for more than 3,000 player lines")
check(all(r.get("side") in ("away","home") for r in rows),"Every MLB player box-score record identifies its home/away team")
check(all(1<=r["batting_slot"]<=9 for r in rows if r.get("batting_slot") is not None),"All verified lineup slots are between one and nine")
check(len(hall_ids)==21,"Exactly 21 witnessed MLB players have Hall of Fame induction records")
check(honors["_meta"]["player_pool"]==len({str(r["player_id"]) for r in rows}),"Awards filtered to all actual unique MLB player IDs")
check(honors["_meta"]["award_recipients"]["mvp"]>=30,"Official MVP awards matched to 30+ attended players")
check(honors["_meta"]["award_recipients"]["cy_young"]>=15,"Cy Young awards matched to at least 15 pitchers seen")
check(honors["_meta"]["award_recipients"]["gold_glove"]>=150,"Official Gold Glove records matched to 150+ players")
check(honors["_meta"]["award_recipients"]["silver_slugger"]>=180,"Official Silver Slugger records matched to 180+ players")
check(all(p["hall_of_fame"]["year"]<=2026 for p in honored.values() if p.get("hall_of_fame")),"No future Hall of Fame induction classes assumed")
check(all(1960<=a["year"]<=2026 for p in honored.values() for key in ("mvp","cy_young","gold_glove","silver_slugger") for a in p.get(key,[])),"Every award has a valid historic season")
for file in ["archive.js","pages.js"]:
 src=(ROOT/"mlb/assets"/file).read_text()
 with tempfile.NamedTemporaryFile(suffix=".js",mode="w") as f:
  f.write(src);f.flush();p=subprocess.run(["node","--check",f.name],capture_output=True,text=True)
  check(p.returncode==0,file+" JavaScript passes syntax check: "+p.stderr[:500])
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
   page.on("pageerror",lambda e:errors.append(str(e)))
   def visit(path,predicate):
    response=page.goto(base+path,wait_until="domcontentloaded")
    check(response and response.status==200,f"{width} {path} opens")
    page.wait_for_function(predicate,timeout=30000)
    check(not errors,f"{width} {path} no JavaScript errors {errors}")
   def fits(where):check(page.evaluate("document.documentElement.scrollWidth <= innerWidth+3"),f"{width} {where} fits viewport")
   visit("mlb/index.html","document.querySelector('#history tbody tr')!==null")
   check(page.locator("#history tbody tr").count()==131,f"{width} all 131 games searchable on Overview")
   check(page.locator(".game-grid .game-card").count()==3,f"{width} home page recent cards")
   check(page.locator(".mlb-feature-grid .mlb-record").count()==3,f"{width} Signature Performances populated")
   check("Matched" in page.locator("#history").inner_text(),f"{width} official boxscore coverage badges")
   check(page.locator(".mlb-charts .panel").count()==2,f"{width} Most Watched Teams and Attendance by Year charts")
   fits("MLB overview")
   visit("mlb/game.html?id=94","document.querySelector('#gameStats #box tbody tr')!==null")
   check(page.locator("#gameSelect option").count()==131,f"{width} game selector lists all 131")
   check("Colorado Rockies" in page.locator("#scoreboard").inner_text(),f"{width} first doubleheader game loaded")
   check(page.locator("#scoreboard #pitchingDecisions").count()==1 and page.locator("#scoreboard #playerOfGame").count()==1,
         f"{width} official decisions and one Player of the Game appear immediately beneath score")
   check(page.locator("#scoreboard > section#pitchingDecisions + section#playerOfGame").count()==1,
         f"{width} W/L/Save section appears before Player of the Game")
   check(page.locator("#pitchingDecisions [data-decision]").count()==3,
         f"{width} three labeled W/L/Save decisions show for each game")
   check("Yu Darvish" in page.locator('#pitchingDecisions [data-decision="winner"]').inner_text() and
         "Jake Bird" in page.locator('#pitchingDecisions [data-decision="loser"]').inner_text(),
         f"{width} first doubleheader official winning/losing pitchers match MLB")
   check("No save" in page.locator('#pitchingDecisions [data-decision="save"]').inner_text(),
         f"{width} official no-save game displays No save, not a guessed reliever")
   check(page.locator("#playerOfGame .mlb-potg-info h3").count()==1,
         f"{width} exactly one Player of the Game, no hitter/pitcher split")
   check(page.locator("#playerOfGame .mlb-potg-impact strong").count()==1 and
         float(page.locator("#playerOfGame .mlb-potg-impact strong").inner_text())>0,
         f"{width} single comparable hitter/pitcher Impact Score displayed")
   result=page.evaluate("""async()=>{const d=await MLBArchive.load();const by=new Map();for(const r of d.rows){if(!by.has(r.game_pk))by.set(r.game_pk,[]);by.get(r.game_pk).push(r)}
     const winners=d.games.map(g=>MLBArchive.playerOfGame(by.get(g.game_pk)||[]));
     return {count:winners.filter(Boolean).length,names:winners.filter(Boolean).map(w=>w.row.player_id),
       nonfinite:winners.filter(Boolean).some(w=>!Number.isFinite(w.score)),
       pitching:winners.filter(Boolean).filter(w=>w.role==="Pitching").length,
       batting:winners.filter(Boolean).filter(w=>w.role==="Batting").length};}""")
   check(result["count"]==131 and not result["nonfinite"] and len(result["names"])==131,
         f"{width} every imported game identifies one finite-scoring Player of the Game")
   check(result["pitching"]>0 and result["batting"]>0,
         f"{width} unified impact model can award either pitcher or hitter")
   check(page.locator("#box .mlb-team-box").count()==2,f"{width} batting score splits two teams")
   check(page.locator("#box .mlb-team-box").evaluate_all("(xs)=>xs.map(e=>e.dataset.side)")==["away","home"],
         f"{width} away lineup appears before home lineup")
   check("Colorado Rockies" in page.locator('#box .mlb-team-box[data-side="away"] h3').inner_text(),
         f"{width} away batting lineup properly labeled")
   check("San Diego Padres" in page.locator('#box .mlb-team-box[data-side="home"] h3').inner_text(),
         f"{width} home batting lineup properly labeled")
   for side in ("away","home"):
    headings=page.locator(f'#box .mlb-team-box[data-side="{side}"] thead th').all_text_contents()
    check([x.strip() for x in headings[:2]]==["Order","Player"],
          f"{width} {side} batting order column is immediately left of player name")
    display=page.locator(f'#box .mlb-team-box[data-side="{side}"] .mlb-lineup-row').evaluate_all(
     "(xs)=>xs.map(x=>({slot:x.dataset.slot,sub:x.dataset.sub,order:x.querySelector('td:first-child').textContent.trim(),player:x.querySelector('td:nth-child(2) a')?.textContent.trim()}))")
    check(all(d["order"]==("↳" if int(d["sub"])>0 else d["slot"]) for d in display if d["slot"]!="—"),
          f"{width} {side} lineup numbers are in left column and substitutions use an arrow")
    check(all(d["player"] for d in display),f"{width} {side} player names are in second column")
   for side in ("away","home"):
    spots=page.locator(f'#box .mlb-team-box[data-side="{side}"] .mlb-lineup-row[data-slot]').evaluate_all(
     "(xs)=>xs.map(x=>Number(x.dataset.slot)).filter(Number.isInteger).filter(x=>x>=1&&x<=9)")
    check(len(set(spots))==9 and spots==sorted(spots),
          f"{width} {side} team batting order runs 1 through 9 with substitutions in their parent slots")
    ids=page.locator(f'#box .mlb-team-box[data-side="{side}"] .mlb-lineup-row').evaluate_all(
     "(xs)=>xs.map(x=>Number(x.dataset.playerId))")
    check(all(any(r["player_id"]==id and r["game_pk"]==662250 and r["side"]==side for r in rows) for id in ids),
          f"{width} {side} lineup cannot contain opponents")
   page.locator("#gameSelect").select_option("95")
   check("Josh Hader" in page.locator('#pitchingDecisions [data-decision="winner"]').inner_text() and
         "Alex Colomé" in page.locator('#pitchingDecisions [data-decision="loser"]').inner_text(),
         f"{width} decisions refresh correctly when switching games")
   check(page.locator("#playerOfGame .mlb-potg-info h3").count()==1,
         f"{width} one fresh Player of the Game when switching doubleheader games")
   saved=next(g for g in games if decisions[str(g["game_pk"])].get("save"))
   page.locator("#gameSelect").select_option(str(saved["attendance_id"]))
   check(decisions[str(saved["game_pk"])]["save"]["name"] in page.locator('#pitchingDecisions [data-decision="save"]').inner_text(),
         f"{width} saved games display official credited save pitcher")
   page.locator("#gameSelect").select_option("95")
   check(page.locator("#box .mlb-team-box").count()==2,
         f"{width} both team batting lineups stay separated when switching doubleheader games")
   check(page.locator("#scoreboard").count()==1 and "San Diego Padres" in page.locator("#scoreboard").inner_text(),f"{width} second doubleheader selectable")
   page.locator("#gameStats [data-cat='pitching']").click()
   check(page.locator("#box tbody tr").count()>5,f"{width} pitching player lines")
   check(page.locator("#box .mlb-team-box").count()==2,f"{width} pitchers grouped by club")
   for side in ("away","home"):
    table_root=f'#box .mlb-team-box[data-side="{side}"]'
    headings=page.locator(table_root+" thead th").all_text_contents()
    check([x.strip() for x in headings[:2]]==["Order","Player"],
          f"{width} {side} pitching order column appears left of player names")
    displayed=page.locator(table_root+" .mlb-lineup-row").evaluate_all(
     "(xs)=>xs.map(x=>({index:x.dataset.pitcherIndex,order:x.querySelector('td:first-child').textContent.trim(),name:x.querySelector('td:nth-child(2) a')?.textContent.trim()}))")
    check(len(displayed)>=1 and displayed[0]["order"]=="1",
          f"{width} {side} starting pitcher is numbered 1")
    check(all(d["order"]==(str(int(d["index"])+1) if d["index"] else "—") and d["name"] for d in displayed),
          f"{width} {side} pitchers follow official appearance order with number to left")
    check([int(d["index"]) for d in displayed if d["index"]]==sorted(int(d["index"]) for d in displayed if d["index"]),
          f"{width} {side} pitcher order ascending without alphabetization")
   page.locator("#gameStats [data-cat='fielding']").click()
   check(page.locator("#box tbody tr").count()>5,f"{width} individual fielding lines")
   check(page.locator("#box .mlb-team-box").count()==2,f"{width} fielding also separated into two teams")
   check([x.strip() for x in page.locator('#box .mlb-team-box[data-side="away"] thead th').all_text_contents()][:1]==["Player"],
         f"{width} fielding layout remains unchanged")
   page.locator("#gameStats [data-cat='batting']").click()
   sub_game=next((r["attendance_id"] for r in rows if r.get("batting_sub_index") is not None and r["batting_sub_index"]>0),None)
   if sub_game:
    page.locator("#gameSelect").select_option(str(sub_game))
    check(page.locator("#box .mlb-substitute").count()>0,
          f"{width} substitutes appear indented beneath their original lineup spots")
    check(all(x=="↳" for x in page.locator("#box .mlb-substitute td:first-child").all_text_contents()),
          f"{width} replacement arrows appear in lineup order column")
    for side in ("away","home"):
     slots=page.locator(f'#box .mlb-team-box[data-side="{side}"] .mlb-lineup-row[data-slot]').evaluate_all(
      "(xs)=>xs.map(x=>Number(x.dataset.slot)).filter(x=>x>=1&&x<=9)")
     check(slots==sorted(slots),f"{width} replacement batters remain nested in order")
   fits("MLB game")
   visit("mlb/stats.html","document.querySelector('#board tbody tr')!==null")
   check(page.locator("#board tbody tr").count()>=15,f"{width} batting leaderboards loaded")
   page.locator("#category").select_option("pitching")
   check(page.locator("#board tbody tr").count()>=15,f"{width} pitching leaderboards loaded")
   fits("MLB players")
   visit("mlb/hall-of-fame.html","document.querySelectorAll('#hofGrid .mlb-hof-card').length===21")
   check(page.locator('nav a[href="./hall-of-fame.html"]').count()==1,f"{width} Hall of Fame nav immediately follows Players")
   check(page.locator("#hofGrid .mlb-hof-card").count()==len(hall_ids),f"{width} all inducted players seen have legend cards")
   check(page.locator("#hofShowing").inner_text().startswith("Showing 21"),f"{width} Hall of Fame page reports precise inducted count")
   check(page.locator(".mlb-hof-summary .metric").count()==3,f"{width} NBA/NFL-style three Hall of Fame summary metrics")
   check("Class of" in page.locator("#hofGrid .mlb-hof-card").first.inner_text(),f"{width} Hall of Fame class year on every card")
   check(page.locator(".mlb-hof-card .mlb-hof-games a").count()>=21,f"{width} witnessed games linked from Hall of Fame cards")
   hof_id=hall_ids[0]
   hof_player=next(r["name"] for r in rows if str(r["player_id"])==hof_id)
   page.locator("#hofSearch").fill(hof_player)
   check(page.locator("#hofGrid .mlb-hof-card").count()==1,f"{width} Hall of Fame player search narrows list")
   page.locator("#hofSearch").fill("")
   page.locator("#hofSort").select_option("year")
   check(page.locator("#hofGrid .mlb-hof-card").count()==21,f"{width} Hall of Fame sort retains every inducted player")
   fits("Hall of Fame page")
   visit(f"mlb/player.html?id={hof_id}","document.querySelector('.mlb-profile-head')!==null")
   check(page.locator('.mlb-profile-hero .mlb-profile-badge.hof').count()==1,f"{width} gold Hall of Fame badge sits inside player hero")
   check(page.locator(".mlb-profile-headline-stats .mlb-profile-stat").count()==6,f"{width} six matching top stats on Hall of Fame profile")
   check(page.locator("#profileTabs .mlb-profile-tab").count()==4,f"{width} awards coexist with NBA-style profile navigation")
   check(page.locator('#honorTabs [data-honor="hall_of_fame"]').count()==1,f"{width} Hall of Fame career tab exists")
   check(str(honored[hof_id]["hall_of_fame"]["year"]) in page.locator('#honor-hall_of_fame').inner_text(),
         f"{width} inducted class year appears on player profile")
   check(page.locator('#honorTabs [data-honor]').count()==5,f"{width} five honors tabs include MVP Cy Young Gold Glove Silver Slugger")
   for category in ("mvp","cy_young","gold_glove","silver_slugger"):
    chosen=next(pid for pid,p in honored.items() if p.get(category))
    visit(f"mlb/player.html?id={chosen}","document.querySelector('.mlb-profile-head')!==null")
    check(page.locator(f'.mlb-profile-hero [data-honor-link="{category}"]').count()==1,f"{width} colored {category} achievement badge is inside player card")
    check(page.locator(f'.mlb-profile-hero [data-honor-link="{category}"]').evaluate("(el)=>getComputedStyle(el).backgroundColor")!="rgba(0, 0, 0, 0)",
          f"{width} {category} badge has distinct background")
    check(page.locator(f'#honorTabs [data-honor="{category}"]').count()==1,
          f"{width} colored {category} award-history tab exists")
    page.locator(f'#honorTabs [data-honor="{category}"]').click()
    check(page.locator(f'#honor-{category}').is_visible(),f"{width} {category} tab opens verified award years")
    page.locator(f'.mlb-profile-hero [data-honor-link="{category}"]').click()
    check(page.locator("#profile-overview").is_visible() and page.locator(f'#honor-{category}').is_visible(),
          f"{width} {category} hero badge switches to corresponding honor details")
    check(str(honored[chosen][category][0]["year"]) in page.locator(f'#honor-{category}').inner_text(),
          f"{width} {category} year is shown from official record")
   fits("MLB awarded player")
   example=rows[0]
   visit(f"mlb/player.html?id={example['player_id']}","document.querySelector('.mlb-profile-head')!==null")
   check(example["name"] in page.locator(".mlb-profile-head").inner_text(),f"{width} MLB-ID player profile")
   check(page.locator(".mlb-profile-hero").count()==1,f"{width} NBA-inspired framed player hero")
   check(page.locator(".mlb-profile-photo img").count()==1,f"{width} portrait inside player card")
   check(page.locator(".mlb-profile-headline-stats .mlb-profile-stat").count()==6,f"{width} six compact profile stats match NBA layout")
   geometry=page.evaluate("""() => {
     const css=x=>getComputedStyle(document.querySelector(x));
     const dimensions=x=>{const r=document.querySelector(x).getBoundingClientRect();return {width:r.width,height:r.height}};
     return {
       hero:dimensions('.mlb-profile-hero'),photo:dimensions('.mlb-profile-photo'),
       heroDirection:css('.mlb-profile-hero').flexDirection,
       heroPadding:css('.mlb-profile-hero').paddingTop,
       heroGap:css('.mlb-profile-hero').columnGap,
       heroRadius:css('.mlb-profile-hero').borderTopLeftRadius,
       statPadding:css('.mlb-profile-stat').paddingTop,
       statRadius:css('.mlb-profile-stat').borderTopLeftRadius,
       statsGap:css('.mlb-profile-headline-stats').columnGap,
       cardPositions:[...document.querySelectorAll('.mlb-profile-stat')].map(x=>Math.round(x.getBoundingClientRect().top)),
       tabPadding:css('.mlb-profile-tab').paddingLeft,
       contentWidth:dimensions('main').width
     };
   }""")
   check(geometry["heroRadius"]=="19px" and geometry["statRadius"]=="14px",
         f"{width} frame and stat-card radii exactly match NBA's 19px and 14px")
   check(geometry["statsGap"]=="11px",
         f"{width} six stat cards use NBA's 11px spacing")
   check(geometry["tabPadding"]=="16px",
         f"{width} Overview/Advanced/Game Log/Milestones buttons use NBA padding")
   if width>550:
    check(geometry["heroDirection"]=="row" and geometry["heroPadding"]=="26px" and geometry["heroGap"]=="27px",
          f"{width} NBA player-hero horizontal layout, 26px padding and 27px gap")
    check(abs(geometry["photo"]["width"]-145)<1 and abs(geometry["photo"]["height"]-180)<1,
          f"{width} NBA portrait geometry 145 by 180 pixels")
    check(geometry["statPadding"]=="18px" and len(set(geometry["cardPositions"]))==1,
          f"{width} six stat tiles in one row with 18px NBA padding")
   else:
    check(geometry["heroDirection"]=="column" and geometry["heroPadding"]=="18px",
          f"{width} NBA-style mobile stacked player hero")
    check(abs(geometry["photo"]["width"]-125)<1 and abs(geometry["photo"]["height"]-150)<1,
          f"{width} NBA mobile portrait geometry 125 by 150 pixels")
    check(geometry["statPadding"]=="12px" and len(set(geometry["cardPositions"]))==3,
          f"{width} NBA mobile layout has two compact stat cards per row")
   check(page.locator("#profileTabs [role=tab]").count()==4,f"{width} four NBA-style profile tabs")
   check(page.locator("#profile-overview").is_visible(),f"{width} Overview default panel visible")
   page.locator('#profileTabs [data-profile-tab="advanced"]').click()
   check(page.locator("#profile-advanced").is_visible() and not page.locator("#profile-overview").is_visible(),
         f"{width} Advanced player rates appear on selected tab")
   page.locator('#profileTabs [data-profile-tab="milestones"]').click()
   check(page.locator("#profile-milestones").is_visible() and page.locator("#profile-milestones .mlb-profile-total").count()>=6,
         f"{width} witnessed single-game milestones accessible")
   page.locator('#profileTabs [data-profile-tab="games"]').click()
   check(page.locator("#profile-games").is_visible(),f"{width} Game Log tab opens")
   check(page.locator("#logs tbody tr").count()>=1,f"{width} individual game log")
   fits("MLB player")
   visit("mlb/records.html","document.querySelector('#recordCards .mlb-record')!==null")
   check(page.locator("#mainTabs [role=tab]").count()==4,f"{width} four NBA/NFL Records tabs")
   check(page.locator("#recordCards .mlb-record").count()==6,f"{width} six MLB record holder cards")
   check(page.locator("#recordTop tbody tr").count()>=1,f"{width} single-game Top 10 records")
   page.locator("#mainTabs [data-tab='milestones']").click()
   check(page.locator("#milestoneTable tbody tr").count()>=1,f"{width} player-game milestones")
   page.locator("#milestoneView").select_option("players")
   check(page.locator("#milestoneTable tbody tr").count()>=1,f"{width} milestone frequency leaderboard")
   page.locator("#mainTabs [data-tab='teams']").click()
   check(page.locator("#teamCards .mlb-record").count()==6,f"{width} team and game record cards")
   page.locator("#mainTabs [data-tab='legendary']").click()
   check(page.locator("#feats").count()==1 and page.locator("#moments tbody tr").count()>=1,f"{width} legendary performance panels")
   fits("MLB records")
   visit("index.html","document.getElementById('allGames').textContent==='267'")
   check(page.locator(".sport-card").count()==6,f"{width} sixth sports archive card")
   fits("main portal")
   page.close()
  browser.close()
finally:server.shutdown()
print("PASS MLB 131-game data and browser regression")
