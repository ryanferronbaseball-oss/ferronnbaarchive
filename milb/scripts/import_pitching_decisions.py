#!/usr/bin/env python3
"""Verified W/L/S pitching decisions for attended MiLB game history.

Uses /api/v1/schedule?gamePk=...&hydrate=decisions (historical results).
The ordinary /api/v1/game/{pk}/feed/live returned 404 for MiLB; if needed,
fall back to /api/v1.1/game/{pk}/feed/live, independently observed to work.

Every credited MLBAM pitcher MUST have appeared on the correct team, and
the credits must match the final score. No decision is guessed from score,
ERA, pitching order or Player of the Game. No MLB or college stats changed.
"""
import collections
import concurrent.futures
import datetime
import json
import pathlib
import time
import urllib.error
import urllib.parse
import urllib.request

DATA=pathlib.Path(__file__).resolve().parents[1]/"data"
BASE="https://statsapi.mlb.com"
HEADERS={"User-Agent":"CourtsideArchive-MiLB-Decision-Reconciliation/1.0","Accept":"application/json"}
def get(url):
    for attempt in range(4):
        try:
            with urllib.request.urlopen(urllib.request.Request(url,headers=HEADERS),timeout=25) as response:
                return json.load(response)
        except (urllib.error.URLError,TimeoutError,OSError):
            if attempt==3:raise
            time.sleep(1.1*(attempt+1))

def read(name):
    return json.loads((DATA/name).read_text(encoding="utf8"))

def save(name,value):
    (DATA/name).write_text(json.dumps(value,ensure_ascii=False,indent=2)+"\n",encoding="utf8")

def official_decisions(game):
    pk=int(game["source_game_id"])
    source=BASE+"/api/v1/schedule?"+urllib.parse.urlencode({"gamePk":pk,"hydrate":"decisions"})
    via="schedule_hydrate_decisions"
    schedules=get(source)
    matches=[item for d in schedules.get("dates",[]) for item in d.get("games",[]) if item.get("gamePk")==pk]
    if len(matches)!=1:raise ValueError(f"Expected one official game {pk} in schedule, got {len(matches)}")
    item=matches[0]
    decisions=item.get("decisions")
    if not decisions or not decisions.get("winner") or not decisions.get("loser"):
        source=BASE+f"/api/v1.1/game/{pk}/feed/live"
        via="game_feed_v1.1"
        feed=get(source)
        if feed.get("gamePk")!=pk:raise ValueError(f"v1.1 gamePk mismatch {pk}")
        decisions=(feed.get("liveData") or {}).get("decisions")
    if not decisions or not decisions.get("winner") or not decisions.get("loser"):
        raise ValueError(f"Official W/L pitcher identity missing for {pk}")
    if item.get("status",{}).get("abstractGameState")!="Final":
        raise ValueError(f"Game is not an official final {pk}")
    for side in ("away","home"):
        given=(item.get("teams",{}).get(side) or {}).get("score")
        if given is not None and int(given)!=int(game[side+"_score"]):
            raise ValueError(f"Official final score mismatch in {pk} on {side}")
        teamid=(item.get("teams",{}).get(side) or {}).get("team",{}).get("id")
        if teamid is not None and int(teamid)!=int(game["official_"+side+"_team_id"]):
            raise ValueError(f"Official team ID mismatch in {pk} on {side}")
    def identity(person):
        if not person:return None
        id=person.get("id")
        name=person.get("fullName") or person.get("name")
        if not isinstance(id,int) or not name:raise ValueError(f"Invalid official pitcher identity {pk}: {person}")
        return {"id":id,"name":name}
    return {"status":"verified","winner":identity(decisions.get("winner")),
            "loser":identity(decisions.get("loser")),
            "save":identity(decisions.get("save")),
            "source":"MLB StatsAPI official "+via,
            "source_url":source,
            "verified_game_pk":pk}

