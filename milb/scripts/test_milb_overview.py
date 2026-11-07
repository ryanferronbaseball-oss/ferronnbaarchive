#!/usr/bin/env python3
"""Confirm MiLB Overview matches MLB overview sections and never combines MLB stats."""
import functools
import http.server
import json
import pathlib
import socketserver
import threading
from playwright.sync_api import sync_playwright

ROOT=pathlib.Path(__file__).resolve().parents[2]
games=json.loads((ROOT/"milb/data/games.json").read_text())
rows=json.loads((ROOT/"milb/data/player_stats.json").read_text())
assert len(games)>=10 and len(rows)>=100
unique_players=len({str(r["player_id"]) for r in rows if r.get("player_id") is not None})
confirmed=sum(g.get("box_score_status")=="verified" and g.get("source_game_id") is not None for g in games)
seasons=len({g["date"][:4] for g in games})
class Reuse(socketserver.ThreadingTCPServer):
    allow_reuse_address=True
server=Reuse(("127.0.0.1",0),functools.partial(http.server.SimpleHTTPRequestHandler,directory=str(ROOT)))
thread=threading.Thread(target=server.serve_forever,daemon=True)
thread.start()
base=f"http://127.0.0.1:{server.server_address[1]}"
try:
    with sync_playwright() as p:
        browser=p.chromium.launch(headless=True)
        page=browser.new_page(viewport={"width":1366,"height":850})
        errors=[]
        requests=[]
        page.on("pageerror",lambda e:errors.append(str(e)))
        page.on("request",lambda r:requests.append(r.url))
        page.goto(base+"/milb/index.html",wait_until="networkidle")
        assert page.locator("h1").inner_text()=="Your MiLB history."
        assert page.locator(".metrics .metric").count()==4
        nums=[int(t.replace(",","")) for t in page.locator(".metrics .metric strong").all_inner_texts()]
        assert nums==[len(games),confirmed,unique_players,seasons],(nums,len(games),confirmed,unique_players,seasons)
        assert page.locator(".game-grid .game-card").count()==min(3,len(games))
        assert page.locator(".mlb-feature-grid .mlb-record").count()==3
        assert page.locator(".mlb-feature-grid a[href^='./player.html?id=']").count()>=2
        assert page.locator(".mlb-charts .panel").count()==2
        assert page.locator(".mlb-bar").count()>=3
        assert page.locator("#gameHistorySection").count()==1
        assert page.locator("#history tbody tr").count()==len(games)
        assert "Showing "+str(len(games))+" of "+str(len(games)) in page.locator("#showing").inner_text()
        assert page.locator('#history a[href^="./detail.html?id="]').count()==len(games)*2
        page.locator("#search").fill("Quakes")
        assert page.locator("#history tbody tr").count()>0
        assert page.locator("#history tbody tr").count()<len(games)
        page.locator("#search").fill("")
        page.locator("#yearFilter").select_option("2021")
        count2021=sum(g["date"].startswith("2021") for g in games)
        assert page.locator("#history tbody tr").count()==count2021
        page.locator("#yearFilter").select_option("")
        page.locator("#teamFilter").select_option("Lake Elsinore Storm")
        storm=sum("Lake Elsinore Storm" in (g["home_team"],g["away_team"]) for g in games)
        assert page.locator("#history tbody tr").count()==storm
        page.locator("#teamFilter").select_option("")
        page.locator("#sort").select_option("asc")
        assert "2014" in page.locator("#history tbody tr").first.inner_text()
        page.locator("#sort").select_option("desc")
        assert "2024" in page.locator("#history tbody tr").first.inner_text()
        assert not any("/mlb/data/" in u or "/college-baseball/data/" in u for u in requests)
        assert not errors,errors
        mobile=browser.new_page(viewport={"width":390,"height":844},is_mobile=True,has_touch=True)
        mobile.goto(base+"/milb/index.html",wait_until="networkidle")
        assert mobile.locator("h1").is_visible()
        assert mobile.locator(".metrics .metric").count()==4
        assert mobile.locator("#history tbody tr").count()==len(games)
        browser.close()
    print("PASS: MiLB Overview MLB layout, signature performances, charts, history filters, mobile and independent stats")
finally:
    server.shutdown()
    server.server_close()
