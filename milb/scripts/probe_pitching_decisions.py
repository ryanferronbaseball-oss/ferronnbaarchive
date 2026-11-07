#!/usr/bin/env python3
"""Research historical MiLB pitching decisions from official MLB stats endpoints, no write."""
import concurrent.futures,json,urllib.parse,urllib.request,urllib.error
API="https://statsapi.mlb.com/api/v1"
P=[648307,647969,388116,750871]
H={"Accept":"application/json","User-Agent":"CourtsideArchive-Decision-Probe/1.0"}
def get(url):
 try:
  req=urllib.request.Request(url,headers=H)
  with urllib.request.urlopen(req,timeout=18) as r:return r.status,json.load(r)
 except urllib.error.HTTPError as e:return e.code,None
 except Exception as e:return "error:"+str(e)[:100],None
def examine(pk):
 urls={
 "game_decisions":f"{API}/game/{pk}/decisions",
 "v11_game_decisions":f"https://statsapi.mlb.com/api/v1.1/game/{pk}/decisions",
 "boxscore":f"{API}/game/{pk}/boxscore",
 "schedule_decisions":f"{API}/schedule?gamePk={pk}&hydrate=decisions",
 "schedule_game":f"{API}/schedule?gamePk={pk}",
 "gamefeed_v11":f"https://statsapi.mlb.com/api/v1.1/game/{pk}/feed/live",
 }
 for label,url in urls.items():
  code,j=get(url)
  if not isinstance(j,dict):
   print("PROBE",pk,label,"status",code,flush=True);continue
  value={"keys":list(j.keys())[:17]}
  if label=="boxscore":
   value.update({"pitchingNotes":j.get("pitchingNotes"),"info":j.get("info")[:12] if j.get("info") else None,
      "teams":list((j.get("teams") or {}).keys())})
   for side in ("away","home"):
    b=(j.get("teams") or {}).get(side) or {}
    ps=b.get("players") or {}
    value[side]={"pitchers":b.get("pitchers"),"player0":list(ps.items())[:1],"note":b.get("note")}
    # print only pitcher-specific detailed stats, no PII beyond player ids/names
    pitchers=b.get("pitchers") or []
    value[side]["sample_pitchers"]=[{"id":p,"name":((ps.get("ID"+str(p)) or {}).get("person") or {}).get("fullName"),
       "gameStats":(ps.get("ID"+str(p)) or {}).get("stats",{}).get("pitching"),
       "seasonStats":(ps.get("ID"+str(p)) or {}).get("seasonStats",{}).get("pitching")} for p in pitchers[:2]]
    value[side].pop("player0")
  if label.startswith("schedule"):
   ds=j.get("dates") or []
   value["games"]=[{"pk":g.get("gamePk"),"keys":list(g.keys()),"decisions":g.get("decisions"),"winningPitcher":g.get("winningPitcher"),"losingPitcher":g.get("losingPitcher"),"savePitcher":g.get("savePitcher")} for d in ds for g in d.get("games",[])[:1]]
  if label=="gamefeed_v11":
   value["liveDecisions"]=(j.get("liveData") or {}).get("decisions")
  print("PROBE",pk,label,"status",code,json.dumps(value,ensure_ascii=False)[:3600],flush=True)
with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:list(pool.map(examine,P))
