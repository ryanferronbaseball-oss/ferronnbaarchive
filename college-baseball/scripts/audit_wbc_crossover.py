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
            name=x.get("fullName") or " ".join(filter(None,(x.get("firstName"),x.get("lastName"))))
            if not name:
                people=get(f"people/{pid}").get("people",[])
                person=next((p for p in people if p.get("id")==pid),{})
                name=person.get("fullName") or " ".join(filter(None,(person.get("firstName"),person.get("lastName"))))
            if not name:
                raise ValueError(f"No official name for player {pid} in game {pk}; box person={x!r}")
            records.append((pid,name,country,pk))
    return records
report={"version":1,"source":"Official MLB Stats API WBC schedule and final game box scores","archive_players":len(players),"years":{},"candidates":[],"errors":[]}
# Preserve completed tournaments from the previous run if the archive identity
# count is unchanged. Retry only incomplete tournaments.
if OUT.exists():
    previous=load(OUT)
    if previous.get("archive_players")==len(players) and previous.get("source")==report["source"]:
        complete={y:v for y,v in previous.get("years",{}).items() if v.get("status")=="complete" and v.get("games")==YEARS.get(int(y))}
        report["years"].update(complete)
        report["candidates"]=[x for x in previous.get("candidates",[]) if str(x["year"]) in complete]
for year,expected in YEARS.items():
    if report["years"].get(str(year),{}).get("status")=="complete":
        print(year,"reusing completed checkpoint",flush=True)
        continue
    try:
        # W denotes the championship round, not the entire WBC tournament.
        # Discover the tournament league from its metadata and query all game types.
        params={"sportId":51,"startDate":f"{year}-03-01","endDate":f"{year}-03-31"}
        probes=[]
        leagues=get("league",sportId=51,season=year).get("leagues",[])
        wbc_leagues=[x["id"] for x in leagues if "world baseball classic" in x.get("name","").lower()]
        for lid in dict.fromkeys(wbc_leagues+[160]):
            for extra in ({},{"gameTypes":"R,F,D,L,W,P"}):
                probes.append({**params,"leagueId":lid,**extra})
        probes.extend([params,{**params,"gameTypes":"R,F,D,L,W,P"},{**params,"gameType":"R,F,D,L,W,P"}])
        games={}
        diagnostics=[]
        # Schedule series descriptions identify WBC games without assuming that
        # every international fixture is a tournament game.
        for query in probes:
            try:
                schedule=get("schedule",**query)
                finals={g["gamePk"]:g for d in schedule.get("dates",[]) for g in d["games"] if g.get("status",{}).get("abstractGameState")=="Final"}
                marked={pk:g for pk,g in finals.items() if ("world baseball classic" in (g.get("seriesDescription") or "").lower() or "wbc" in (g.get("seriesDescription") or "").lower()) and "qualif" not in (g.get("seriesDescription") or "").lower() and "exhibition" not in (g.get("seriesDescription") or "").lower() and g.get("gameType") not in ("E","S")}
                scoped={pk:g for pk,g in finals.items() if g.get("gameType") not in ("E","S") and "qualif" not in (g.get("seriesDescription") or "").lower() and "exhibition" not in (g.get("seriesDescription") or "").lower()}
                diagnostics.append({"query":query,"finals":len(finals),"marked":len(marked),"scoped":len(scoped),"types":sorted(set(g.get("gameType","") for g in finals.values())),"series":sorted(set(g.get("seriesDescription") or "" for g in finals.values()))})
                if len(marked)==expected:
                    games=marked; break
                if query.get("leagueId") in wbc_leagues and len(scoped)==expected:
                    games=scoped; break
            except Exception as exc:
                diagnostics.append({"query":query,"error":str(exc)})
        report["years"][str(year)]={"status":"probing","schedule_diagnostics":diagnostics}
        if len(games)!=expected: raise ValueError(f"{year}: expected {expected} completed tournament games; schedule probes: {json.dumps(diagnostics)}")
        played=defaultdict(set); names={}
        with ThreadPoolExecutor(max_workers=4) as pool:
            for result in pool.map(game_players,games.values()):
                for pid,name,country,pk in result:
                    played[(pid,country)].add(pk); names[pid]=name
        report["years"][str(year)]={"games":len(games),"participants":len(played),"status":"complete","schedule_diagnostics":diagnostics}
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
        report["years"].setdefault(str(year),{})["status"]="incomplete"
        print(year,str(exc),flush=True)
    OUT.write_text(json.dumps(report,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
if report["errors"]: raise SystemExit("Incomplete WBC coverage; review saved partial checkpoint")
