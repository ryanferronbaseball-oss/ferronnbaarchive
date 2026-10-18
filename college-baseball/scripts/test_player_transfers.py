#!/usr/bin/env python3
"""Verify 96 attendee-proposed transferred players against original official rows;
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
check(len(games)==444 and len(original)==13183 and len(rules["rules"])==96,
      "Protected college attendance or original official player rows changed")
check(audit["ready_merges"]==92 and audit["not_ready"]==4 and
      cross["activated_person_merges"]==92 and cross["pending_person_merges"]==4,
      "Only 92 identities supported by current 96 owner-nominated school pairs")
check({x["name"] for x in audit["preview"] if x["status"]!="merge_ready"}==
      {"Tate Soderstrom","Ethan Lizama","Kyle Hvidsten","Michael Graziano"},
      "Unexpected four school-side source exceptions")
check(len(cross["merges"])==92 and len({m["canonical_id"] for m in cross["merges"]})==92,
      "Missing or duplicate canonical identities")
source_by_key=defaultdict(list)
for r in original:
    source_by_key[(r["team"],r["player_id"])].append(r)
mapped={}
used_ids=set()
for m in cross["merges"]:
    check(len(m["source_player_ids"])==2 and
          m["canonical_id"]==m["source_player_ids"][0],
          "Canonical ID must preserve first-school source profile URL")
    rule=next(x for x in rules["rules"] if name(x["name"])==name(m["name"]))
    allowed_schools={school(t) for t in rule["schools"]}
    pairs={(x["team"],x["source_player_id"]) for x in m["pairs"]}
    matched=[r for t,i in pairs for r in source_by_key[(t,i)]]
    check(len(pairs)==2 and len(matched)==m["source_rows"] and len(matched)>1,
          "Both exact source player identities must be present")
    for t,i in pairs:
        check(school(t) in allowed_schools and
              all(name(r["player"])==name(rule["name"]) for r in source_by_key[(t,i)]),
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
# Simulate the browser alias transform and require the entire 13,183 original lines
# to remain present, with no duplicate canonical person-game IDs.
unified=[(r["game_id"],mapped.get((r["team"],r["player_id"]),r["player_id"])) for r in original]
check(len(set(unified))==len(original),"Two identities collided in the same attended game")
before=len({r["player_id"] for r in original})
after=len({p for _,p in unified})
check(before-after==92,"Exactly one unique player identity should collapse per approved pair")
print(json.dumps({"source_records_preserved":len(original),"verified_owner_proposals":92,
      "left_pending":4,"before_unique_players":before,"after_unique_players":after,
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
]
try:
    with sync_playwright() as pw:
        browser=pw.chromium.launch()
        page=browser.new_page(viewport={"width":1100,"height":850})
        for who,schools,games_expected in cases:
            match=next(x for x in cross["merges"] if x["name"]==who)
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
        # Four deferred players remain at their old, single-school URL.
        page.goto(base+"/player.html?id="+quote("cb-uc-san-diego-tate-soderstrom"),wait_until="domcontentloaded")
        page.locator(".cb-profile-hero").wait_for(timeout=35000)
        check(page.locator(".mlb-profile-team-name").inner_text().casefold()=="uc san diego",
              "One-school-only proposal incorrectly merged an unobserved Arizona profile")
        page.goto(base+"/stats.html",wait_until="domcontentloaded")
        page.locator("#cb-player-board .cb-table").wait_for(timeout=35000)
        page.locator("#cb-player-search").fill("Justin DeCriscio")
        page.wait_for_timeout(250)
        check(page.locator("#cb-player-board tbody tr").count()==1 and
              "san diego" in page.locator("#cb-player-board").inner_text().casefold() and
              "nc state" in page.locator("#cb-player-board").inner_text().casefold(),
              "Unified career player leaderboard still contains separate Justin DeCriscio entries")
        browser.close()
finally:
    server.shutdown()
    thread.join(timeout=5)
print("PASS 92 scoped transfer profiles, redirects, leaderboards, exclusion rules and original official boxscore data")
