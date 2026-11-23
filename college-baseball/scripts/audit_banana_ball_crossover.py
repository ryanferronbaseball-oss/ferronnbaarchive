#!/usr/bin/env python3
"""Audit Banana Ball game appearances among witnessed college baseball, MiLB and MLB players.

Sources:
 - Archive source-level box-score player rows.
 - Officially Bananas historical profiles: independently compiled summaries based
   on organizer-linked Banana Ball statistics, coverage 2020-2026.
NO automatic public player tags. Name matches require identity confirmation.
Separate actual played-game records from a draft/roster/selection announcement.
"""
from __future__ import annotations
import argparse
import json
import re
import time
import unicodedata
from collections import defaultdict
from pathlib import Path
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "college-baseball" / "data" / "banana_ball_crossover_audit.json"
INDEX = "https://officiallybananas.com/player-team-history/"
PATHS = {
  "NCAA": ROOT / "college-baseball" / "data" / "player_stats.json",
  "MiLB": ROOT / "milb" / "data" / "player_stats.json",
  "MLB": ROOT / "mlb" / "data" / "player_stats.json",
}
SUFFIX = re.compile(r"\b(?:jr|sr|ii|iii|iv)\b", re.I)
FIRST = re.compile(r"First recorded Banana Ball appearance:\s*(\d{4}-\d{2}-\d{2}|No recorded appearances)", re.I)
TEAMS = re.compile(r"Teams with recorded appearances:\s*([^\n]+)", re.I)
ROLE = re.compile(r"Last recorded playing team:\s*([^\n]+)", re.I)

def norm(s):
    s = unicodedata.normalize("NFKD", str(s or "")).encode("ascii", "ignore").decode().lower()
    s = s.replace("’","'").replace("“","").replace("”","")
    s = re.sub(r"\([^)]*\)", " ", s)
    s = re.sub(r"[^a-z0-9\s]", " ", s)
    s = SUFFIX.sub(" ", s)
    return " ".join(s.split())

def index_key(name):
    return norm(name)

def loose(name):
    arr = index_key(name).split()
    return arr[-1] + ":" + arr[0][:1] if len(arr)>=2 else ""

def get(session, url, delay):
    last = None
    for retry in range(3):
        try:
            response = session.get(url, timeout=35)
            response.raise_for_status()
            if len(response.text)<600: raise ValueError("Suspiciously short HTML")
            return response.text
        except (requests.RequestException, ValueError) as exc:
            last = str(exc)
            time.sleep(2*(retry+1))
        finally:
            time.sleep(delay)
    raise RuntimeError(f"{url}: {last}")

def load_archive():
    levels={}
    for level, path in PATHS.items():
        data=json.loads(path.read_text(encoding="utf-8"))
        if isinstance(data, dict):
            rows=next((data[k] for k in ["rows","player_stats","players","stats"] if isinstance(data.get(k),list)),None)
            if rows is None:
                raise ValueError(f"{path}: unexpected archive object keys {list(data)[:15]}")
        elif isinstance(data,list):
            rows=data
        else:
            raise ValueError(f"{path}: invalid player data")
        by_id={}
        for item in rows:
            if not isinstance(item, dict): continue
            pid=item.get("player_id")
            name=item.get("player") or item.get("name") or item.get("player_name")
            if not pid or not name: continue
            ident=str(pid)
            obj=by_id.setdefault(ident,{"player_id":pid,"archive_name":name,"teams":set(),"games":set(),"aliases":set()})
            obj["aliases"].add(str(name))
            if item.get("team"): obj["teams"].add(str(item["team"]))
            if item.get("game_id") is not None: obj["games"].add(str(item["game_id"]))
            if item.get("game_pk") is not None: obj["games"].add(str(item["game_pk"]))
        for obj in by_id.values():
            obj["teams"]=sorted(obj["teams"])
            obj["archive_aliases"]=sorted(obj.pop("aliases"))
            obj["games_seen"]=len(obj.pop("games"))
        levels[level]=by_id
        print(f"{level}: {len(rows)} player-game rows, {len(by_id)} unique IDs",flush=True)
    return levels

def roster_directory(html):
    soup=BeautifulSoup(html,"html.parser")
    seen={}
    for link in soup.find_all("a",href=True):
        href=urljoin(INDEX,link["href"])
        p=urlparse(href)
        if p.netloc != "officiallybananas.com": continue
        if not re.match(r"^/players/[^/]+/?$",p.path): continue
        name=link.get_text(" ",strip=True)
        if not name: continue
        if href.rstrip("/") not in seen:
            seen[href.rstrip("/")+"/"]={"banana_ball_name":name,"url":href.rstrip("/")+"/"}
    if len(seen)<250:
        raise RuntimeError(f"Only {len(seen)} player profiles; expected >=250. HTML layout or source changed.")
    return list(seen.values())

