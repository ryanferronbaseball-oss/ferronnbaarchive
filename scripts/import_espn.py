#!/usr/bin/env python3
"""ESPN historical NBA box-score pilot. No data is accepted without validation."""
import argparse
import csv
import json
import pathlib
import re
import time
import requests

ROOT=pathlib.Path(__file__).resolve().parents[1]
DATA=ROOT/"data"
TEAMS={
"Atlanta":"ATL","Boston":"BOS","Brooklyn":"BKN","Charlotte":"CHA","Chicago":"CHI",
"Cleveland":"CLE","Dallas":"DAL","Denver":"DEN","Detroit":"DET","Golden State":"GS",
"Houston":"HOU","Indiana":"IND","LA Clippers":"LAC","LA Lakers":"LAL",
"Memphis":"MEM","Miami":"MIA","Milwaukee":"MIL","Minnesota":"MIN",
"New Orleans":"NO","New York":"NY","Oklahoma City":"OKC","Orlando":"ORL",
"Philadelphia":"PHI","Phoenix":"PHX","Portland":"POR","Sacramento":"SAC",
"San Antonio":"SA","Toronto":"TOR","Utah":"UTAH","Washington":"WSH"}
ALIASES={
"ATL":{"ATL"},"BOS":{"BOS"},"CHA":{"CHA","CHA"},"CHI":{"CHI"},"CLE":{"CLE"},
"DEN":{"DEN"},"GS":{"GS","GSW"},"LAC":{"LAC"},"LAL":{"LAL"},"MIA":{"MIA"},
"MIN":{"MIN"},"NO":{"NO","NOH","NOK","NOP"},"NY":{"NY","NYK"},
"OKC":{"OKC"},"PHX":{"PHX"},"SAC":{"SAC"},"SA":{"SA","SAS"},"UTAH":{"UTAH","UTA"}}
SESSION=requests.Session()
SESSION.headers.update({"User-Agent":"CourtsideArchive/0.3 historical box-score research"})

def get(url, params):
    response=SESSION.get(url,params=params,timeout=18)
    response.raise_for_status()
    return response.json()

def matching(comp, name):
    want=TEAMS[name]
    found=(comp.get("team") or {}).get("abbreviation","").upper()
    return found in ALIASES.get(want,{want})

def find_event(game):
    date=game["date"].replace("-","")
    obj=get("https://site.api.espn.com/apis/site/v2/sports/basketball/nba/scoreboard",{"dates":date,"limit":50})
    matched=[]
    for event in obj.get("events",[]):
        comps=(event.get("competitions") or [{}])[0].get("competitors") or []
        home=next((c for c in comps if c.get("homeAway")=="home"),None)
        away=next((c for c in comps if c.get("homeAway")=="away"),None)
        if home and away and matching(home,game["home"]) and matching(away,game["away"]):
            matched.append((event,away,home))
    if len(matched)!=1: raise ValueError(f"ESPN matchup matches: {len(matched)} on {date}")
    event,away,home=matched[0]
    if not event.get("status",{}).get("type",{}).get("completed"):
        raise ValueError("Game not marked final")
    for comp,key in ((away,"away_score"),(home,"home_score")):
        if game[key] and int(comp["score"])!=int(game[key]):
            raise ValueError(f"{key} differs: attendance tracker {game[key]}, ESPN {comp['score']}")
    return str(event["id"]),int(away["score"]),int(home["score"])

def parse_made_attempted(value):
    parts=str(value or "0-0").split("-")
    if len(parts)!=2: raise ValueError(f"Bad shooting stat: {value}")
    return int(parts[0]),int(parts[1])

