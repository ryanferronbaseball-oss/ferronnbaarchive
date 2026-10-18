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
check(len(games)==444 and len(original)==13188 and len(rules["rules"])==96,
      "Protected college attendance or original official player rows changed")
check(audit["ready_merges"]==96 and audit["not_ready"]==0 and
      cross["activated_person_merges"]==96 and cross["pending_person_merges"]==0,
      "All 96 attendee-approved transfer identities must now source-match")
check(all(x["status"]=="merge_ready" for x in audit["preview"]),
      "Every requested transfer pair must match both school records")
check(len(cross["merges"])==96 and len({m["canonical_id"] for m in cross["merges"]})==96,
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
              all(name(r["player"]) in ({name(rule["name"])} |
                  {name(alias) for sch,aliases in rule.get("source_names_by_school",{}).items()
                   if school(sch)==school(t) for alias in aliases})
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
# Simulate the browser alias transform and require all 13,188 genuine player-game lines
# to remain present, with no duplicate canonical person-game IDs.
unified=[(r["game_id"],mapped.get((r["team"],r["player_id"]),r["player_id"])) for r in original]
check(len(set(unified))==len(original),"Two identities collided in the same attended game")
before=len({r["player_id"] for r in original})
after=len({p for _,p in unified})
check(before-after==96,"Exactly one unique player identity should collapse per approved pair")
print(json.dumps({"source_records_preserved":len(original),"verified_owner_proposals":96,
      "left_pending":0,"before_unique_players":before,"after_unique_players":after,
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
    ("Ethan Lizama",["Western Kentucky","South Carolina"],2),
    ("Tate Soderstrom",["Arizona","UC San Diego"],7),
    ("Kyle Hvidsten",["Western Kentucky","Liberty"],2),
    ("Michael Graziano",["Georgia Tech","Mercer"],2),
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
        # Explicit 4/13 original university game replaces the wrong 4/14
        # attended-game identity without breaking the old scorecard deep link.
        oldgame="cb-2024-04-14-virginia-tech-georgia-tech-att0268"
        newgame="cb-2024-04-13-virginia-tech-georgia-tech-att0268"
        check(sum(g["id"]==newgame for g in games)==1 and
              not any(g["id"]==oldgame for g in games),
              "Correct attended April 13 identity not installed")
        for gid in (newgame,oldgame):
            page.goto(base+"/game.html?id="+quote(gid),wait_until="domcontentloaded")
            page.locator("#cb-game-details .cb-game-summary").wait_for(timeout=35000)
            summary=page.locator("#cb-game-details").inner_text()
            check("0 – 19" in summary and "Apr 13, 2024" in summary and
                  "Cam Jones" in summary,"April 13 score/date/official winner missing at game link")
            check(page.locator("#cb-game-details tr.mlb-substitute").count()>=13,
                  "April 13 nine-slot batting orders dropped official pinch hitters")
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
print("PASS 96 scoped transfer profiles, initials, old April 14 link, 13 pinch hitter rows and original 4/13 boxscore data")
