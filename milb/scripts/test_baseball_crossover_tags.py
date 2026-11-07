#!/usr/bin/env python3
"""Verify baseball cross-sport badges on MiLB, MLB and college player profiles."""
import collections,functools,http.server,json,pathlib,socketserver,threading
from playwright.sync_api import sync_playwright
ROOT=pathlib.Path(__file__).resolve().parents[2]
M=ROOT/"milb"/"data"
rows=json.loads((M/"player_stats.json").read_text())
links=json.loads((M/"player_links.json").read_text())
college=json.loads((M/"college_links.json").read_text())
gameids={g["id"] for g in json.loads((M/"games.json").read_text())}
byId=collections.defaultdict(list)
for r in rows:
 assert r["game_id"] in gameids
 byId[r["player_id"]].append(r)
ids=set(byId)
assert len(ids)==156
assert len(links)==35
assert len([x for x in links if x["mlb_seen"]])==7
assert len(college)==6
assert len({r["college_player_id"] for r in college})==6
assert all(r["verified"] is True and r["milb_id"] in ids for r in college)
assert all(r["verified"] is True and r["mlb_debut"] for r in links)
assert not ({r["milb_id"] for r in college}-{r for r in ids})
positive={r["milb_id"]:r for r in links}
schools={r["milb_id"]:r for r in college}
example_nondebuted=next(i for i in ids if i not in positive and i not in schools)
mlb_alumni=next(r for r in links if not r["mlb_seen"])
both_mlb=next(r for r in links if r["mlb_seen"])
college_only=next(r for r in college if r["milb_id"] not in positive)
class Reuse(socketserver.ThreadingTCPServer):allow_reuse_address=True
server=Reuse(("127.0.0.1",0),functools.partial(http.server.SimpleHTTPRequestHandler,directory=str(ROOT)))
threading.Thread(target=server.serve_forever,daemon=True).start()
origin=f"http://127.0.0.1:{server.server_address[1]}"
try:
 with sync_playwright() as p:
  browser=p.chromium.launch(headless=True)
  def tab(url):
   page=browser.new_page(viewport={"width":1360,"height":900})
   page.goto(origin+url,wait_until="networkidle",timeout=65000)
   assert "Unable to load" not in page.locator("main").inner_text(),url
   assert "Player not found" not in page.locator("main").inner_text(),url
   return page
  # MLB debut is independent of whether user also attended a big-league game.
  page=tab("/milb/player.html?id="+str(mlb_alumni["milb_id"]))
  assert page.locator(".milb-crossover-badge").count()==1
  assert "REACHED MLB" in page.locator(".milb-crossover-badge").inner_text()
  assert "SEEN IN MiLB + MLB" not in page.locator("main").inner_text()
  page.close()
  page=tab("/milb/player.html?id="+str(both_mlb["milb_id"]))
  assert "REACHED MLB" in page.locator(".mlb-profile-achievements").inner_text()
  assert "SEEN IN MiLB + MLB" in page.locator(".mlb-profile-achievements").inner_text()
  assert page.locator('.milb-crossover-badge[href^="../mlb/player.html?id="]').count()==1
  page.close()
  page=tab("/milb/player.html?id="+str(college_only["milb_id"]))
  assert page.locator('.milb-crossover-badge[href^="../college-baseball/player.html?id="]').count()==1
  assert "SEEN IN COLLEGE + MiLB" in page.locator(".mlb-profile-achievements").inner_text()
  assert "REACHED MLB" not in page.locator("main").inner_text()
  page.close()
  page=tab("/milb/player.html?id="+str(example_nondebuted))
  assert page.locator(".milb-crossover-badge").count()==0
  page.close()
  for r in college:
   page=tab("/milb/player.html?id="+str(r["milb_id"]))
   match=page.locator('.milb-crossover-badge[href="../college-baseball/player.html?id='+r["college_player_id"]+'"]')
   assert match.count()==1,(r,match.count())
   page.close()
  # Reciprocal verified crossovers on MLB and College Baseball player profiles.
  page=tab("/mlb/player.html?id="+str(both_mlb["mlb_id"]))
  assert page.locator('.mlb-profile-badge[href="../milb/player.html?id='+str(both_mlb["milb_id"])+'"]').count()==1
  assert "SEEN IN MiLB + MLB" in page.locator("main").inner_text()
  page.close()
  for r in college:
   page=tab("/college-baseball/player.html?id="+r["college_player_id"])
   assert page.locator('.mlb-profile-badge[href="../milb/player.html?id='+str(r["milb_id"])+'"]').count()==1,r
   assert "SEEN IN COLLEGE + MiLB" in page.locator("main").inner_text()
   page.close()
  mobile=browser.new_page(viewport={"width":390,"height":844},is_mobile=True,has_touch=True)
  mobile.goto(origin+"/milb/player.html?id="+str(both_mlb["milb_id"]),wait_until="networkidle")
  assert mobile.locator(".milb-crossover-badge").count()>=2
  browser.close()
 print("PASS: 35 verified Reached MLB tags, 7 MiLB + MLB and 6 College + MiLB reciprocal links, no inferred identities, independent stats")
finally:
 server.shutdown();server.server_close()
