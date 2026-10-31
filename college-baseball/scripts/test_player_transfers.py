#!/usr/bin/env python3
"""Verify attendee-proposed transferred players against original official rows;
browser-test unified profiles, old deep links, game attribution, and restricted IDs.
"""
from pathlib import Path
from collections import defaultdict
from functools import partial
from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler
from threading import Thread
from urllib.parse import quote
import json
import sys

ROOT=Path(__file__).resolve().parents[2]
DATA=ROOT/"college-baseball"/"data"
sys.path.insert(0,str(ROOT/"college-baseball"/"scripts"))
from reconcile_player_identities import name,school

def check(cond,message):
    if not cond:raise AssertionError(message)

rules=json.loads((DATA/"player_identity_merges.json").read_text())
audit=json.loads((DATA/"player_identity_reconciliation_audit.json").read_text())
cross=json.loads((DATA/"player_identity_crosswalk.json").read_text())
original=json.loads((DATA/"player_stats.json").read_text())
games=json.loads((DATA/"games.json").read_text())
check(len(games)==444 and len(original)==13183 and len(rules["rules"])==rules["expected_proposals"]==100,
      "Protected college attendance or original official player rows changed")
check(audit["ready_merges"]==96 and audit["not_ready"]==4 and
      cross["requested_person_merges"]==100 and
      cross["activated_person_merges"]==97 and cross["pending_person_merges"]==3,
      "97 of 100 owner-nominated identities linked, including the Tyler Pitzer school transfer and source-name alias")
check({x["name"] for x in audit["preview"] if x["status"]!="merge_ready"}==
      {"Tate Soderstrom","Ethan Lizama","Kyle Hvidsten","Michael Graziano"},
      "Original-row audit should still document the four former source exceptions")
check(len(cross["merges"])==97 and len({m["canonical_id"] for m in cross["merges"]})==97,
      "Missing or duplicate canonical identities")
source_by_key=defaultdict(list)
for r in original:
    source_by_key[(r["team"],r["player_id"])].append(r)
# The preserved raw import lacks Graziano's Georgia Tech appearance because
# worksheet attendance #268 originally pointed to the wrong April 14 game.
# The official April 13 correction now supplies that exact missing school side.
corrections=json.loads((DATA/"attendance_game_corrections.json").read_text())["games"]
game_correction=next(g for g in corrections if g["replaces_game_id"]==
                     "cb-2024-04-14-virginia-tech-georgia-tech-att0268")
graziano=[x for x in game_correction["batting"]["Georgia Tech"] if x[1]=="Michael Graziano"]
check(len(graziano)==1 and game_correction["game"]["date"]=="2024-04-13" and
      game_correction["game"]["home_score"]==19 and
      game_correction["source_url"].endswith("gt041324.pdf"),
      "Official corrected gamebook must establish Michael Graziano at Georgia Tech")
corrected_graziano={"game_id":game_correction["game"]["id"],
                   "team":"Georgia Tech", "player":"Michael Graziano",
                   "player_id":"cb-georgia-tech-michael-graziano"}
source_by_key[(corrected_graziano["team"],corrected_graziano["player_id"])].append(corrected_graziano)
mapped={}
used_ids=set()
for m in cross["merges"]:
    check(len(m["source_player_ids"])==(3 if m["name"]=="Tyler Pitzer" else 2) and
          m["canonical_id"]==m["source_player_ids"][0],
          "Canonical ID must preserve first-school source profile URL")
    rule=next(x for x in rules["rules"] if name(x["name"])==name(m["name"]))
    aliases={a["source_player_id"]:a for a in rule.get("source_aliases",[])}
    allowed_schools={school(t) for t in rule["schools"]}
    pairs={(x["team"],x["source_player_id"]) for x in m["pairs"]}
    matched=[r for t,i in pairs for r in source_by_key[(t,i)]]
    check(len(pairs)==len(m["source_player_ids"]) and len(matched)==m["source_rows"] and len(matched)>1,
          "Both exact source player identities must be present")
    for t,i in pairs:
        check(school(t) in allowed_schools and
              all(name(r["player"])==name(rule["name"]) or
                  (i in aliases and r["player"]==aliases[i]["source_player_name"] and
                   r["game_id"]==aliases[i]["game_id"] and r["team"]==aliases[i]["team"])
                  for r in source_by_key[(t,i)]),
              "Owner name and school gate failed")
        check((t,i) not in mapped and i not in used_ids, "Double-booked source player ID")
        mapped[(t,i)]=m["canonical_id"]
        used_ids.add(i)
# Hard-stop against accidental general name matching for similar people.
for withheld in ("Dylan Johnson","Tanner Smith"):
    m=next(x for x in cross["merges"] if x["name"]==withheld)
    expected=({"Fresno State","Gonzaga"} if withheld=="Dylan Johnson" else {"Oregon State","Miami"})
    check(set(m["schools"])==expected and
          all(school(pair["team"]) in {school(t) for t in expected} for pair in m["pairs"]),
          "Explicit name collision school exclusion breached")
