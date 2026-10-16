#!/usr/bin/env python3
"""Match personal MLB attendance to official MLB StatsAPI, retrieve verified box scores.

python mlb/scripts/import_official.py --pilot       # Five spread-out historical games
python mlb/scripts/import_official.py --all         # All 131 attendee entries

Authoritative input: mlb/data/attendance.json. Doubleheaders are kept distinct.
Unmatched games and unavailable player metrics remain null, never zero.
"""
import argparse,collections,concurrent.futures,datetime,json,pathlib,re,time,urllib.request,urllib.parse
ROOT=pathlib.Path(__file__).resolve().parents[1]
DATA=ROOT/"data"
ATTENDANCE=json.loads((DATA/"attendance.json").read_text())
API="https://statsapi.mlb.com/api/v1"
TEAM={
"arizona diamondbacks":109,"atlanta braves":144,"baltimore orioles":110,
"boston red sox":111,"chicago white sox":145,"chicago cubs":112,"cincinnati reds":113,
"cleveland indians":114,"cleveland guardians":114,"colorado rockies":115,
"detroit tigers":116,"houston astros":117,"kansas city royals":118,
"los angeles angels":108,"los angeles angels of anaheim":108,"anaheim angels":108,
"los angeles dodgers":119,"florida marlins":146,"miami marlins":146,
"milwaukee brewers":158,"minnesota twins":142,"new york mets":121,
"new york yankees":147,"oakland athletics":133,"athletics":133,
"philadelphia phillies":143,"pittsburgh pirates":134,"san diego padres":135,
"seattle mariners":136,"san francisco giants":137,"st. louis cardinals":138,
"st louis cardinals":138,"tampa bay rays":139,"tampa bay devil rays":139,
"texas rangers":140,"toronto blue jays":141,"washington nationals":120}
PILOT_IDS={1,38,55,74,130}
def get_json(url,retries=3):
 for attempt in range(retries):
  try:
   req=urllib.request.Request(url,headers={"User-Agent":"CourtsideArchive/1.0 (personal historical MLB attendance)", "Accept":"application/json"})
   with urllib.request.urlopen(req,timeout=27) as res:return json.load(res)
  except Exception:
   if attempt==retries-1:raise
   time.sleep(1.5*(attempt+1))
def integer(x):
 try:return int(x)
 except (ValueError,TypeError):return 0
def decimal(x):
 try:return float(x)
 except (ValueError,TypeError):return None
def team_id(s):return TEAM.get(str(s).strip().lower())
def inning_outs(ip):
 # Baseball IP is .0/.1/.2 for thirds, not decimal fractional innings.
 text=str(ip or "0.0")
 parts=text.split(".")
 if len(parts)==2 and parts[1] in ("0","1","2"):return int(parts[0])*3+int(parts[1])
 return None
def schedule(date):
 u=API+"/schedule?"+urllib.parse.urlencode({"sportId":1,"date":date,"gameType":"R,F,D,L,W,C,P","hydrate":"linescore"})
 response=get_json(u)
 return [g for date_group in response.get("dates",[]) for g in date_group.get("games",[])]
def match_games():
 by_date=collections.defaultdict(list)
 for e in ATTENDANCE:by_date[e["date"]].append(e)
 schedules={}
 dates=list(by_date)
 with concurrent.futures.ThreadPoolExecutor(max_workers=5) as pool:
  results=pool.map(lambda d:(d,schedule(d)),dates)
  for d,games in results:schedules[d]=games
 assigned={}
 for date,entries in by_date.items():
  used=set()
  for e in entries:
   away_id=team_id(e["away"]);home_id=team_id(e["home"])
   matches=[g for g in schedules[date] if g["teams"]["away"]["team"]["id"]==away_id and g["teams"]["home"]["team"]["id"]==home_id]
   matches.sort(key=lambda g:(integer(g.get("gameNumber")),g.get("gameDate",""),g["gamePk"]))
   chosen=next((g for g in matches if g["gamePk"] not in used),None)
   if chosen:used.add(chosen["gamePk"])
   assigned[e["attendance_id"]]=chosen
 return assigned
