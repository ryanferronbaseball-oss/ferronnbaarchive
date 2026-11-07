#!/usr/bin/env python3
"""Browser and data acceptance checks for verified W/L/S on all 112 MiLB games."""
import collections
import functools
import http.server
import json
import pathlib
import socketserver
import threading
from playwright.sync_api import sync_playwright

ROOT=pathlib.Path(__file__).resolve().parents[2]
D=ROOT/"milb"/"data"
games=json.loads((D/"games.json").read_text())
rows=json.loads((D/"player_stats.json").read_text())
decisions=json.loads((D/"pitching_decisions.json").read_text())
audit=json.loads((D/"pitching_decisions_audit.json").read_text())
report=json.loads((D/"game_detail_report.json").read_text())
assert len(games)==112
assert len(decisions)==112
assert audit["games_checked"]==112
assert audit["games_with_verified_win"]==112
assert audit["games_with_verified_loss"]==112
assert audit["all_w_l_sv_internally_consistent"] is True
assert report["pitching_decisions_verified"]==112
assert all(x.get("decision_status")=="verified" for x in report["games"])
byGame=collections.defaultdict(list)
byPerson=collections.defaultdict(lambda:{"w":0,"l":0,"sv":0})
for r in rows:
 byGame[r["game_id"]].append(r)
 if r.get("pitching") is not None:
  p=r["pitching"]
  assert all(p.get(key) in (0,1) for key in ["w","l","sv"])
  assert sum(p[key] for key in ["w","l","sv"])<=1
  for key in ["w","l","sv"]:byPerson[r["player_id"]][key]+=p[key]
assert sum(x["w"] for x in byPerson.values())==112
assert sum(x["l"] for x in byPerson.values())==112
assert sum(x["sv"] for x in byPerson.values())==audit["games_with_verified_save"]
assert audit["games_with_verified_save"]+audit["games_without_save"]==112
for g in games:
 d=decisions[str(g["source_game_id"])]
 assert d["status"]=="verified" and d["winner"] and d["loser"]
 if d["save"]: assert d["save"]["id"]!=d["winner"]["id"]
 pitchers=[r for r in byGame[g["id"]] if r.get("pitching") is not None]
 for key,flag in [("winner","w"),("loser","l"),("save","sv")]:
  credited=[r for r in pitchers if r["pitching"][flag]==1]
  expected=d[key]
  assert len(credited)==(1 if expected else 0),(g["id"],flag)
  if credited:assert credited[0]["player_id"]==expected["id"],(g["id"],flag)
class Reuse(socketserver.ThreadingTCPServer):allow_reuse_address=True
server=Reuse(("127.0.0.1",0),functools.partial(http.server.SimpleHTTPRequestHandler,directory=str(ROOT)))
threading.Thread(target=server.serve_forever,daemon=True).start()
origin=f"http://127.0.0.1:{server.server_address[1]}"
try:
 with sync_playwright() as p:
  browser=p.chromium.launch(headless=True)
  # Across years, official status and names must appear on the game page.
  samples=[next(g for g in games if g["date"]==day)
      for day in ("2014-05-24","2015-08-02","2021-06-08","2022-07-02","2024-05-10")]
  for g in samples:
   page=browser.new_page(viewport={"width":1360,"height":900})
   jsErrors=[];network=[]
   page.on("pageerror",lambda e:jsErrors.append(str(e)))
   page.on("request",lambda r:network.append(r.url))
   page.goto(origin+"/milb/game.html?id="+g["id"],wait_until="networkidle",timeout=50000)
   d=decisions[str(g["source_game_id"])]
   for name in ("winner","loser"):
    pid=str(d[name]["id"])
    node=page.locator('#pitchingDecisions [data-decision="'+name+'"] a')
    assert node.count()==1,(g["id"],name)
    assert node.get_attribute("href")=="./player.html?id="+pid
    assert d[name]["name"] in node.inner_text(),(g["id"],name)
   save=page.locator('#pitchingDecisions [data-decision="save"]')
   if d["save"]:
    assert save.locator("a").count()==1
    assert save.locator("a").get_attribute("href")=="./player.html?id="+str(d["save"]["id"])
   else:
    assert save.locator("a").count()==0
    assert "No save" in save.inner_text()
   page.locator('[data-cat="pitching"]').click()
   header=page.locator("#box table thead").first.inner_text()
   assert all(x in header.split() for x in ("W","L","SV")),header
   assert page.locator("#box .mlb-lineup-row").count()>=2
   assert not jsErrors,jsErrors
   assert not any("/mlb/data/" in url or "/college-baseball/data/" in url for url in network)
   page.close()
  # Any pitcher with verified wins can see the awards in both totals and game logs.
  topId=max(byPerson,key=lambda pid:byPerson[pid]["w"])
  top=byPerson[topId]
  assert top["w"]>0
  profile=browser.new_page(viewport={"width":1360,"height":900})
  errors=[];profile.on("pageerror",lambda e:errors.append(str(e)))
  profile.goto(origin+"/milb/player.html?id="+str(topId),wait_until="networkidle")
  text=profile.locator("#profile-overview").inner_text()
  assert "Wins" in text and "Losses" in text and "Saves" in text
  assert "W–L" in profile.locator(".mlb-profile-headline-stats").inner_text()
  profile.locator('[data-profile-tab="games"]').click()
  profile.locator('[data-side="pitching"]').click()
  headers=profile.locator("#logs thead").inner_text()
  assert "W" in headers and "L" in headers and "SV" in headers
  assert not errors,errors
  profile.close()
  # Leaderboards show actual counting categories and don't mix MLB totals.
  players=browser.new_page(viewport={"width":1280,"height":820})
  requests=[];errors=[]
  players.on("request",lambda r:requests.append(r.url))
  players.on("pageerror",lambda e:errors.append(str(e)))
  players.goto(origin+"/milb/stats.html",wait_until="networkidle")
  players.locator("#category").select_option("pitching")
  choices=[e.get_attribute("value") for e in players.locator("#stat option").all()]
  assert all(s in choices for s in ("wins","losses","saves")),choices
  for category,maximum in (("wins",max(x["w"] for x in byPerson.values())),
                           ("losses",max(x["l"] for x in byPerson.values())),
                           ("saves",max(x["sv"] for x in byPerson.values()))):
   players.locator("#stat").select_option(category)
   assert category.capitalize() in players.locator("#boardHeading").inner_text()
   if maximum>0:
    table=players.locator("#board tbody tr")
    assert table.count()>0,(category,maximum)
    assert str(maximum)==table.first.locator("strong").inner_text(),(category,maximum,table.first.inner_text())
  assert not any("/mlb/data/" in url or "/college-baseball/data/" in url for url in requests)
  assert not errors,errors
  mobile=browser.new_page(viewport={"width":390,"height":844},is_mobile=True,has_touch=True)
  mobile.goto(origin+"/milb/game.html?id="+samples[2]["id"],wait_until="networkidle")
  assert mobile.locator("#pitchingDecisions [data-decision]").count()==3
  mobile.locator('[data-cat="pitching"]').click()
  assert "SV" in mobile.locator("#box thead").first.inner_text()
  browser.close()
 print("PASS: all 112 official W/L/S, player totals, game decision cards, pitching lines, profiles and leaderboards")
finally:
 server.shutdown()
 server.server_close()
