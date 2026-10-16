#!/usr/bin/env python3
"""Import witnessed NCAA football gamebooks from official school websites.

SIDEARM HTML table schemas vary (2017-19 vs 2025). We classify columns from
the actual source and preserve source provenance. No unknown values are zeroed.
2017 Western New Mexico uses a contemporary USD recap; that game's PPR is
intentionally not computed from incomplete individual statistics.
"""
from __future__ import annotations
import collections
import hashlib
import json
import pathlib
import re
import urllib.request
from bs4 import BeautifulSoup

ROOT=pathlib.Path(__file__).resolve().parents[1]
DATA=ROOT/"data"
GAMES=json.loads((DATA/"games.json").read_text())
ROWS=[]
SCORING={}
REPORT=[]
PPR=[]
def clean(x):
 return re.sub(r"\s+"," ",str(x or "")).strip()
def number(s):
 try:return float(re.sub(r"[^\d.\-]","",str(s)))
 except (ValueError,TypeError):return None
def val(a,i,default=""):
 return clean(a[i]) if len(a)>i else default
def canonical(name,team):
 name=clean(name)
 if team=="USD":
  known={"LAWRENCE, A":"Anthony Lawrence","MARTINEZ, E":"Emilio Martinez",
         "PRIEST, Justin":"Justin Priest","BANDY, Michael":"Michael Bandy",
         "SINNETT, Reid":"Reid Sinnett","KINCAID, Dalton":"Dalton Kincaid",
         "DWELLEY, Ross":"Ross Dwelley"}
  if name.upper() in {k.upper() for k in known}:
   return next(v for k,v in known.items() if k.upper()==name.upper())
 if "," in name:
  last,first=[z.strip() for z in name.split(",",1)]
  if first and last:return clean(first+" "+last.title())
 return name.title() if name.isupper() else name
def identity(n,team):
 n=canonical(n,team)
 # Stable names across attended games; no cross-school identity guessed.
 normalized=re.sub(r"[^a-z0-9]+","-",n.lower()).strip("-")
 return "cfb-"+re.sub(r"[^a-z0-9]+","-",team.lower())+"-"+normalized
def row(g,team,name,category,labels,values):
 if not name or name.lower() in ("team","totals","total") or name.startswith("-"):return
 name=canonical(name,team)
 athlete_id=identity(name,team)
 if not any(clean(v) for v in values):return
 ROWS.append(dict(game_id=g["id"],date=g["date"],espn_event_id=g.get("espn_event_id"),team=team,
  team_id=team,athlete_id=athlete_id,player=name,category=category,
  stat_values=[clean(v) for v in values],stat_labels=labels,stat_keys=labels,
  source=g["boxscore_url"]))
def fetch(url):
 req=urllib.request.Request(url,headers={"User-Agent":"Mozilla/5.0 (compatible; CourtsideArchive/1.0; personal historical stats)"})
 with urllib.request.urlopen(req,timeout=45) as h:return BeautifulSoup(h.read(),"html.parser")
def detect(t):
 trs=t.find_all("tr")
 if not trs:return None
 # Several official tables have multirow headers, so use the very first row
 # with a Player heading or its first thead tr.
 headings=[" ".join(clean(h.get_text(" ",strip=True)).lower().split()) for h in t.select("thead th")]
 if not headings:return None
 hs=" ".join(headings)
 if "player" not in hs:return None
 if "cmp" in hs and "att" in hs and ("yds" in hs or "yds." in hs):return "passing"
 if "gain" in hs and "net" in hs and "loss" in hs:return "rushing"
 if "rec." in hs and "long" in hs and "td" in hs:return "receiving"
 if "solo" in hs and "ast" in hs and "tot" in hs:return "defensive"
 if "punts" in hs and "kickoffs" in hs and "interceptions" in hs:return "returns"
 if "qtr" in hs and "result" in hs and "yds" in hs:return "field_goals"
 if "punts" in hs and "avg" in hs and "long" in hs:return "punting"
 if "kicks" in hs and "passes" in hs and "rushes" in hs:return "pat"
 # 2025 statistical header uses Punts./punts as separate
 return None
def body(t):
 entries=[]
 for tr in t.find_all("tr"):
  td=tr.find_all("td",recursive=False)
  if len(td)<2:continue
  cells=[clean(z.get_text(" ",strip=True)) for z in td]
  name=cells[0]
  if not name or name.lower() in ("totals","total","player","team","-"):continue
  if name.startswith("Totals"):continue
  entries.append(cells)
 return entries