def apply():
    games=read("games.json")
    rows=read("player_stats.json")
    previous=read("pitching_decisions.json")
    report=read("game_detail_report.json")
    if len(games)!=112 or report["games_checked"]!=112:
        raise ValueError("Expected all 112 verified MiLB game entries")
    if any(g.get("box_score_status")!="verified" or g.get("source_game_id") is None for g in games):
        raise ValueError("Unverified MiLB games cannot receive official decisions")
    if len({g["source_game_id"] for g in games})!=len(games):
        raise ValueError("Duplicate official MiLB game IDs")
    byGame=collections.defaultdict(list)
    for r in rows:
        byGame[str(r["game_id"])].append(r)
    if set(byGame)!={g["id"] for g in games}:
        raise ValueError("Game boxscore coverage incomplete; do not publish decisions")
    if any(len(byGame[g["id"]])<18 for g in games):
        raise ValueError("Incomplete MiLB boxscore; do not publish decisions")
    decisions={}
    with concurrent.futures.ThreadPoolExecutor(max_workers=7) as pool:
        for game,record in zip(games,pool.map(official_decisions,games)):
            pk=str(game["source_game_id"])
            winner_id,loser_id=record["winner"]["id"],record["loser"]["id"]
            save_id=record["save"]["id"] if record["save"] else None
            if winner_id==loser_id or save_id in (winner_id,loser_id):
                raise ValueError(f"Invalid overlapping pitching credits {pk}")
            if int(game["away_score"])==int(game["home_score"]):
                raise ValueError("Tie game requires special official review; no W/L assumed")
            winningSide="away" if game["away_score"]>game["home_score"] else "home"
            losingSide="home" if winningSide=="away" else "away"
            pitcherSide={}
            for row in byGame[game["id"]]:
                if row.get("pitching") is not None:
                    if row["player_id"] in pitcherSide:
                        raise ValueError(f"Duplicate pitcher ID in official game {pk}")
                    pitcherSide[row["player_id"]]=row["side"]
            if pitcherSide.get(winner_id)!=winningSide:
                raise ValueError(f"Winner not on winning team/boxscore {pk}: {winner_id}")
            if pitcherSide.get(loser_id)!=losingSide:
                raise ValueError(f"Loser not on losing team/boxscore {pk}: {loser_id}")
            if save_id is not None and pitcherSide.get(save_id)!=winningSide:
                raise ValueError(f"Save pitcher not on winning team/boxscore {pk}: {save_id}")
            decisions[pk]=record
            print("VERIFIED_PITCHING_DECISION",json.dumps({
                "pk":pk,"date":game["date"],
                "W":record["winner"]["name"],"L":record["loser"]["name"],
                "SV":record["save"]["name"] if record["save"] else None,
                "source":record["source"]},ensure_ascii=False),flush=True)
    # Only after all 112 official credits were verified, add them to the per-game
    # pitching stats and roll up the existing audit.
    byPk={g["id"]:str(g["source_game_id"]) for g in games}
    for row in rows:
        if row.get("pitching") is None:continue
        d=decisions[byPk[row["game_id"]]]
        person=row["player_id"]
        row["pitching"]["w"]=1 if person==d["winner"]["id"] else 0
        row["pitching"]["l"]=1 if person==d["loser"]["id"] else 0
        row["pitching"]["sv"]=1 if d["save"] and person==d["save"]["id"] else 0
    for game in games:
        r=[x for x in byGame[game["id"]] if x.get("pitching") is not None]
        assert sum(p["pitching"]["w"] for p in r)==1
        assert sum(p["pitching"]["l"] for p in r)==1
        assert sum(p["pitching"]["sv"] for p in r)<=1
        assert all(p["pitching"]["w"]+p["pitching"]["l"]+p["pitching"]["sv"]<=1 for p in r)
    allStats=[r["pitching"] for r in rows if r.get("pitching") is not None]
    wins=sum(x["w"] for x in allStats)
    losses=sum(x["l"] for x in allStats)
    saves=sum(x["sv"] for x in allStats)
    assert wins==losses==len(games)
    assert saves==sum(d["save"] is not None for d in decisions.values())
    if set(decisions)!={str(g["source_game_id"]) for g in games}:
        raise ValueError("Pitching decision coverage incomplete")
    byResult={item["game_id"]:item for item in report["games"]}
    if set(byResult)!={g["id"] for g in games}:
        raise ValueError("Previous game-detail report is missing an attended game")
    for g in games:
        record=byResult[g["id"]]
        record["decision_status"]="verified"
        record.pop("decision_error",None)
        record["status"]="verified" if all(record.get(k+"_status")=="verified" for k in ("order","score","play","decision")) else "partial"
    report["pitching_decisions_verified"]=len(games)
    report["timestamp"]=datetime.datetime.now(datetime.timezone.utc).isoformat()
    audit={
        "source":"Official MLB StatsAPI schedule hydration with /api/v1.1/game feed fallback",
        "verified_at":report["timestamp"],
        "games_checked":len(games),
        "games_with_verified_win":wins,
        "games_with_verified_loss":losses,
        "games_with_verified_save":saves,
        "games_without_save":len(games)-saves,
        "player_game_pitching_rows":len(allStats),
        "all_w_l_sv_internally_consistent":True,
        "miLB_data_only":True,
        "unverified_game_ids":[],
        "games":[{"game_id":g["id"],"game_pk":g["source_game_id"],
                  "winner":decisions[str(g["source_game_id"])]["winner"]["id"],
                  "loser":decisions[str(g["source_game_id"])]["loser"]["id"],
                  "save":decisions[str(g["source_game_id"])]["save"]["id"] if decisions[str(g["source_game_id"])]["save"] else None}
                 for g in games]
    }
    # No files are mutated unless the full audit succeeded.
    save("player_stats.json",rows)
    save("pitching_decisions.json",decisions)
    save("game_detail_report.json",report)
    save("pitching_decisions_audit.json",audit)
    print("PITCHING_DECISIONS_SUCCESS",json.dumps({k:v for k,v in audit.items() if k!="games"}),flush=True)

if __name__=="__main__":
    apply()