def game_data(e,g):
 if not g:
  return {**e,"match_status":"unmatched","verified":False}
 gamepk=g["gamePk"];teams=g.get("teams",{})
 home=teams.get("home",{});away=teams.get("away",{})
 venue=g.get("venue",{})
 record={**e,"game_pk":gamepk,"match_status":"matched","verified":True,
 "away_score":away.get("score"),"home_score":home.get("score"),
 "mlb_home_team":home.get("team",{}).get("name",e["home"]),
 "mlb_away_team":away.get("team",{}).get("name",e["away"]),
 "venue_official":venue.get("name"),"game_date_utc":g.get("gameDate"),
 "game_number":g.get("gameNumber"),"double_header":g.get("doubleHeader"),
 "game_type":g.get("gameType"),"status_detail":g.get("status",{}).get("detailedState"),
 "source_url":f"https://www.mlb.com/gameday/{gamepk}",
 "stat_status":"pending_boxscore","scoring_status":"pending_playbyplay",
 "innings":[],"attendance":None}
 return record
def parse_pitch_stats(stats):
 if not stats:return None
 fields=("gamesPitched","gamesStarted","wins","losses","saves","saveOpportunities","holds","blownSaves",
 "inningsPitched","hits","runs","earnedRuns","baseOnBalls","strikeOuts","homeRuns",
 "hitBatsmen","wildPitches","balks","numberOfPitches","strikes","battersFaced","pitchesThrown")
 p={k:stats.get(k) for k in fields if stats.get(k) is not None}
 p["outs"]=inning_outs(stats.get("inningsPitched"))
 return p
def parse_bat(stats):
 if not stats:return None
 keys=("atBats","plateAppearances","runs","hits","doubles","triples","homeRuns","rbi","baseOnBalls","intentionalWalks","strikeOuts","hitByPitch","stolenBases","caughtStealing","sacFlies","sacBunts","groundIntoDoublePlay","leftOnBase","totalBases")
 b={k:stats.get(k) for k in keys if stats.get(k) is not None}
 # Some older games do not provide PA; do not infer absent HBP/sacs as zeros.
 if "plateAppearances" not in b and all(k in b for k in ["atBats","baseOnBalls","hitByPitch","sacFlies","sacBunts"]):
  b["plateAppearances"]=sum(integer(b[k]) for k in ["atBats","baseOnBalls","hitByPitch","sacFlies","sacBunts"])
 return b
def parse_box(e,box):
 result=[]
 for side in ("away","home"):
  t=box.get("teams",{}).get(side,{})
  team=t.get("team",{})
  for key,p in t.get("players",{}).items():
   stats=p.get("stats",{})
   batting=parse_bat(stats.get("batting"))
   pitching=parse_pitch_stats(stats.get("pitching"))
   fielding=stats.get("fielding") or None
   if not batting and not pitching and not fielding:continue
   person=p.get("person",{})
   player_id=person.get("id") or integer(key.replace("ID",""))
   result.append({"game_pk":e["game_pk"],"attendance_id":e["attendance_id"],
      "date":e["date"],"team_id":team.get("id"),"team":team.get("name"),
      "player_id":player_id,"name":person.get("fullName"),"position":p.get("position",{}).get("abbreviation"),
      "batting":batting,"pitching":pitching,"fielding":fielding})
 return result
def parse_linescore(e,lines):
 innings=[]
 for v in lines.get("innings",[]):
  innings.append({"inning":v.get("num"),"away":(v.get("away") or {}).get("runs"),"home":(v.get("home") or {}).get("runs")})
 e["innings"]=innings
 return innings
def parse_scoring(plays):
 output=[]
 for p in plays.get("allPlays",[]):
  about=p.get("about",{})
  if not about.get("isScoringPlay"):continue
  desc=p.get("result",{}).get("description") or p.get("result",{}).get("event") or ""
  if not desc:continue
  output.append({"inning":about.get("inning"),"half":about.get("halfInning"),
    "description":desc,"event":p.get("result",{}).get("event"),
    "rbi":p.get("result",{}).get("rbi"),"at_bat_index":about.get("atBatIndex"),
    "source":"mlb-statsapi-playbyplay"})
 return output