def normalized_category_row(g,team,cat,cells):
 name=cells[0]
 v=cells[1:]
 if cat=="passing":
  if len(v)<7:return
  att=number(v[1]) or 0; yards=number(v[2]) or 0
  row(g,team,name,"passing",["C/ATT","YDS","AVG","TD","INT","SACKS","QBR","RTG"],
      [v[0]+"/"+v[1],v[2],("%.1f"%(yards/att) if att else ""),v[3],v[4],v[6]+"-0","",""])
 elif cat=="rushing":
  if len(v)<7:return
  row(g,team,name,"rushing",["CAR","YDS","AVG","TD","LONG"],[v[0],v[3],v[6],v[4],v[5]])
 elif cat=="receiving":
  if len(v)<4:return
  n=number(v[0]);y=number(v[1]);avg=("%.1f"%(y/n)) if n and y is not None else ""
  row(g,team,name,"receiving",["REC","YDS","AVG","TD","LONG","TGTS"],[v[0],v[1],avg,v[2],v[3],""])
 elif cat=="defensive":
  # SIDEARM 2017-19: Solo Ast Tot TFL/Yds TFL Sack/Yds Sacks FF FR-Yds
  #                   Fumbl INT INT BrUp Blkd QH
  # SIDEARM 2025:    Solo Ast Tot TFL/Yds Sack/Yds FF FR-Yds INT BrUp Blkd QH
  if len(v)<10:return
  classic=len(v)>=14
  sackcol=6 if classic else 4
  tfl=v[4] if classic else v[3]
  sacks=v[sackcol] if classic else v[sackcol].split("/")[0].strip()
  pd=v[12] if classic else v[8]
  row(g,team,name,"defensive",["TOT","SOLO","SACKS","TFL","PD","QB HTS","TD"],
      [v[2],v[0],sacks if number(sacks)is not None else "",tfl if number(tfl)is not None else "",pd if number(pd)is not None else "",v[-1] if number(v[-1])is not None else "",""])
 elif cat=="punting":
  if len(v)<7:return
  row(g,team,name,"punting",["NO","YDS","AVG","TB","In 20","LONG"],[v[0],v[1],v[2],v[5],v[4],v[3]])
 elif cat=="returns":
  if len(v)<9:return
  # This detailed 3x3 box score has punts, kickoffs and interceptions.
  for typ,offset in (("puntReturns",0),("kickReturns",3),("interceptions",6)):
   count=number(v[offset])
   if count is None or count<=0:continue
   if typ=="interceptions":
    row(g,team,name,"interceptions",["INT","YDS","TD"],[v[offset],v[offset+1],""])
   else:
    row(g,team,name,typ,["NO","YDS","AVG","LONG","TD"],[v[offset],v[offset+1],
      "%.1f"%((number(v[offset+1]) or 0)/count),v[offset+2],""])