def build_players(summary,event_id,game):
    box=summary.get("boxscore") or {}
    teams=box.get("players") or []
    if len(teams)!=2: raise ValueError("ESPN summary lacks both team player lists")
    output=[]
    for team in teams:
        for group in team.get("statistics") or []:
            labels=[str(x).upper().strip() for x in group.get("labels") or []]
            if not labels: continue
            for entry in group.get("athletes") or []:
                if entry.get("didNotPlay") or not entry.get("stats"): continue
                values=entry["stats"]
                if len(values)!=len(labels): raise ValueError("Player stat columns do not match labels")
                stats=dict(zip(labels,values))
                if str(stats.get("MIN","")).strip() in {"", "--", "DNP", "DND"}: continue
                for required in ["PTS","REB","AST","FG","3PT","FT"]:
                    if required not in stats: raise ValueError("Missing ESPN stat column "+required)
                fg, fga=parse_made_attempted(stats["FG"])
                fg3, fg3a=parse_made_attempted(stats["3PT"])
                ft, fta=parse_made_attempted(stats["FT"])
                pts=int(stats["PTS"])
                if pts!=2*fg+fg3+ft: raise ValueError("Player scoring arithmetic invalid")
                rebounds=int(stats["REB"])
                oreb=int(stats.get("OREB",0)) if "OREB" in stats else None
                dreb=int(stats.get("DREB",0)) if "DREB" in stats else None
                if oreb is not None and dreb is not None and oreb+dreb!=rebounds:
                    raise ValueError("Player rebounds arithmetic invalid")
                athlete=entry.get("athlete") or {}
                if not athlete.get("id"):raise ValueError("Missing stable ESPN player id")
                item={
                    "game_id":game.get("nba_game_id") or None,
                    "espn_event_id":event_id,
                    "date":game["date"],"player_id":"espn:"+str(athlete["id"]),
                    "player":athlete.get("displayName") or athlete.get("fullName"),
                    "team_id":str((team.get("team") or {}).get("id","")),
                    "minutes":str(stats.get("MIN","")),
                    "pts":pts,"reb":rebounds,"ast":int(stats["AST"]),
                    "fgm":fg,"fga":fga,"fg3m":fg3,"fg3a":fg3a,"ftm":ft,"fta":fta,
                    "oreb":oreb,"dreb":dreb,
                    "stl":int(stats["STL"]) if "STL" in stats else None,
                    "blk":int(stats["BLK"]) if "BLK" in stats else None,
                    "tov":int(stats["TO"]) if "TO" in stats else None,
                    "source":"ESPN summary API"}
                output.append(item)
    if len(output)<10: raise ValueError(f"Only {len(output)} appearing players")
    ids={(p["espn_event_id"],p["player_id"]) for p in output}
    if len(ids)!=len(output):raise ValueError("Duplicate players")
    return output

def validate(players,away_score,home_score):
    points={}
    for p in players:
        if not p["team_id"]: raise ValueError("Missing team ID in box score")
        points[p["team_id"]]=points.get(p["team_id"],0)+p["pts"]
    if len(points)!=2 or sorted(points.values())!=sorted([away_score,home_score]):
        raise ValueError(f"Team sum mismatch: {points}, expected {away_score} / {home_score}")
    return points

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--pilot",action="store_true",help="Run only three representative years")
    args=parser.parse_args()
    games=list(csv.DictReader((DATA/"games.csv").open()))
    if args.pilot: games=[g for g in games if g["id"] in {"1","23","30"}]
    outfile=DATA/"player_boxscores_espn.json"
    reportfile=DATA/"espn_import_report.json"
    logs=json.loads(outfile.read_text()) if outfile.exists() else []
    report=json.loads(reportfile.read_text()) if reportfile.exists() else {}
    existing={p["espn_event_id"] for p in logs}
    for game in games:
        key=game["id"]
        try:
            event_id,away,home=find_event(game)
            if event_id in existing:
                report[key]={"status":"already_imported","espn_event_id":event_id}
                continue
            summary=get("https://site.api.espn.com/apis/site/v2/sports/basketball/nba/summary",{"event":event_id})
            players=build_players(summary,event_id,game)
            sums=validate(players,away,home)
            logs.extend(players)
            existing.add(event_id)
            report[key]={"status":"validated","espn_event_id":event_id,"players":len(players),
                         "away_score":away,"home_score":home,"team_points":sums}
            print(f"VALIDATED {game['date']} {game['away']} @ {game['home']}: {len(players)} players")
        except Exception as error:
            report[key]={"status":"needs_review","reason":str(error)[:300]}
            print(f"NEEDS REVIEW {game['date']} {game['away']} @ {game['home']}: {error}")
        outfile.write_text(json.dumps(logs,indent=2)+"\n")
        reportfile.write_text(json.dumps(report,indent=2)+"\n")
        time.sleep(1)
    if not logs:
        print("No validated player logs yet. Inspect report; a green workflow result is not a successful import.")

if __name__=="__main__":main()
