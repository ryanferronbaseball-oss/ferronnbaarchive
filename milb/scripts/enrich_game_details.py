#!/usr/bin/env python3
"""Enrich verified attended MiLB games with official inning, scoring, decisions,
and lineup/appearance order. Never read or write MLB or college-baseball data.
"""
import collections
import concurrent.futures
import datetime
import json
import pathlib
import time
import urllib.request

DATA=pathlib.Path(__file__).resolve().parents[1]/"data"
API="https://statsapi.mlb.com/api/v1"
HEADERS={"User-Agent":"CourtsideArchive-MiLB/1.0 (historical attendance verification)","Accept":"application/json"}
def get_json(url):
    for i in range(4):
        try:
            req=urllib.request.Request(url,headers=HEADERS)
            with urllib.request.urlopen(req,timeout=32) as res:
                return json.load(res)
        except Exception:
            if i==3:raise
            time.sleep(1.4*(i+1))

def data(name,default):
    path=DATA/name
    return json.loads(path.read_text(encoding="utf8")) if path.exists() else default

def save(name,value):
    (DATA/name).write_text(json.dumps(value,indent=2,ensure_ascii=False)+"\n",encoding="utf8")

def enrich(g):
    pk=g["source_game_id"]
    d={"game_id":g["id"],"pk":pk,"status":"pending","scores":None,"plays":None,"decisions":None,"order":None}
    side_ids={side:g["official_"+side+"_team_id"] for side in ("away","home")}
    # Official lineup (including replacements) and pitcher appearance ordering.
    try:
        box=get_json(f"{API}/game/{pk}/boxscore")
        patches={}
        for side in ("away","home"):
            team=box["teams"][side]
            if team["team"]["id"]!=side_ids[side]:
                raise ValueError(f"Team ID mismatch: {side} at game {pk}")
            pitchers=[str(i) for i in team.get("pitchers",[])]
            batters=[str(i) for i in team.get("batters",[])]
            starters=[str(i) for i in team.get("battingOrder",[])]
            for entry in team.get("players",{}).values():
                p=entry.get("person") or {}
                if p.get("id") is None:continue
                player_id=str(p["id"])
                order=entry.get("battingOrder")
                if order is not None:
                    order=int(order)
                    slot=order//100 if 100<=order<1000 else None
                    sub=order%100 if slot is not None else None
                elif player_id in starters:
                    slot=starters.index(player_id)+1
                    sub=0
                    order=slot*100
                else:
                    slot=sub=None
                patches[(side,player_id)]={
                    "batting_order":str(order) if order is not None else None,
                    "batting_slot":slot,
                    "batting_sub_index":sub,
                    "batter_appearance_index":batters.index(player_id) if player_id in batters else None,
                    "pitching_appearance_index":pitchers.index(player_id) if player_id in pitchers else None,
                }
        if len(patches)<18:raise ValueError("Incomplete official player order payload")
        d["order"]=patches
        d["order_status"]="verified"
    except Exception as error:
        d["order_status"]="error"
        d["order_error"]=str(error)[:180]
    try:
        lines=get_json(f"{API}/game/{pk}/linescore")
        total=lines.get("teams") or {}
        for side in ("away","home"):
            given=(total.get(side) or {}).get("runs")
            if given is not None and int(given)!=int(g[side+"_score"]):
                raise ValueError("Official "+side+" runs do not match attended final score")
        innings=[{"inning":i.get("num"),"away":(i.get("away") or {}).get("runs"),"home":(i.get("home") or {}).get("runs")} for i in lines.get("innings",[])]
        if not innings:raise ValueError("No inning data")
        d["scores"]=innings
        d["score_status"]="verified"
    except Exception as error:
        d["score_status"]="error"
        d["score_error"]=str(error)[:180]
    try:
        allplays=get_json(f"{API}/game/{pk}/playByPlay").get("allPlays",[])
        plays=[]
        for play in allplays:
            about=play.get("about") or {}
            if not about.get("isScoringPlay"):continue
            result=play.get("result") or {}
            description=result.get("description") or result.get("event")
            if not description:continue
            plays.append({"inning":about.get("inning"),"half":about.get("halfInning"),
                          "event":result.get("event"),"description":description,
                          "at_bat_index":about.get("atBatIndex")})
        if not plays and (g["away_score"]+g["home_score"])>0:
            raise ValueError("No official scoring descriptions available")
        d["plays"]=plays
        d["play_status"]="verified"
    except Exception as error:
        d["play_status"]="error"
        d["play_error"]=str(error)[:180]
    try:
        feed=get_json(f"{API}/game/{pk}/feed/live")
        if (feed.get("gameData") or {}).get("game",{}).get("pk")!=pk:
            raise ValueError("Unexpected feed game ID")
        decisions=(feed.get("liveData") or {}).get("decisions") or {}
        winner,loser=decisions.get("winner"),decisions.get("loser")
        if not winner or not loser or not winner.get("id") or not loser.get("id"):
            raise ValueError("Win/loss decisions unavailable in official game feed")
        if d["order"]:
            roster={int(pid):side for side,pid in d["order"].keys()}
            win_side="away" if g["away_score"]>g["home_score"] else "home"
            lose_side="home" if win_side=="away" else "away"
            if roster.get(int(winner["id"]))!=win_side or roster.get(int(loser["id"]))!=lose_side:
                raise ValueError("Official pitching decision team did not match winner/loser")
        def who(person):
            return {"id":person["id"],"name":person.get("fullName") or person.get("name") or ""} if person and person.get("id") else None
        d["decisions"]={"status":"verified","winner":who(winner),"loser":who(loser),"save":who(decisions.get("save"))}
        d["decision_status"]="verified"
    except Exception as error:
        d["decision_status"]="unavailable"
        d["decision_error"]=str(error)[:180]
    d["status"]="partial" if any(d.get(k+"_status")!="verified" for k in ["order","score","play","decision"]) else "verified"
    return d

