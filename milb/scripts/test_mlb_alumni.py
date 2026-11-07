#!/usr/bin/env python3
"""Validate MiLB To the MLB page mirrors the College Baseball alumni UX."""
import collections,functools,http.server,json,pathlib,socketserver,threading
from playwright.sync_api import sync_playwright
ROOT=pathlib.Path(__file__).resolve().parents[2]
games=json.loads((ROOT/"milb/data/games.json").read_text())
rows=json.loads((ROOT/"milb/data/player_stats.json").read_text())
registry=json.loads((ROOT/"milb/data/mlb_alumni_seed.json").read_text())
links=json.loads((ROOT/"milb/data/player_links.json").read_text())
audit=json.loads((ROOT/"milb/data/mlb_status_audit.json").read_text())
byId={int(r["mlb_id"]):r for r in links}
assert audit["player_ids_checked"]==len({r["player_id"] for r in rows})
assert len(registry["players"])==len(links)==audit["official_mlb_debuts"] and len(links)>0
assert all(x.get("verified") is True and x["mlb_id"]==x["milb_id"] and x["mlb_debut"] for x in links)
assert len({x["mlb_id"] for x in links})==len(links)
assert sum(x["mlb_seen"] for x in links)==audit["also_attended_in_mlb"]
assert all(x["mlb_player_id"] in byId for x in registry["players"])
byPlayer=collections.defaultdict(set)
for r in rows:byPlayer[r["player_id"]].add(r["game_id"])
uniqueGames=len({game for p in registry["players"] for game in byPlayer[p["mlb_player_id"]]})
round1=sum(p.get("draft_round")=="1" for p in registry["players"])
class Reuse(socketserver.ThreadingTCPServer):allow_reuse_address=True
server=Reuse(("127.0.0.1",0),functools.partial(http.server.SimpleHTTPRequestHandler,directory=str(ROOT)))
threading.Thread(target=server.serve_forever,daemon=True).start()
origin=f"http://127.0.0.1:{server.server_address[1]}"
try:
 with sync_playwright() as p:
  browser=p.chromium.launch(headless=True)
  page=browser.new_page(viewport={"width":1360,"height":900})
  errors=[];requests=[]
  page.on("pageerror",lambda e:errors.append(str(e)))
  page.on("request",lambda r:requests.append(r.url))
  page.goto(origin+"/milb/mlb-alumni.html",wait_until="networkidle",timeout=45000)
  assert page.locator("h1").inner_text()=="From MiLB to the MLB."
  assert page.locator(".alumni-summary .metric").count()==3
  values=[int(v.replace(",","")) for v in page.locator(".alumni-summary .metric strong").all_inner_texts()]
  assert values==[len(links),uniqueGames,round1],(values,len(links),uniqueGames,round1)
  assert page.locator(".alumni-player").count()==len(links)
  assert page.locator(".alumni-identity").count()==len(links)
  assert page.locator(".alumni-portrait img").count()==len(links)
  assert page.locator(".alumni-line").count()==len(links)
  assert page.locator(".alumni-info").count()==len(links)*4
  assert page.locator(".alumni-dates").count()==len(links)
  assert page.locator("#lastVerified").inner_text()!="Verification pending"
  assert page.locator('.alumni-player a[href^="./game.html?id="]').count()>0
  assert page.locator('.alumni-player a[href^="./player.html?id="]').count()==len(links)*2
  assert page.locator('.alumni-player a[href^="https://www.mlb.com/player/"]').count()==len(links)
  assert page.locator('.alumni-player a[href^="../mlb/player.html?id="]').count()==sum(x["mlb_seen"] for x in links)
  options=[x.get_attribute("value") for x in page.locator("#sort option").all()]
  assert options==["draft","draft-newest","draft-oldest","games","hits","strikeouts","name"]
  page.locator("#sort").select_option("name")
  first_names=[x.inner_text() for x in page.locator(".alumni-name").all()]
  assert first_names==sorted(first_names)
  page.locator("#sort").select_option("hits")
  page.locator("#sort").select_option("strikeouts")
  page.locator("#sort").select_option("games")
  page.locator("#sort").select_option("draft-newest")
  page.locator("#sort").select_option("draft-oldest")
  unique=registry["players"][0]["name"].split(" ")[-1]
  page.locator("#search").fill(unique)
  assert page.locator(".alumni-player").count()>=1
  assert page.locator(".alumni-player").count()<len(links)
  page.locator("#search").fill("xyz-unfindable-no-player")
  assert page.locator(".alumni-player").count()==0
  assert "No players match" in page.locator("#cards").inner_text()
  page.locator("#search").fill("")
  assert page.locator(".alumni-player").count()==len(links)
  assert not any("/mlb/data/" in u or "/college-baseball/data/" in u for u in requests),"Cross-sport stat request"
  assert not errors,errors
  mobile=browser.new_page(viewport={"width":390,"height":844},is_mobile=True,has_touch=True)
  mobile.goto(origin+"/milb/mlb-alumni.html",wait_until="networkidle",timeout=45000)
  assert mobile.locator(".alumni-player").count()==len(links)
  assert mobile.locator(".alumni-toolbar select").is_visible()
  browser.close()
 print("PASS: College Baseball style MiLB-to-MLB directory, 35 alumni, 7 cross-attended, filters, dates, links and independent stats")
finally:server.shutdown();server.server_close()
