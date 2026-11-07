#!/usr/bin/env python3
"""Audit corrected college baseball profiles against completed MiLB attendance.
Creates review-only candidate file; it never silently merges names.
"""
import collections
import functools
import http.server
import json
import pathlib
import socketserver
import threading
import unicodedata
import re
from playwright.sync_api import sync_playwright

ROOT=pathlib.Path(__file__).resolve().parents[2]
DATA=ROOT/"milb"/"data"
rows=json.loads((DATA/"player_stats.json").read_text(encoding="utf8"))
progress=json.loads((DATA/"season_2021_import_progress.json").read_text(encoding="utf8"))
if not progress.get("full_2021_season_complete") or progress.get("2021_games_remaining")!=0:
    raise RuntimeError("College↔MiLB identity audit must wait until all attended 2021 games are imported")
previous_links=json.loads((DATA/"college_links.json").read_text(encoding="utf8"))
def norm(v):
    v=unicodedata.normalize("NFKD",str(v or "").casefold())
    v="".join(c for c in v if not unicodedata.combining(c))
    return re.sub(r"[^a-z0-9]","",v)
byMilb=collections.defaultdict(lambda:{"names":set(),"teams":set(),"games":set()})
for r in rows:
    if not isinstance(r.get("player_id"),int):continue
    obj=byMilb[r["player_id"]]
    obj["names"].add(r.get("name",""))
    obj["teams"].add(r.get("team",""))
    obj["games"].add(r.get("game_id",""))
class Reuse(socketserver.ThreadingTCPServer):allow_reuse_address=True
server=Reuse(("127.0.0.1",0),functools.partial(http.server.SimpleHTTPRequestHandler,directory=str(ROOT)))
threading.Thread(target=server.serve_forever,daemon=True).start()
try:
    with sync_playwright() as p:
        browser=p.chromium.launch(headless=True)
        page=browser.new_page()
        page.goto(f"http://127.0.0.1:{server.server_address[1]}/college-baseball/index.html",wait_until="domcontentloaded",timeout=60000)
        page.wait_for_function("typeof window.CollegeBaseballArchive !== 'undefined'",timeout=30000)
        college=page.evaluate("""async () => {
          const d=await window.CollegeBaseballArchive.load();
          return d.players.map(p=>({
            college_player_id:p.player_id,
            name:p.name,
            schools:p.teams,
            games:p.games.length
          }));
        }""")
        browser.close()
finally:server.shutdown();server.server_close()
byName=collections.defaultdict(list)
for r in college:byName[norm(r["name"])].append(r)
byMilbName=collections.defaultdict(list)
for id,obj in byMilb.items():
    for name in obj["names"]:
        byMilbName[norm(name)].append(id)
candidates=[]
for id,obj in sorted(byMilb.items()):
    matches={r["college_player_id"]:r for name in obj["names"] for r in byName.get(norm(name),[])}
    if not matches:continue
    candidate={
        "milb_id":id,
        "milb_names":sorted(obj["names"]),
        "milb_teams":sorted(obj["teams"]),
        "milb_games":len(obj["games"]),
        "college_profiles":list(matches.values()),
        "status":"review",
        "reason":"Exact normalized full name only: needs distinct-person validation",
    }
    if len(matches)>1:
        candidate["reason"]="Multiple distinct college profiles with same normalized name"
    if any(len(set(byMilbName[norm(name)]))>1 for name in obj["names"]):
        candidate["reason"]="Multiple different MiLB IDs have the same full name"
    prior=next((link for link in previous_links if link["milb_id"]==id),None)
    if prior and prior.get("verified"):
        candidate["status"]="previously_verified"
        candidate["existing_college_player_id"]=prior["college_player_id"]
    candidates.append(candidate)
report={"source":"CollegeBaseballArchive.load() with identity merges & corrections",
        "college_profiles_checked":len(college),
        "milb_ids_checked":len(byMilb),
        "name_match_candidates":len(candidates),
        "links_auto_approved":0,
        "existing_verified_links":len(previous_links),
        "new_name_candidates":sum(c["status"]=="review" for c in candidates),
        "candidates":candidates}
(DATA/"college_match_review.json").write_text(json.dumps(report,indent=2,ensure_ascii=False)+"\n",encoding="utf8")
print("COLLEGE_MATCH_AUDIT",json.dumps({k:v for k,v in report.items() if k!="candidates"}),flush=True)
for candidate in candidates:print("CANDIDATE",json.dumps(candidate,ensure_ascii=False),flush=True)
