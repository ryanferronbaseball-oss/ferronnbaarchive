#!/usr/bin/env python3
"""Inspect exact original April 13, 2024 GT university PDF and initialed players.
No writes and no changes to source records.
"""
import json
import requests
from pathlib import Path
from collections import Counter
from copy import deepcopy
from import_2024_pdf import parse,pdf_text
D=Path(__file__).resolve().parents[1]/"data"
rows=json.loads((D/"player_stats.json").read_text())
games=json.loads((D/"games.json").read_text())
for full,teams in (
    ("Ethan Lizama",("Western Kentucky","South Carolina")),
    ("Tate Soderstrom",("Arizona","UC San Diego")),
    ("Kyle Hvidsten",("Western Kentucky","Liberty")),
    ("Michael Graziano",("Georgia Tech","Mercer"))):
    last=full.split()[-1]
    matches=[r for r in rows if last.lower() in r["player"].lower() and r["team"] in teams]
    print("ALIAS SOURCES",full,[(t,list(sorted({(r["player"],r["player_id"]) for r in matches if r["team"]==t}))) for t in teams],flush=True)
OLD="cb-2024-04-14-virginia-tech-georgia-tech-att0268"
NEW="cb-2024-04-13-virginia-tech-georgia-tech-att0268"
old=next(g for g in games if g["id"]==OLD)
source="https://storage.googleapis.com/ramblinwreck-com-prod/2024/04/gt041324.pdf"
res=requests.get(source,timeout=45);res.raise_for_status()
print("PDF SOURCE",res.status_code,len(res.content),res.content[:5],flush=True)
print("PDF SCOREBOOK LINES",[(i,repr(v)) for i,v in enumerate(pdf_text(res.content).splitlines()) if ("ip h r er" in v.lower() or v.strip().startswith("Totals") or "Score by Innings" in v or "Cam Jones" in v or "Wyatt Parliament" in v or "Virginia Tech 0" in v or "Georgia Tech 19" in v)],flush=True)
g=deepcopy(old);g.update({"id":NEW,"date":"2024-04-13","away_score":None,"home_score":None})
item={"source_url":source,"official_score":[0,19],"date":"2024-04-13","source_type":"official_university_pdf_scorebook","worksheet_row":269}
keys={(r["game_id"],r["player_id"]) for r in rows if r["game_id"]!=OLD}
try:
    new,audit=parse(g,item,keys,res)
    print("NEW SCOREBOOK PASS",len(new),len([x for x in rows if x["game_id"]==OLD]),audit,flush=True)
    print("PH BATTERS",[(r["team"],r["player"],r.get("batting_slot"),r.get("batting_sub_index")) for r in new if r.get("batting_sub_index",0)>0],flush=True)
except Exception as e:
    print("NEW SCOREBOOK PARSER ERROR",type(e).__name__,str(e),flush=True)
    raise
