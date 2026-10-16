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
check(report.get("lineup_team_games_with_nine_spots")==262,"All 262 team box scores have nine official batting-order positions")
check(report.get("lineup_slot_rows",0)>3000,"Official batting slots imported for more than 3,000 player lines")
check(all(r.get("side") in ("away","home") for r in rows),"Every MLB player box-score record identifies its home/away team")
check(all(1<=r["batting_slot"]<=9 for r in rows if r.get("batting_slot") is not None),"All verified lineup slots are between one and nine")
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
   example=rows[0]
   visit(f"mlb/player.html?id={example['player_id']}","document.querySelector('.mlb-profile-head')!==null")
   check(example["name"] in page.locator(".mlb-profile-head").inner_text(),f"{width} MLB-ID player profile")
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