def extract(g,soup):
 counts=collections.Counter()
 tables=soup.find_all("table")
 bycat=collections.defaultdict(list)
 for t in tables:
  cat=detect(t)
  if cat:bycat[cat].append(t)
 print("TABLE GROUPS",g["id"],{k:len(v) for k,v in bycat.items()},flush=True)
 for cat in ("passing","rushing","receiving","defensive","punting","returns"):
  pair=bycat[cat]
  for i,t in enumerate(pair[:2]):
   team=g["away_abbr"] if i==0 else g["home_abbr"]
   for cells in body(t):
    before=len(ROWS)
    normalized_category_row(g,team,cat,cells)
    if len(ROWS)>before:counts[cat]+=1
 # field-goal events + PATs -> standard kicker boxscore
 bykicker=collections.defaultdict(lambda:{"made":0,"attempt":0,"long":0,"xp_made":0,"xp_att":0})
 for i,t in enumerate(bycat["field_goals"][:2]):
  team=g["away_abbr"] if i==0 else g["home_abbr"]
  for cells in body(t):
   if len(cells)<5:continue
   a=bykicker[(team,cells[0])];a["attempt"]+=1
   if "GOOD" in cells[4].upper():
    a["made"]+=1;a["long"]=max(a["long"],int(number(cells[3]) or 0))
 for i,t in enumerate(bycat["pat"][:2]):
  team=g["away_abbr"] if i==0 else g["home_abbr"]
  for cells in body(t):
   if len(cells)<3:continue
   a=bykicker[(team,cells[0])];a["xp_att"]+=int(number(cells[1]) or 0)
   a["xp_made"]+=int(number(cells[2]) or 0)
 for (team,name),x in bykicker.items():
  row(g,team,name,"kicking",["FG","PCT","LONG","XP","PTS"],
   [str(x["made"])+"/"+str(x["attempt"]),("%.1f"%(100*x["made"]/x["attempt"]) if x["attempt"] else ""),
   str(x["long"]) if x["made"] else "",str(x["xp_made"])+"/"+str(x["xp_att"]),
   str(x["made"]*3+x["xp_made"])])
  counts["kicking"]+=1
 # Scoring plays: find the small official scoring table before statistical tables.
 scoring_candidates=[]
 for t in tables[:7]:
  heads=clean(t.get_text(" ",strip=True))[:180].lower()
  sample_rows=[]
  for tr in t.find_all("tr")[:18]:
   vals=[clean(x.get_text(" ",strip=True)) for x in tr.find_all("td",recursive=False)]
   if len(vals)>=5 and vals[-2].isdigit() and vals[-1].isdigit() and " - " in vals[-3]:
    sample_rows.append(vals)
  if sample_rows or ("scoring play" in heads):
   scoring_candidates.append(t)
 print("SCORING TABLES",g["id"],len(scoring_candidates),flush=True)
 scoring_rows=[]
 if scoring_candidates:
  for tr in scoring_candidates[0].find_all("tr"):
   td=tr.find_all("td",recursive=False)
   vals=[clean(x.get_text(" ",strip=True)) for x in td]
   # Modern web views put empty icon cell first, old views start Qtr.
   if len(vals)<5:continue
   a,b=str(g["away_score"]),str(g["home_score"])
   if vals[-2].isdigit() and vals[-1].isdigit():
    aa,hh=int(vals[-2]),int(vals[-1])
    desc=vals[-3]
    joined=" ".join(vals[:-3])
    match=re.search(r"\b(1st|2nd|3rd|4th|5th|OT)\b",joined,re.I)
    period={"1st":1,"2nd":2,"3rd":3,"4th":4,"5th":5,"ot":5}.get(match.group(1).lower(),0) if match else 0
    if not period or not desc or " - " not in desc:continue
    clock_match=re.search(r"\b\d{1,2}:\d\d\b",joined)
    clock=clock_match.group(0) if clock_match else "—"
    team=desc.split(" - ",1)[0].strip()
    if team!=g["away_abbr"] and team!=g["home_abbr"]:
     # 2025 scoring table prepends team image text but uses NCS/WFU in description
     continue
    kind=("field_goal" if "field goal" in desc.lower() else
      "touchdown" if ("yd " in desc.lower() or "touchdown" in desc.lower()) else "other")
    if kind=="field_goal":typ="Field Goal Good"
    elif "kickoff return" in desc.lower():typ="Kick Return Touchdown"
    elif "punt return" in desc.lower():typ="Punt Return Touchdown"
    elif "interception" in desc.lower():typ="Interception Return Touchdown"
    elif "fumble" in desc.lower():typ="Fumble Return Touchdown"
    elif "pass from" in desc.lower():typ="Passing Touchdown"
    elif "run" in desc.lower():typ="Rushing Touchdown"
    else:typ="Scoring Touchdown"
    old=scoring_rows[-1] if scoring_rows else dict(away_score=0,home_score=0)
    point_diff=(aa-old["away_score"]) if team==g["away_abbr"] else (hh-old["home_score"])
    scoring_rows.append(dict(id=g["id"]+"-"+str(len(scoring_rows)+1),period=period,clock=clock,
      team=team,kind=kind,type=typ,description=desc,points=max(0,point_diff),
      away_score=aa,home_score=hh,source=g["boxscore_url"]))
 if not scoring_rows:
  print("NO_SCORING_ROWS",g["id"],flush=True)
 SCORING[g["id"]]={"plays":scoring_rows}
 return counts
