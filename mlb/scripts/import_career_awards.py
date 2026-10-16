#!/usr/bin/env python3
"""Match MLB career honors to the precise MLB player IDs in attendance gamebooks.

Source: official MLB StatsAPI historical award recipient lists.
Honors are CAREER distinctions, not necessarily awards won in attended seasons.
MVP = AL/NL regular-season MVP (excludes World Series, All-Star, other MVPs).
Cy Young = AL/NL Cy Young, plus pre-1967 combined MLB Cy Young where relevant.
Gold Glove = regular AL/NL Rawlings Gold Glove, not Platinum/All-Time/MiLB.
Silver Slugger = regular AL/NL Silver Slugger, not team MVP awards.
MLB All-Star = official ALAS and NLAS award recipients, deduplicated by season.
National Baseball Hall of Fame = verified MLBHOF recipient, not eligibility.
"""
import concurrent.futures,datetime,json,pathlib,time,urllib.request,urllib.error
ROOT=pathlib.Path(__file__).resolve().parents[1];D=ROOT/"data"
stats=json.loads((D/"player_stats.json").read_text(encoding="utf-8"))
unique={}
for r in stats:
 if r.get("player_id") is not None:unique[str(r["player_id"])]=r.get("name") or f"MLB #{r['player_id']}"
CATEGORIES={
 "MLBHOF":("hall_of_fame",None),"ALMVP":("mvp","AL"),"NLMVP":("mvp","NL"),
 "ALCY":("cy_young","AL"),"NLCY":("cy_young","NL"),"MLBCY":("cy_young","MLB"),
 "ALGG":("gold_glove","AL"),"NLGG":("gold_glove","NL"),
 "ALSS":("silver_slugger","AL"),"NLSS":("silver_slugger","NL"),
 "ALAS":("all_star","AL"),"NLAS":("all_star","NL")
}
def fetch(item):
 award_id=item
 url=f"https://statsapi.mlb.com/api/v1/awards/{award_id}/recipients"
 for attempt in range(3):
  try:
   req=urllib.request.Request(url,headers={"Accept":"application/json","User-Agent":"CourtsideArchive/1.0 (personal statistics archive)"})
   with urllib.request.urlopen(req,timeout=55) as res: obj=json.load(res)
   if "awards" not in obj:raise ValueError(f"award endpoint {award_id} returned no awards")
   return award_id,obj["awards"]
  except Exception:
   if attempt==2:raise
   time.sleep(0.7*(attempt+1))
players={pid:{"name":name,"hall_of_fame":None,"mvp":[],"cy_young":[],"gold_glove":[],"silver_slugger":[],"all_star":[]} for pid,name in unique.items()}
source_counts={}
with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
 for award_id,records in pool.map(fetch,CATEGORIES):
  kind,league=CATEGORIES[award_id]
  matched=0
  for award in records:
   p=award.get("player") or {}
   pid=str(p.get("id",""))
   if pid not in players:continue
   year=award.get("season") or str(award.get("date",""))[:4]
   try:year=int(year)
   except (ValueError,TypeError):continue
   if year>2026:continue
   matched+=1
   if kind=="hall_of_fame":
    # If a player ever occurs more than once, use their first verified class.
    prior=players[pid]["hall_of_fame"]
    if prior is None or year<prior["year"]:
     players[pid]["hall_of_fame"]={"year":year,"source_id":award_id,
       "source":"https://www.mlb.com/news/hall-of-fame-inductions-by-year"}
   else:
    record={"year":year,"league":league}
    notes=award.get("notes")
    if notes:record["notes"]=str(notes)
    if kind=="all_star":
     if not any(r["year"]==year for r in players[pid]["all_star"]):players[pid]["all_star"].append({"year":year})
    elif record not in players[pid][kind]:players[pid][kind].append(record)
  source_counts[award_id]={"recipient_records":len(records),"matched_records":matched}
for val in players.values():
 for k in ["mvp","cy_young","gold_glove","silver_slugger","all_star"]:
  val[k].sort(key=lambda x:(x["year"],x.get("league",""),x.get("notes","")))
retained={pid:p for pid,p in players.items() if p["hall_of_fame"] or any(p[k] for k in ["mvp","cy_young","gold_glove","silver_slugger","all_star"])}
output={"_meta":{
  "source":"Official MLB StatsAPI annual awards/recipients (MLB player IDs)",
  "source_url":"https://statsapi.mlb.com/api/v1/awards",
  "hall_of_fame_confirmation":"https://www.mlb.com/news/hall-of-fame-inductions-by-year",
  "career_scope":"Awarded at any point through MLB's latest officially posted honors, not necessarily during an attended season.",
  "mvp_definition":"American and National League regular-season MVP awards only",
  "cy_young_definition":"AL/NL and historical combined MLB Cy Young awards only",
  "gold_glove_definition":"Rawlings AL/NL standard Gold Glove awards only",
  "silver_slugger_definition":"AL/NL standard Silver Slugger awards only",
  "all_star_definition":"Official MLB All-Star selections deduplicated by year; not All-MLB Team or All-Star Game appearances",
  "player_pool":len(unique),"honored_players":len(retained),
  "inductees":sum(bool(x["hall_of_fame"]) for x in retained.values()),
  "award_recipients":{k:sum(bool(x[k]) for x in retained.values()) for k in ["mvp","cy_young","gold_glove","silver_slugger","all_star"]},
  "sources":source_counts,"imported_utc":datetime.datetime.now(datetime.timezone.utc).isoformat()},
 "players":retained}
assert len(unique)>300
assert output["_meta"]["inductees"]>=10,output["_meta"]
assert output["_meta"]["award_recipients"]["mvp"]>=10,output["_meta"]
assert output["_meta"]["award_recipients"]["gold_glove"]>=15,output["_meta"]
assert output["_meta"]["award_recipients"]["silver_slugger"]>=15,output["_meta"]
(D/"career_awards.json").write_text(json.dumps(output,indent=2,ensure_ascii=False)+"\n",encoding="utf8")
print("MLB CAREER AWARDS REPORT",json.dumps(output["_meta"],ensure_ascii=False),flush=True)
print("MLB HOF",[(p["name"],p["hall_of_fame"]["year"]) for p in retained.values() if p["hall_of_fame"]],flush=True)
