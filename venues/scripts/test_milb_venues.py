#!/usr/bin/env python3
"""Verify all MiLB stadium profiles, including future additions."""
import functools,http.server,json,pathlib,socketserver,threading
from playwright.sync_api import sync_playwright
root=pathlib.Path(__file__).resolve().parents[2]
data=json.loads((root/"venues/data/venues.json").read_text())
venues=[v for v in data["venues"] if "MiLB" in (v.get("sports") or [v["sport"]])]
assert len(venues)>=4
photos=json.loads((root/"venues/data/photos.json").read_text()).get("photos",{})
class Reuse(socketserver.ThreadingTCPServer):allow_reuse_address=True
server=Reuse(("127.0.0.1",0),functools.partial(http.server.SimpleHTTPRequestHandler,directory=str(root)))
threading.Thread(target=server.serve_forever,daemon=True).start()
origin=f"http://127.0.0.1:{server.server_address[1]}"
try:
 with sync_playwright() as p:
  browser=p.chromium.launch(headless=True)
  page=browser.new_page(viewport={"width":1360,"height":860})
  errors=[];page.on("pageerror",lambda e:errors.append(str(e)))
  page.goto(origin+"/venues/index.html",wait_until="networkidle")
  assert str(data["venueCount"]) in page.locator("#venueDirectoryStatus").inner_text()
  page.locator("#venueDirectorySport").select_option("MiLB")
  assert page.locator(".vp-venue").count()==len(venues)
  for v in venues:
   assert page.locator(f'.vp-venue[href="./venue.html?id={v["id"]}"]').count()==1,v["id"]
  page.locator("#venueDirectorySearch").fill("Lake Elsinore")
  assert page.locator(".vp-venue").count()==1
  assert not errors,errors
  for v in venues:
   vp=browser.new_page(viewport={"width":1360,"height":860})
   local=[];vp.on("pageerror",lambda e:local.append(str(e)))
   vp.goto(origin+"/venues/venue.html?id="+v["id"],wait_until="networkidle")
   assert vp.locator("#venueProfile h1").inner_text()==v["name"]
   assert vp.locator("#venueGamesRows tr").count()==min(v["visits"],15)
   assert vp.locator('#venueGamesRows a[href^="../milb/game.html?id="]').count()==2*sum(g["id"].startswith("milb-") for g in v["games"][-15:])
   assert vp.locator('a[href="../milb/"]').count()==1
   if v["id"] in photos:
    assert vp.locator(".vp-photo-figure").count()==1
   else:
    assert vp.locator(".vp-photo-placeholder").count()==1
   assert not local,local
   vp.close()
  mobile=browser.new_page(viewport={"width":390,"height":844},is_mobile=True,has_touch=True)
  mobile.goto(origin+"/venues/venue.html?id=venue-0133",wait_until="networkidle")
  assert mobile.locator("#venueProfile h1").inner_text()=="Lake Elsinore Diamond"
  diamond=next(v for v in venues if v["id"]=="venue-0133")
  assert mobile.locator("#venueGamesRows tr").count()==min(diamond["visits"],15)
  game=browser.new_page()
  example=next(v for v in venues if v["id"]=="venue-0133")["games"][0]
  game.goto(origin+"/milb/game.html?id="+example["id"],wait_until="networkidle")
  assert game.locator('a[href="../venues/venue.html?id=venue-0133"]').count()>0
  browser.close()
 print(f"PASS: {len(venues)} MiLB stadium profiles, directory filters, links, and mobile layouts")
finally:
 server.shutdown();server.server_close()
