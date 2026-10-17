#!/usr/bin/env python3
"""Inspect official athletics box-score HTML structure for the five-game pilot.
Diagnostic only. This script DOES NOT publish or fabricate player stats.
"""
import json
import re
from pathlib import Path
import requests
from bs4 import BeautifulSoup
ROOT=Path(__file__).resolve().parents[1]
BATCH=json.loads((ROOT/"data/verified_batches/2026_auburn_regional_pilot.json").read_text())["games"]
output=[]
session=requests.Session()
session.headers["User-Agent"]="Mozilla/5.0 (compatible; CourtsideArchive-Verification/1.0; source audit)"
for game in BATCH:
    url=game["source_url"]
    print("SOURCE",game["id"],url,flush=True)
    result={"game_id":game["id"],"source":url,"status":"pending","tables":[]}
    try:
        req=session.get(url,timeout=25)
        req.raise_for_status()
        soup=BeautifulSoup(req.text,"html.parser")
        result.update({"status":"reachable","http_code":req.status_code,"html_bytes":len(req.content),
                       "page_title":soup.title.get_text(" ",strip=True) if soup.title else None})
        print("HTML",req.status_code,len(req.content),"title",result["page_title"],flush=True)
        for i,table in enumerate(soup.find_all("table")):
            trs=table.find_all("tr")
            if not trs:continue
            head=[]
            thead=table.find("thead")
            if thead:
                for th in thead.find_all("th"):
                    t=th.get_text(" ",strip=True)
                    if t:head.append(t)
            if not head:
                ths=trs[0].find_all("th")
                head=[th.get_text(" ",strip=True) for th in ths if th.get_text(" ",strip=True)]
            first=[]
            for row in trs[:3]:
                first.append([td.get_text(" ",strip=True)[:40] for td in row.find_all(["td","th"])][:10])
            classes=table.get("class",[])
            item={"index":i,"classes":classes,"head":head[:24],
                  "nrows":len(trs),"first_rows":first}
            result["tables"].append(item)
            if any("AB"==str(s).strip().upper() for s in head) or any("IP"==str(s).strip().upper() for s in head):
                print("PLAYER TABLE",i,"HEAD",head[:24],"ROWS",len(trs),"FIRST",first[:2],flush=True)
        print("TABLE SUMMARY",len(result["tables"]),[{"index":t["index"],"head":t["head"][:10],"nrows":t["nrows"]} for t in result["tables"][:18]],flush=True)
        if not result["tables"]:
            raise RuntimeError("Page has no HTML scorebook tables")
    except Exception as exc:
        result["status"]="error";result["error"]=repr(exc)
        print("SOURCE ERROR",game["id"],repr(exc),flush=True)
    output.append(result)
out=ROOT/"output"/"pilot-source-inspection.json"
out.parent.mkdir(parents=True,exist_ok=True)
out.write_text(json.dumps(output,indent=2)+"\n")
print("REACHABLE",sum(x["status"]=="reachable" for x in output),"/",len(output),flush=True)
if sum(x["status"]=="reachable" for x in output)<3:
    raise SystemExit("Fewer than three official boxscore pages accessible: manual/PDF source needed.")