def enrich(e):
 if not e.get("game_pk"):return e,[],[]
 pk=e["game_pk"];rows=[];plays=[]
 try:
  b=get_json(f"{API}/game/{pk}/boxscore")
  rows=parse_box(e,b)
  info=b.get("info",[])
  for item in info:
   if item.get("label","").strip(": ").lower()=="attendance":
    raw=str(item.get("value","")).replace(",","")
    if raw.isdigit():e["attendance"]=int(raw)
  e["stat_status"]="verified" if rows else "unavailable"
 except Exception as exc:e["stat_status"]="error";e["stat_error"]=str(exc)[:150]
 try:
  lines=get_json(f"{API}/game/{pk}/linescore")
  parse_linescore(e,lines)
 except Exception as exc:e["linescore_error"]=str(exc)[:120]
 try:
  plays=parse_scoring(get_json(f"{API}/game/{pk}/playByPlay"))
  e["scoring_status"]="verified" if plays else "unavailable"
 except Exception as exc:e["scoring_status"]="error";e["scoring_error"]=str(exc)[:120]
 return e,rows,plays
def write_json(name,data):(DATA/name).write_text(json.dumps(data,ensure_ascii=False,indent=2)+"\n",encoding="utf8")
def main():
 p=argparse.ArgumentParser();p.add_argument("--pilot",action="store_true");p.add_argument("--all",action="store_true");args=p.parse_args()
 if not args.pilot and not args.all:p.error("Select --pilot or --all")
 keep={e["attendance_id"] for e in ATTENDANCE if args.all or e["attendance_id"] in PILOT_IDS}
 matched=match_games()
 enriched=[game_data(e,matched[e["attendance_id"]]) if e["attendance_id"] in keep else {**e,"match_status":"pending","verified":False} for e in ATTENDANCE]
 todo=[g for g in enriched if g["attendance_id"] in keep and g.get("game_pk")]
 player_rows=[];scoring={}
 with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
  for e,rows,events in pool.map(enrich,todo):
   player_rows.extend(rows);scoring[str(e["game_pk"])]=events
   print("VERIFIED",e["attendance_id"],e["date"],e["game_pk"],e["stat_status"],len(rows),"player rows",len(events),"scoring plays",flush=True)
 previous_games={}
 previous_rows=[];previous_scoring={}
 if args.pilot:
  try:previous_games={x["attendance_id"]:x for x in json.loads((DATA/"games.json").read_text())}
  except (FileNotFoundError,ValueError):pass
  try:previous_rows=json.loads((DATA/"player_stats.json").read_text())
  except (FileNotFoundError,ValueError):pass
  try:previous_scoring=json.loads((DATA/"scoring_plays.json").read_text())
  except (FileNotFoundError,ValueError):pass
  enriched=[previous_games.get(g["attendance_id"],g) if g["attendance_id"] not in keep else g for g in enriched]
  player_rows=previous_rows+[r for r in player_rows if r["attendance_id"] in keep and r["attendance_id"] not in {x["attendance_id"] for x in previous_rows}]
  previous_scoring.update(scoring);scoring=previous_scoring
 write_json("games.json",enriched)
 write_json("player_stats.json",player_rows)
 write_json("scoring_plays.json",scoring)
 stats=collections.Counter(g["stat_status"] for g in enriched if g.get("stat_status"))
 report={"source_count":len(ATTENDANCE),"attempted":len(keep),"matched":sum(bool(g.get("game_pk")) for g in enriched),
 "player_rows":len(player_rows),"statuses":dict(stats),
 "doubleheaders":[{"date":e["date"],"id":e["attendance_id"],"game_pk":e.get("game_pk")} for e in enriched if e["date"]=="2022-08-02" and e["home"]=="San Diego Padres"],
 "unmatched":[{"id":g["attendance_id"],"date":g["date"],"away":g["away"],"home":g["home"]} for g in enriched if g.get("match_status")=="unmatched"],
 "timestamp":datetime.datetime.now(datetime.timezone.utc).isoformat(),"source":"MLB StatsAPI"}
 write_json("import_report.json",report)
 print("REPORT",json.dumps(report),flush=True)
if __name__=="__main__":main()
