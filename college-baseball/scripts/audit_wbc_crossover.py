#!/usr/bin/env python3
"""Review-only WBC crossmatch, based on actual official game box scores.
Verified MLBAM identity links are distinguished from names needing manual review.
No roster-only tags, qualifiers, or automatic name-only merges.
"""
import json, re, unicodedata, time
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from urllib.request import urlopen, Request
from urllib.parse import urlencode

ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / "college-baseball/data"
OUT = DATA / "wbc_crossover_audit.json"
YEARS = {2026:47, 2023:47, 2017:40, 2013:39, 2009:39, 2006:39}
API = "https://statsapi.mlb.com/api/v1/"
def load(path):
    return json.loads(path.read_text(encoding="utf-8"))
def get(path, **params):
    url = API + path + ("?" + urlencode(params) if params else "")
    for attempt in range(3):
        try:
            with urlopen(Request(url, headers={"User-Agent":"CourtsideArchive/1.0"}), timeout=45) as r:
                return json.load(r)
        except Exception:
            if attempt == 2: raise
            time.sleep(2 ** attempt)
def norm(name):
    s = unicodedata.normalize("NFKD", str(name or "")).encode("ascii","ignore").decode().lower()
    s = re.sub(r"\b(jr|sr|ii|iii|iv)\b", "", s)
    return re.sub(r"[^a-z0-9]", "", s)
def loose(name):
    s = re.sub(r"\b(jr|sr|ii|iii|iv)\b", "", str(name or ""), flags=re.I).split()
    return norm(s[0][0] + s[-1]) if len(s)>1 else ""
identity = load(DATA/"player_identity_crosswalk.json")
corrections = load(DATA/"player_name_corrections.json")
fixes = {(g["game_id"],g["team"],x["source_player_id"]):x for g in [corrections]+corrections.get("games",[]) for x in g["corrections"]}
aliases = {(x["team"],x["source_player_id"]):m["canonical_id"] for m in identity["merges"] for x in m["pairs"]}
redirect = {x:m["canonical_id"] for m in identity["merges"] for x in m["source_player_ids"]}
redirect.update({x["source_player_id"]:x["canonical_player_id"] for x in fixes.values()})
rows = load(DATA/"player_stats.json")
if not isinstance(rows,list): raise ValueError("Unexpected player rows")
players = {}
for row in rows:
    pid, team, name = row.get("player_id"),row.get("team"),row.get("player")
    if not pid or not team or not name: continue
    fix = fixes.get((row.get("game_id"),team,pid))
    if fix: pid,name = fix["canonical_player_id"],fix["player"]
    pid = aliases.get((team,pid),pid)
    p = players.setdefault(pid,{"college_player_id":pid,"names":set(),"schools":set()})
    p["names"].add(name); p["schools"].add(team)
for m in identity["merges"]:
    if m["canonical_id"] in players: players[m["canonical_id"]]["names"].add(m.get("name",""))
for a in identity.get("display_aliases",[]):
    if a["player_id"] in players: players[a["player_id"]]["names"].update([a.get("display_name","")]+a.get("former_names",[]))
exact, near = defaultdict(set),defaultdict(set)
for pid,p in players.items():
    for name in p["names"]:
        if norm(name): exact[norm(name)].add(pid)
        if loose(name): near[loose(name)].add(pid)
    p["names"]=sorted(p["names"]); p["schools"]=sorted(p["schools"])
known = defaultdict(set)
def link(x, field):
    pid=redirect.get(x["college_player_id"],x["college_player_id"])
    if pid in players and x.get(field): known[int(x[field])].add(pid)
for x in load(DATA/"mlb_alumni_seed.json")["players"]: link(x,"mlb_player_id")
for x in load(DATA/"mlb_crosswalk.json"):
    if x.get("verified"): link(x,"mlb_player_id")
for x in load(ROOT/"milb/data/college_links.json"):
    if x.get("verified"): link(x,"milb_id")
def game_players(g):
    pk=g["gamePk"]; box=get(f"game/{pk}/boxscore")
    records=[]
    for side in ("away","home"):
        t=box["teams"][side]; country=g["teams"][side]["team"]["name"]
        ids=set(t.get("batters",[]))|set(t.get("pitchers",[]))
        # Defensive substitutions and pinch runners may have no AB or IP.
        for x in t["players"].values():
            if any((x.get("stats",{}).get(k,{}) or {}).get("gamesPlayed",0)>0 for k in ("batting","pitching","fielding")):
                ids.add(x["person"]["id"])
        if not ids: raise ValueError(f"No player appearances in {pk} {side}")
        for pid in ids:
            x=t["players"]["ID"+str(pid)]["person"]
            records.append((pid,x["fullName"],country,pk))
    return records
report={"version":1,"source":"Official MLB Stats API WBC schedule and final game box scores","archive_players":len(players),"years":{},"candidates":[],"errors":[]}
for year,expected in YEARS.items():
    try:
        schedule=get("schedule",sportId=51,gameType="W",startDate=f"{year}-03-01",endDate=f"{year}-03-31")
        games={g["gamePk"]:g for d in schedule["dates"] for g in d["games"] if g.get("status",{}).get("abstractGameState")=="Final"}
        if len(games)!=expected: raise ValueError(f"{year}: expected {expected} completed tournament games, found {len(games)}; inspect source before claiming coverage")
        played=defaultdict(set); names={}
        with ThreadPoolExecutor(max_workers=4) as pool:
            for result in pool.map(game_players,games.values()):
                for pid,name,country,pk in result:
                    played[(pid,country)].add(pk); names[pid]=name
        report["years"][str(year)]={"games":len(games),"participants":len(played),"status":"complete"}
        for (mid,country),pks in sorted(played.items()):
            name=names[mid]; ids=known.get(mid,set())
            candidates=ids or exact.get(norm(name),set()) or near.get(loose(name),set())
            for pid in sorted(candidates):
                status="verified_existing_mlbam_link" if len(ids)==1 and pid in ids else "review_exact_name" if pid in exact.get(norm(name),set()) else "review_initial_surname"
                if len(ids)>1: status="review_conflicting_mlbam_links"
                report["candidates"].append({**players[pid],"mlb_player_id":mid,"wbc_name":name,"year":year,"country":country,"games":len(pks),"game_pks":sorted(pks),"source_url":API+f"game/{min(pks)}/boxscore","status":status})
        print(year,report["years"][str(year)],flush=True)
    except Exception as exc:
        report["errors"].append({"year":year,"error":str(exc)})
        report["years"][str(year)]={"status":"incomplete"}
        print(year,str(exc),flush=True)
    OUT.write_text(json.dumps(report,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
if report["errors"]: raise SystemExit("Incomplete WBC coverage; review saved partial checkpoint")
