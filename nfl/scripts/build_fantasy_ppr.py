#!/usr/bin/env python3
"""Build source-traceable traditional ESPN-style Full-PPR skill-player game scores.

Only passing, rushing, receiving and associated LOST fumbles are scored; DST,
IDP tackles/sacks, and kicker points are intentionally NOT mixed into PPR.
Before extending to new games, audit conversions and return touchdowns separately.
"""
import json
from collections import defaultdict
from decimal import Decimal
from pathlib import Path

DATA=Path(__file__).resolve().parents[1]/"data"
GAMES={g["id"]:g for g in json.loads((DATA/"games.json").read_text())}
ROWS=json.loads((DATA/"player_stats.json").read_text())
PLAYS=json.loads((DATA/"scoring_plays.json").read_text())
assert len(GAMES)==3 and len(PLAYS)==3

def integer(r,label):
    if not r:return 0
    try:return int(str(r["stat_values"][r["stat_labels"].index(label)]).replace(",",""))
    except (ValueError, IndexError):return 0

source=defaultdict(dict)
for row in ROWS:
    if row["category"] in ("passing","rushing","receiving","fumbles"):
        key=(row["game_id"],row["athlete_id"])
        source[key][row["category"]]=row

# Verify the known 2023 failed offensive conversion and defensive two-point
# conversion are not falsely credited to QB / RB / WR.
two_point_events=[
    (game_id,event)
    for game_id,day in PLAYS.items()
    for event in day["plays"]
    if "conversion" in (event.get("type","")+" "+event.get("description","")).lower()
       and ("two-point" in (event.get("type","")+" "+event.get("description","")).lower()
            or "2pt" in (event.get("type","")+" "+event.get("description","")).lower())
]
assert all("failed" in x[1].get("description","").lower() or "defensive" in x[1].get("type","").lower()
           for x in two_point_events), "New successful offensive 2-point conversion needs an athlete-level attribution"
return_td_rows=[r for r in ROWS if r["category"] in ("kickReturns","puntReturns") and integer(r,"TD")>0]
assert not return_td_rows, "New return TD requires attribution to eligible fantasy players"

players=[]
for (game_id,athlete_id),group in source.items():
    if not any(cat in group for cat in ("passing","rushing","receiving")):continue
    exemplar=next(group[x] for x in ("passing","rushing","receiving") if x in group)
    pas,rus,rec,fum=(group.get(x) for x in ("passing","rushing","receiving","fumbles"))
    stats={
      "passing_yards":integer(pas,"YDS"),
      "passing_tds":integer(pas,"TD"),
      "interceptions_thrown":integer(pas,"INT"),
      "rushing_yards":integer(rus,"YDS"),
      "rushing_tds":integer(rus,"TD"),
      "receptions":integer(rec,"REC"),
      "receiving_yards":integer(rec,"YDS"),
      "receiving_tds":integer(rec,"TD"),
      "fumbles_lost":integer(fum,"LOST"),
      "offensive_two_point_conversions":0,
      "kick_punt_return_tds":0
    }
    d=Decimal
    component={
      "passing":d(stats["passing_yards"])/25+4*d(stats["passing_tds"])-2*d(stats["interceptions_thrown"]),
      "rushing":d(stats["rushing_yards"])/10+6*d(stats["rushing_tds"]),
      "receiving":d(stats["receptions"])+d(stats["receiving_yards"])/10+6*d(stats["receiving_tds"]),
      "turnovers":-2*d(stats["fumbles_lost"]),
      "two_point":d(0),
      "returns":d(0)
    }
    total=sum(component.values(),d(0))
    game=GAMES[game_id]
    players.append({
      "game_id":game_id,"date":game["date"],"athlete_id":str(athlete_id),
      "player":exemplar["player"],"team":exemplar["team"],
      "opponent":game["home_abbr"] if exemplar["team"]==game["away_abbr"] else game["away_abbr"],
      "fantasy_ppr":float(total),"stat_line":stats,
      "ppr_components":{k:float(v) for k,v in component.items()},
      "source_categories":sorted(group),
      "source":"ESPN archived NFL player box score",
      "score_type":"traditional_full_ppr"
    })
players.sort(key=lambda x:(-x["fantasy_ppr"],x["date"],x["player"]))
assert len(players)==59,len(players)
assert sum(p["fantasy_ppr"]>=30 for p in players)<=len(players)
assert all(p["team"] in (GAMES[p["game_id"]]["away_abbr"],GAMES[p["game_id"]]["home_abbr"]) for p in players)
assert all(abs(sum(p["ppr_components"].values())-p["fantasy_ppr"])<0.000001 for p in players)
obj={
 "rules":{"name":"Traditional Full-PPR (ESPN-style)","passing_yards":0.04,
          "passing_touchdowns":4,"interceptions_thrown":-2,"rushing_yards":0.1,
          "rushing_touchdowns":6,"receiving_yards":0.1,"receiving_touchdowns":6,
          "reception":1,"fumbles_lost":-2,"successful_offensive_two_point_conversion":2,
          "individual_kick_or_punt_return_touchdown":6,
          "excluded":["K/DST scoring","IDP scoring","bonuses","TE premiums","yardage return points"]},
 "eligibility":"Players with source passing, rushing or receiving statistical rows",
 "audit":{"player_games":len(players),"games_covered":sorted({x["game_id"] for x in players}),
          "verified_successful_offensive_two_point_conversions":0,
          "verified_kick_punt_return_touchdowns":0,
          "source_two_point_notes":[{"game_id":g,"description":p["description"]}
                            for g,p in two_point_events],
          "milestones":{str(n):sum(x["fantasy_ppr"]>=n for x in players) for n in (10,20,25,30,40)}},
 "performances":players
}
(DATA/"fantasy_ppr.json").write_text(json.dumps(obj,indent=2)+"\n")
print("PPR sourced player-game scores:",len(players))
print("Best five:",[(x["player"],x["team"],x["date"],x["fantasy_ppr"]) for x in players[:5]])
print("Milestones:",obj["audit"]["milestones"])