def recap(g):
 # Verified directly from 2017 USD game recap; partial by design.
 values=[
 ("USD","Anthony Lawrence","passing",["C/ATT","YDS","AVG","TD","INT","SACKS","QBR","RTG"],["15/28","187","6.7","2","","","",""]),
 ("WNMU","Javia Hall","passing",["C/ATT","YDS","AVG","TD","INT","SACKS","QBR","RTG"],["39/62","464","7.5","3","","","",""]),
 ("USD","Emilio Martinez","rushing",["CAR","YDS","AVG","TD","LONG"],["17","96","5.6","1",""]),
 ("USD","Blake Martin","rushing",["CAR","YDS","AVG","TD","LONG"],["14","54","3.9","",""]),
 ("USD","Justin Priest","receiving",["REC","YDS","AVG","TD","LONG","TGTS"],["4","95","23.8","1","",""]),
 ("WNMU","D'Angelo Bowie","receiving",["REC","YDS","AVG","TD","LONG","TGTS"],["19","263","13.8","2","",""]),
 ("USD","David Tolbert","defensive",["TOT","SOLO","SACKS","TFL","PD","QB HTS","TD"],["9","","","","","",""]),
 ("USD","Ray Clark","defensive",["TOT","SOLO","SACKS","TFL","PD","QB HTS","TD"],["9","","","","","",""]),
 ("USD","Kim Mahoney","defensive",["TOT","SOLO","SACKS","TFL","PD","QB HTS","TD"],["8","","","","","",""]),
 ("WNMU","Dominic Barry","defensive",["TOT","SOLO","SACKS","TFL","PD","QB HTS","TD"],["8","","","","","",""])
 ]
 for team,name,cat,keys,stats in values:row(g,team,name,cat,keys,stats)
 seq=[
 (1,"7:37","WNMU","Passing Touchdown","Javia Hall 8-yard touchdown pass to D'Angelo Bowie",7,7,0),
 (1,"3:10","WNMU","Passing Touchdown","Javia Hall 44-yard touchdown pass to Sean North",6,13,0),
 (1,"2:59","USD","Passing Touchdown","Anthony Lawrence 58-yard touchdown pass to Justin Priest",7,13,7),
 (1,"0:30","USD","Field Goal Good","Patrick Murray 32-yard field goal",3,13,10),
 (2,"0:56","USD","Rushing Touchdown","Zach Nelson 1-yard touchdown run",7,13,17),
 (3,"—","USD","Passing Touchdown","Anthony Lawrence 2-yard touchdown pass to Ross Dwelley",7,13,24),
 (3,"—","USD","Field Goal Good","Patrick Murray 34-yard field goal",3,13,27),
 (4,"11:06","WNMU","Passing Touchdown","Javia Hall 86-yard touchdown pass to D'Angelo Bowie",7,20,27),
 (4,"8:43","USD","Rushing Touchdown","Emilio Martinez 13-yard touchdown run",7,20,34)
 ]
 SCORING[g["id"]]={"plays":[dict(id=g["id"]+"-"+str(i+1),period=q,clock=clock,team=team,kind="field_goal" if typ=="Field Goal Good" else "touchdown",type=typ,description=desc,points=pts,away_score=a,home_score=h,source=g["boxscore_url"]) for i,(q,clock,team,typ,desc,pts,a,h) in enumerate(seq)]}
 return collections.Counter(x[2] for x in values)
def n(r,field):
 if r is None:return None
 ix=r["stat_labels"].index(field) if field in r["stat_labels"] else -1
 return number(r["stat_values"][ix]) if ix>=0 else None
def verified_return_tds():
 credits=collections.Counter()
 for g in GAMES:
  for play in SCORING.get(g["id"],{}).get("plays",[]):
   if play["type"] not in ("Kick Return Touchdown","Punt Return Touchdown"):continue
   text=play.get("description","")
   match=re.search(r"(?:^| - )(.+?)\s+\d+\s+yd\s+(?:kickoff|punt)\s+return",text,re.I)
   if not match:continue
   credited=canonical(match.group(1),play["team"])
   credits[(g["id"],identity(credited,play["team"]))]+=1
 return credits