def fetch_appearance(session,profile,delay):
    try: html=get(session,profile["url"],delay)
    except Exception as exc: return {"status":"source_fetch_failed","error":str(exc)}
    soup=BeautifulSoup(html,"html.parser")
    main=soup.find("main") or soup
    body=main.get_text("\n",strip=True)
    # The source's profile summary explicitly distinguishes played-game status from draft status.
    first=FIRST.search(body)
    if not first:
        # Try whitespace-normalized complete profile if markup splits text.
        line=next((i for i in body.splitlines() if "First recorded Banana Ball appearance:" in i), "")
        if line:
            value=line.split(":",1)[-1].strip()
            if re.fullmatch(r"\d{4}-\d{2}-\d{2}",value): first_value=value
            elif "No recorded appearances" in value: first_value=None
            else: first_value="unknown"
        else: first_value="unknown"
    else:
        first_value=first.group(1) if first.group(1)!="No recorded appearances" else None
    if first_value=="unknown": return {"status":"source_parse_uncertain","source_url":profile["url"]}
    teams=TEAMS.search(body)
    latest=ROLE.search(body)
    return {
      "status":"recorded_game_appearance" if first_value else "no_recorded_game_appearance",
      "first_recorded_game":first_value,
      "team_history":teams.group(1).strip() if teams else None,
      "last_playing_team":latest.group(1).strip() if latest else None,
      "source_url":profile["url"]
    }

def audit(delay,max_profiles=0):
    levels=load_archive()
    session=requests.Session()
    session.headers.update({"User-Agent":"Mozilla/5.0 (compatible; CourtsideArchiveResearch/1.0; not a commercial crawler)"})
    source=roster_directory(get(session,INDEX,delay))
    archive_exact=defaultdict(list);archive_loose=defaultdict(list)
    for level,by_id in levels.items():
        for obj in by_id.values():
            record={"level":level,**obj}
            for alias in obj["archive_aliases"]:
                archive_exact[index_key(alias)].append(record)
                archive_loose[loose(alias)].append(record)
    matches=[]
    for p in source:
        token=index_key(p["banana_ball_name"])
        exact=archive_exact.get(token,[])
        if not exact:continue
        unique={(x["level"],str(x["player_id"])):x for x in exact}
        matches.append({**p,"archive_records":list(unique.values())})
    matches.sort(key=lambda p:p["banana_ball_name"].lower())
    if max_profiles:
        matches=matches[:max_profiles]
    print(f"Historical profiles: {len(source)}. Exact-name matches: {len(matches)}. Fetching individual game-status profiles.",flush=True)
    for i,match in enumerate(matches,1):
        match["appearance"]=fetch_appearance(session,match,delay)
        if i%10==0:print(f"Profile verification {i}/{len(matches)}",flush=True)
    alias_candidates=[]
    for p in source:
        if archive_exact.get(index_key(p["banana_ball_name"])):continue
        options=archive_loose.get(loose(p["banana_ball_name"]),[])
        unique={(o["level"],str(o["player_id"])):o for o in options}
        if 1<=len(unique)<=4:
            alias_candidates.append({"banana_ball_name":p["banana_ball_name"],"source_url":p["url"],"archive_records":list(unique.values()),"status":"initial_and_surname_only_unverified"})
    confirmed=[m for m in matches if m["appearance"]["status"]=="recorded_game_appearance"]
    pending=[m for m in matches if m["appearance"]["status"]!="recorded_game_appearance"]
    summary={
      "data_as_of":"2026-11-13 (source snapshot; historical player participation through 2026-10-10)",
      "archive_unique_players":{k:len(v) for k,v in levels.items()},
      "historical_source_profiles":len(source),
      "exact_name_matches":len(matches),
      "exact_name_with_recorded_games":len(confirmed),
      "exact_name_without_verified_game_or_source_failure":len(pending),
      "initial_surname_only_needs_review":len(alias_candidates),
      "new_player_tags_published":0,
      "warning":"A matching name and recorded Banana Ball appearance is a candidate, not yet verified as the identical archive person. No draft-only/roster-only players can be tagged."
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps({
      "summary":summary,
      "source":{"index":INDEX,"organizer_stats":"https://bananaball.com/stats/","notes":"Fan-maintained participation histories link to the organizer stats; independent source, not official player identity registry."},
      "recorded_game_candidates":confirmed,
      "no_recorded_games_or_fetch_issues":pending,
      "nickname_or_initial_candidates":alias_candidates
    },indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
    print(json.dumps(summary,indent=2),flush=True)
    for match in confirmed:
        print("GAME CANDIDATE",match["banana_ball_name"],
             match["appearance"].get("first_recorded_game"),
             [f"{r['level']}:{r['player_id']}" for r in match["archive_records"]],
             match["url"],flush=True)

if __name__=="__main__":
    ap=argparse.ArgumentParser()
    ap.add_argument("--delay",type=float,default=0.5)
    ap.add_argument("--max-profiles",type=int,default=0)
    args=ap.parse_args()
    audit(args.delay,args.max_profiles)
