#!/usr/bin/env python3
"""Import official pitcher decisions for the 131 attended MLB games.

Official StatsAPI /game/{gamePk}/decisions, with historical live-feed fallback.
Missing save in a successfully verified decision record means there was no save.
The result is game-pk keyed, with MLB person IDs for profile links.
"""
import concurrent.futures,json,pathlib,time,urllib.error,urllib.request
D=pathlib.Path(__file__).resolve().parents[1]/"data"
games=json.loads((D/"games.json").read_text(encoding="utf8"))
API="https://statsapi.mlb.com/api"
def request(url):
 err=None
 for attempt in range(3):
  try:
   req=urllib.request.Request(url,headers={"User-Agent":"CourtsideArchive/1.0 (personal baseball records)","Accept":"application/json"})
   with urllib.request.urlopen(req,timeout=22) as f:return json.load(f)
  except (urllib.error.URLError,TimeoutError,ValueError) as exc:
   err=exc
   if attempt<2:time.sleep(0.35*(attempt+1))
 raise err
def person(p):
 if not p:return None
 return {"id":p.get("id"),"name":p.get("fullName") or p.get("name") or p.get("nameFirstLast") }
def decisions(g):
 pk=g["game_pk"]
 try:
  data=request(f"{API}/v1/game/{pk}/decisions")
  record=data.get("decisions",data)
  if record.get("winner") and record.get("loser"):
   return str(pk),{"status":"verified","winner":person(record.get("winner")),"loser":person(record.get("loser")),"save":person(record.get("save")),
     "source":f"https://statsapi.mlb.com/api/v1/game/{pk}/decisions"}
 except Exception as exc:primary_error=str(exc)
 else:primary_error="Missing winner and loser"
 try:
  # Older historical games may expose decisions only in the completed game feed.
  data=request(f"{API}/v1.1/game/{pk}/feed/live")
  record=data.get("liveData",{}).get("decisions",{})
  if record.get("winner") and record.get("loser"):
   return str(pk),{"status":"verified","winner":person(record.get("winner")),"loser":person(record.get("loser")),"save":person(record.get("save")),
     "source":f"https://statsapi.mlb.com/api/v1.1/game/{pk}/feed/live"}
 except Exception as exc:fallback_error=str(exc)
 else:fallback_error="Missing decisions in live feed"
 return str(pk),{"status":"unavailable","winner":None,"loser":None,"save":None,
   "note":f"No verified game decision (decision endpoint: {primary_error}; feed: {fallback_error})"[:300]}
def main():
 output={}
 with concurrent.futures.ThreadPoolExecutor(max_workers=6) as executor:
  for pk,record in executor.map(decisions,games):
   output[pk]=record
   print(f"DECISION {pk} {record['status']} winner={record['winner']['name'] if record['winner'] else 'N/A'} loser={record['loser']['name'] if record['loser'] else 'N/A'} save={record['save']['name'] if record['save'] else 'None'}",flush=True)
 check=[g["game_pk"] for g in games]
 assert len(check)==len(set(check))==131
 assert len(output)==131
 statuses={}
 for value in output.values():statuses[value["status"]]=statuses.get(value["status"],0)+1
 report={"games":len(output),"statuses":statuses,"save_games":sum(bool(x.get("save")) for x in output.values())}
 print("DECISIONS REPORT",json.dumps(report),flush=True)
 (D/"decisions.json").write_text(json.dumps(output,indent=2,ensure_ascii=False)+"\n",encoding="utf8")
 if statuses.get("verified",0)<120:raise SystemExit("Too few official verified decisions; review endpoint coverage")
if __name__=="__main__":main()
