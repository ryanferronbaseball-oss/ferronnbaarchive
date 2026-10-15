#!/usr/bin/env python3
"""Import complete ESPN NFL game summaries and each original box-score stat category.

Never fabricate missing historical player rows. ESPN box-score statistics are retained
verbatim with their category and original column names for future analytics mapping.
"""
import json, os, pathlib, time, urllib.request, urllib.parse
ROOT=pathlib.Path(__file__).resolve().parents[1]
DATA=ROOT/"data"
GAMES=json.loads((DATA/"games.json").read_text())
API="https://site.api.espn.com/apis/site/v2/sports/football/nfl/"
def fetch(endpoint):
 url=API+endpoint
 req=urllib.request.Request(url,headers={"User-Agent":"CourtsideArchiveDataImporter/1.0","Accept":"application/json"})
 with urllib.request.urlopen(req,timeout=30) as r:return json.load(r)
def find_event(g):
 if g.get("espn_event_id"):return str(g["espn_event_id"])
 # ESPN date scoreboard can return early-season opponents, old seasons included when indexed.
 for dates in (g["date"].replace("-",""), str(g["season"])):
  q=urllib.parse.urlencode({"dates":dates,"limit":1000})
  try:board=fetch("scoreboard?"+q)
  except Exception as exc:print("scoreboard unavailable",g["id"],dates,str(exc));continue
  for event in board.get("events",[]):
   c=(event.get("competitions") or [{}])[0]
   x=[(t.get("team") or {}).get("abbreviation","").upper() for t in c.get("competitors",[])]
   aliases={"SF":{"SF","SFO"},"STL":{"STL","LAR","LA"}}
   a=aliases.get(g["away_abbr"],{g["away_abbr"]})
   h=aliases.get(g["home_abbr"],{g["home_abbr"]})
   if event.get("date","")[:10]==g["date"] and any(t in a for t in x) and any(t in h for t in x):
    return str(event["id"])
 return None
def parse(g,doc,event_id):
 box=doc.get("boxscore") or {}
 result=[]
 for side in box.get("players",[]):
  team=side.get("team") or {}
  abbrev=team.get("abbreviation")
  teamid=team.get("id")
  for cat in side.get("statistics",[]):
   labels=cat.get("labels") or []
   keys=cat.get("keys") or []
   for entry in cat.get("athletes",[]):
    a=entry.get("athlete") or {}
    stats=entry.get("stats") or []
    if not a.get("id"):continue
    result.append({"game_id":g["id"],"date":g["date"],"espn_event_id":event_id,
     "team":abbrev,"team_id":teamid,"athlete_id":str(a["id"]),"player":a.get("displayName"),
     "category":cat.get("name"),"stat_values":stats,"stat_labels":labels,"stat_keys":keys,
     "source":"ESPN game summary boxscore"})
 return result
def main():
 all_rows=[];reports=[];raw=DATA/"raw";raw.mkdir(exist_ok=True)
 for g in GAMES:
  game_id=g["id"]
  event=find_event(g)
  if event is None:
   reports.append({"game_id":game_id,"status":"unresolved_espn_event_id","full_boxscore_imported":False,"player_stat_rows":0})
   print(game_id,"EVENT_ID_UNRESOLVED");continue
  try:
   doc=fetch("summary?"+urllib.parse.urlencode({"event":event}))
   comp=(doc.get("header",{}).get("competitions") or [{}])[0]
   teams=[x.get("team",{}).get("abbreviation","") for x in comp.get("competitors",[])]
   if not teams or not any(x in ("ARI","IND","TEN","SF","SFO","STL","LAR","LA") for x in teams):
    raise ValueError("Unexpected teams: "+str(teams))
   rows=parse(g,doc,event)
   (raw/(game_id+".json")).write_text(json.dumps(doc,indent=2)+"\n")
   all_rows+=rows
   reports.append({"game_id":game_id,"status":"imported" if rows else "no_player_statistics_returned",
                   "full_boxscore_imported":bool(rows),"player_stat_rows":len(rows),
                   "categories":sorted(set(x["category"] or "" for x in rows)),"espn_event_id":event})
   print(game_id,len(rows),"category-rows",flush=True)
  except Exception as exc:
   reports.append({"game_id":game_id,"status":"error","full_boxscore_imported":False,"error":str(exc)})
   print(game_id,"ERROR",str(exc),flush=True)
 (DATA/"player_stats.json").write_text(json.dumps(all_rows,indent=2)+"\n")
 (DATA/"import_report.json").write_text(json.dumps({"games":reports,"all_games_fully_imported":all(x["full_boxscore_imported"] for x in reports)},indent=2)+"\n")
if __name__=="__main__":main()