def fantasy():
 # Source completeness policy: only the four full gamebooks qualify for PPR.
 groups=collections.defaultdict(list)
 return_scores=verified_return_tds()
 for r in ROWS:
  if r["game_id"]==GAMES[0]["id"]:continue
  groups[(r["game_id"],r["athlete_id"])].append(r)
 result=[]
 for (gid,aid),cat in groups.items():
  a={r["category"]:r for r in cat}
  if not any(t in a for t in ("passing","rushing","receiving")):continue
  def f(t,k):
   v=n(a.get(t),k);return v if v is not None else 0
  py=f("passing","YDS"); pt=f("passing","TD"); ints=f("passing","INT")
  ry=f("rushing","YDS");rt=f("rushing","TD")
  rec=f("receiving","REC");vy=f("receiving","YDS");vt=f("receiving","TD")
  # Individual interception throws and documented yardage are counted only
  # where corresponding source statistical categories exist.
  return_td=return_scores.get((gid,aid),0)
  score=round(py*.04+pt*4-ints*2+ry*.1+rt*6+rec+vy*.1+vt*6+return_td*6,2)
  r=cat[0];g=next(x for x in GAMES if x["id"]==gid)
  result.append({"game_id":gid,"date":g["date"],"athlete_id":aid,"player":r["player"],"team":r["team"],
   "opponent":g["home_abbr"] if r["team"]==g["away_abbr"] else g["away_abbr"],
   "fantasy_ppr":score,"stat_line":{"passing_yards":py,"passing_tds":pt,"interceptions_thrown":ints,
    "rushing_yards":ry,"rushing_tds":rt,"receptions":rec,"receiving_yards":vy,"receiving_tds":vt,
    "fumbles_lost":0,"offensive_two_point_conversions":0,"kick_punt_return_tds":return_td},
   "ppr_components":{"passing":round(py*.04+pt*4,2),"rushing":round(ry*.1+rt*6,2),
     "receiving":round(rec+vy*.1+vt*6,2),"turnovers":round(-ints*2,2),"two_point":0,"returns":return_td*6},
   "score_type":"traditional_full_ppr","source":g["boxscore_url"]})
 return sorted(result,key=lambda p:(-p["fantasy_ppr"],p["date"],p["player"]))
def main():
 for g in GAMES:
  try:
   if g["official_source_type"]=="game_recap":
    cats=recap(g)
   else:
    cats=extract(g,fetch(g["boxscore_url"]))
   p=SCORING.get(g["id"],{}).get("plays",[])
   status="complete" if sum(cats.values())>=25 and p and p[-1]["away_score"]==g["away_score"] and p[-1]["home_score"]==g["home_score"] else "partial"
   REPORT.append({"game_id":g["id"],"source":g["boxscore_url"],"status":status,
     "stat_category_rows":dict(cats),"player_rows":sum(cats.values()),"scoring_plays":len(p),
     "scoring_final_reconciled":bool(p and p[-1]["away_score"]==g["away_score"] and p[-1]["home_score"]==g["home_score"])})
   print("AUDIT",g["id"],status,"stats",sum(cats.values()),"scoring",len(p),flush=True)
  except Exception as err:
   print("IMPORT ERROR",g["id"],repr(err),flush=True)
   SCORING[g["id"]]={"plays":[]}
   REPORT.append({"game_id":g["id"],"status":"import_error","error":repr(err),"source":g["boxscore_url"]})
 ps=fantasy()
 counts={str(v):sum(p["fantasy_ppr"]>=v for p in ps) for v in (10,20,25,30,40)}
 data={"rules":{"name":"Traditional Full-PPR (ESPN-style)","passing_yards":0.04,
   "passing_touchdowns":4,"interceptions_thrown":-2,"rushing_yards":0.1,"rushing_touchdowns":6,
   "receiving_yards":0.1,"receiving_touchdowns":6,"reception":1,"fumbles_lost":-2,
   "successful_offensive_two_point_conversion":2,"individual_kick_or_punt_return_touchdown":6,
   "excluded":["K/DST scoring","IDP scoring","bonuses","TE premiums","yardage return points"],
   "coverage_notice":"Individual kick or punt return touchdowns are included when identifiable in the official scoring summary; fumbles-lost are not deducted unless supported by individual evidence."},
  "eligibility":"Officially verified full player boxscores (excludes incomplete 2017 WNMU game). Missing turnover values are not deducted.",
  "audit":{"player_games":len(ps),"games_covered":list(dict.fromkeys(p["game_id"] for p in ps)),
           "milestones":counts},"performances":ps}
 for name,val in (("player_stats.json",ROWS),("scoring_plays.json",SCORING),("fantasy_ppr.json",data),("import_report.json",REPORT)):
  (DATA/name).write_text(json.dumps(val,ensure_ascii=False,indent=2)+"\n")
 print("FINISHED",len(ROWS),"category rows",len(ps),"PPR games",sum(len(x["plays"]) for x in SCORING.values()),"scores",flush=True)
if __name__=="__main__":main()