# The identity test includes the one newly sourced Georgia Tech school-side row;
# the 13,183 protected original records remain immutable.
effective=original+[corrected_graziano]
unified=[(r["game_id"],mapped.get((r["team"],r["player_id"]),r["player_id"])) for r in effective]
check(len(set(unified))==len(effective),"Two identities collided in the same attended game")
before=len({r["player_id"] for r in effective})
after=len({p for _,p in unified})
check(before-after==sum(len(m["source_player_ids"])-1 for m in cross["merges"]),
      "Only owner-approved source identities may collapse, including the scoped Pitzer shorthand")
print(json.dumps({"source_records_preserved":len(original),"verified_owner_proposals":cross["activated_person_merges"],
      "left_pending":cross["pending_person_merges"],"before_unique_players":before,"after_unique_players":after,
      "source_college_games":len(games)},indent=2))

# Existing JS page has full crosswalk logic. Smoke-test its behavior in Chromium.
try:
    from playwright.sync_api import sync_playwright
except ImportError:
    raise SystemExit("Browser QA needs Playwright and Chromium, installed in project CI")

class Silent(SimpleHTTPRequestHandler):
    def log_message(self,*args):
        pass

server=ThreadingHTTPServer(("127.0.0.1",0),
                           partial(Silent,directory=str(ROOT)))
thread=Thread(target=server.serve_forever,daemon=True)
thread.start()
base=f"http://127.0.0.1:{server.server_port}/college-baseball"
cases=[
    ("Justin DeCriscio",["San Diego","NC State"],80),
    ("Gavin Kilen",["Louisville","Tennessee"],7),
    ("Dylan Johnson",["Fresno State","Gonzaga"],11),
    ("Tanner Smith",["Oregon State","Miami"],2),
    ("Dalton Bargo",["Tennessee","NC State"],8),
    ("Andrew Wiggins",["Indiana","NC State"],3),
    ("Michael Graziano",["Georgia Tech","Mercer"],2),
    ("Michael O'Shaughnessy",["Davidson","Georgia"],3),
    ("Tyler Pitzer",["South Carolina","Mississippi State"],5),
]
try:
    with sync_playwright() as pw:
        browser=pw.chromium.launch()
        page=browser.new_page(viewport={"width":1100,"height":850})
        for who,schools,games_expected in cases:
            match=next(x for x in cross["merges"] if x.get("display_name",x["name"])==who)
            source_id=match["source_player_ids"][1] # formerly independent school
            page.goto(base+"/player.html?id="+quote(source_id),wait_until="domcontentloaded")
            page.locator(".cb-profile-hero").wait_for(timeout=35000)
            check(page.locator(".cb-profile-hero h1").inner_text()==who,
                  "Former second-school deep link did not resolve to unified "+who)
            display=page.locator(".mlb-profile-team-name").inner_text()
            check(all(s.casefold() in display.casefold() for s in schools),
                  "Player profile does not show both user-confirmed schools: "+who+" "+display)
            check(page.locator(".cb-player-game-log tbody tr").count()==games_expected,
                  "Witnessed game logs do not combine source rows for "+who)
            print("PASS unified old-school deep link",who,display,games_expected)
        page.goto(base+"/player.html?id="+quote("cb-south-carolina-pitzer"),wait_until="domcontentloaded")
        page.locator(".cb-profile-hero").wait_for(timeout=35000)
        check(page.locator(".cb-profile-hero h1").inner_text()=="Tyler Pitzer" and
              page.locator(".cb-player-game-log tbody tr").count()==5,
              "Abbreviated South Carolina Pitzer deep link resolves to all five attended games")
        # Three still-deferred players remain at their old, single-school URLs.
        page.goto(base+"/player.html?id="+quote("cb-uc-san-diego-tate-soderstrom"),wait_until="domcontentloaded")
        page.locator(".cb-profile-hero").wait_for(timeout=35000)
        check(page.locator(".mlb-profile-team-name").inner_text().casefold()=="uc san diego",
              "One-school-only proposal incorrectly merged an unobserved Arizona profile")
        page.goto(base+"/stats.html",wait_until="domcontentloaded")
        page.locator("#cb-player-board .cb-table").wait_for(timeout=35000)
        for who,schools in [("Justin DeCriscio",["San Diego","NC State"]),
                            ("Dalton Bargo",["Tennessee","NC State"]),
                            ("Andrew Wiggins",["Indiana","NC State"]),
                            ("Michael O'Shaughnessy",["Davidson","Georgia"]),
                            ("Tyler Pitzer",["South Carolina","Mississippi State"])]:
            page.locator("#cb-player-search").fill(who)
            page.wait_for_timeout(250)
            board=page.locator("#cb-player-board")
            check(board.locator("tbody tr").count()==1 and
                  all(s.casefold() in board.inner_text().casefold() for s in schools),
                  "Unified career player leaderboard contains split or missing entries for "+who)
        browser.close()
finally:
    server.shutdown()
    thread.join(timeout=5)
print("PASS 97 scoped transfer profiles, redirects, leaderboards, exclusion rules and original official boxscore data")