def main():
    games=data("games.json",[])
    rows=data("player_stats.json",[])
    valid=[g for g in games if g.get("source_game_id") is not None and g.get("box_score_status")=="verified"]
    if not valid:raise RuntimeError("No verified MiLB games")
    if any((r.get("game_id") not in {g["id"] for g in games}) for r in rows):
        raise ValueError("Orphan player stats found")
    by_game=collections.defaultdict(list)
    for r in rows:by_game[r["game_id"]].append(r)
    if any(len(by_game[g["id"]])<18 for g in valid):
        raise ValueError("Missing complete boxscore rows in a game being enriched")
    innings=data("inning_scores.json",{})
    scoring=data("scoring_plays.json",{})
    decisions=data("pitching_decisions.json",{})
    summary=[]
    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:
        for result in pool.map(enrich,valid):
            summary.append(result)
            gid=result["game_id"]
            pk=str(result["pk"])
            if result["scores"] is not None:innings[pk]=result["scores"]
            if result["plays"] is not None:scoring[pk]=result["plays"]
            if result["decisions"] is not None:decisions[pk]=result["decisions"]
            if result["order"] is not None:
                for r in by_game[gid]:
                    patch=result["order"].get((r["side"],str(r["player_id"])))
                    if patch:r.update(patch)
            print(json.dumps({key:value for key,value in result.items() if key not in ("scores","plays","order","decisions")}),flush=True)
    byid={g["id"]:g for g in valid}
    verify_rows=0
    for g in valid:
        pk=str(g["source_game_id"])
        for line in innings.get(pk,[]):
            assert isinstance(line.get("inning"),int),f"Invalid inning: {pk}"
        for side in ("away","home"):
            assert all(r["team_id"]==g["official_"+side+"_team_id"] for r in by_game[g["id"]] if r["side"]==side)
            verify_rows+=len([r for r in by_game[g["id"]] if r["side"]==side])
    assert verify_rows==sum(len(by_game[g["id"]]) for g in valid)
    save("inning_scores.json",innings)
    save("scoring_plays.json",scoring)
    save("pitching_decisions.json",decisions)
    save("player_stats.json",rows)
    report={
        "source":"MLB StatsAPI (MiLB games only)",
        "timestamp":datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "games_checked":len(valid),
        "innings_verified":sum(x.get("score_status")=="verified" for x in summary),
        "scoring_plays_verified":sum(x.get("play_status")=="verified" for x in summary),
        "pitcher_order_verified":sum(x.get("order_status")=="verified" for x in summary),
        "pitching_decisions_verified":sum(x.get("decision_status")=="verified" for x in summary),
        "games":[{k:v for k,v in x.items() if k not in ("order","scores","plays","decisions")} for x in summary],
    }
    save("game_detail_report.json",report)
    print("FINAL_REPORT",json.dumps({k:v for k,v in report.items() if k!="games"}),flush=True)
if __name__=="__main__":main()
