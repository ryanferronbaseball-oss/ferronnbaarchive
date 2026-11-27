#!/usr/bin/env python3
"""Recover explicit official pitching BF, only for attended 2019 college games."""
import json, re, unicodedata
from pathlib import Path
from itertools import permutations
from concurrent.futures import ThreadPoolExecutor
import requests
from bs4 import BeautifulSoup
from import_sidearm_pilot import table_head, table_rows, normalize_name, innings_outs

D=Path(__file__).resolve().parents[1]/"data"
def load(n): return json.loads((D/n).read_text())
def dump(n,v): (D/n).write_text(json.dumps(v,ensure_ascii=False,indent=2)+"\n")
# Directly inspected official pitching tables: name, IP, H, R, ER, BB, SO, BF.
SEEDS={}
FIELDS=("outs","hits","runs","earnedRuns","baseOnBalls","strikeOuts")
def norm(s):
    return re.findall(r"[a-z0-9]+",unicodedata.normalize("NFKD",s).encode("ascii","ignore").decode().lower())
def name_match(source, archived):
    a=norm(normalize_name(source)); b=norm(archived)
    if a==b: return True
    # Accept only exact surname tokens, with optional matching abbreviated first name.
    if len(a)==1: return a[0] in b[1:]
    if b and a==b[1:]: return True
    return len(a)>1 and len(b)>1 and a[1:]==b[1:] and (a[0]==b[0] or (len(a[0])==1 and b[0].startswith(a[0])) or (len(b[0])==1 and a[0].startswith(b[0])))
def align(table, arms):
    if len(table)!=len(arms): raise ValueError("pitching row count differs")
    matches=[]; used=set()
    for name,ip,h,r,er,bb,so,bf in table:
        sig=(innings_outs(ip,name),h,r,er,bb,so)
        if bf < bb+so+h: raise ValueError("impossible BF: "+name)
        candidates=[i for i,p in enumerate(arms) if i not in used and name_match(name,p["player"]) and tuple(p["pitching"].get(k) for k in FIELDS)==sig]
        if len(candidates)!=1: raise ValueError("ambiguous source pitcher: "+name)
        i=candidates[0]; used.add(i); matches.append((arms[i],bf))
    return matches
def get_tables(g):
    if g["id"] in SEEDS: return SEEDS[g["id"]],"manually verified official BF column"
    resp=requests.get(g["source_url"],timeout=30,headers={"User-Agent":"Mozilla/5.0"})
    resp.raise_for_status()
    soup=BeautifulSoup(resp.text,"html.parser")
    y,m,d=map(int,g["date"].split("-"))
    page=soup.get_text(" ",strip=True)
    if not any(v in page for v in (f"{m}/{d}/{y}",f"{m:02}/{d:02}/{y}",f"{m}/{d:02}/{y}",f"{m:02}/{d}/{y}")): raise ValueError("date not confirmed")
    tables=[]
    for t in soup.find_all("table"):
        hd=table_head(t)
        if not all(k in hd for k in ("Player","IP","H","R","ER","BB","SO","BF")): continue
        lines=table_rows(t,hd)
        vals=[]; totals=[]
        for line in lines:
            if line.get("_totals"): totals.append(int(line["BF"])); continue
            vals.append((line["Player"],line["IP"],*[int(line[k]) for k in ("H","R","ER","BB","SO","BF")]))
        if not vals or len(totals)!=1 or sum(x[-1] for x in vals)!=totals[0]: raise ValueError("source BF totals not reconciled")
        if vals not in tables: tables.append(vals)
    if len(tables)!=2: raise ValueError("expected two explicit BF pitching tables, found "+str(len(tables)))
    return tables,"official HTML BF column and source team totals"
games=[g for g in load("games.json") if g.get("season") ==2019 and not g.get("boxscore_backfill_excluded")]
rows=load("player_stats.json")
existing={g["game_id"] for g in load("source_stat_backfills.json")["games"]}
def inspect(g):
    gid=g["id"]; result={"game_id":gid,"date":g["date"],"away":g["away"],"home":g["home"],"source_url":g.get("source_url")}
    arms=[r for r in rows if r["game_id"]==gid and r.get("pitching") is not None]
    if gid in existing: return dict(result,status="existing_verified_backfill"),[]
    if not arms: return dict(result,status="unresolved",reason="no pitching rows"),[]
    if all(p["pitching"].get("battersFaced") is not None for p in arms): return dict(result,status="already_complete",pitchers=len(arms)),[]
    try:
        tables,method=get_tables(g)
        teams=[g["away"],g["home"]]; solutions=[]
        for order in permutations(teams):
            try:
                matches=[pair for t,team in zip(tables,order) for pair in align(t,[p for p in arms if p["team"]==team])]
                solutions.append(matches)
            except ValueError: pass
        if len(solutions)!=1: raise ValueError("unable to uniquely match both full pitching tables to archived names and IP/H/R/ER/BB/K")
        matches=solutions[0]
        for p,bf in matches:
            old=p["pitching"].get("battersFaced")
            if old is not None and old!=bf: raise ValueError("existing BF conflict: "+p["player"])
        # Cross-check BF using opponent AB, BB and available supplemental batting totals.
        for team in teams:
            opp=next(t for t in teams if t!=team)
            batting=[r["batting"] for r in rows if r["game_id"]==gid and r["team"]==opp and r.get("batting") is not None]
            bf=sum(n for p,n in matches if p["team"]==team)
            fields=("atBats","baseOnBalls","hitByPitch","sacBunts","sacFlies","catcherInterference")
            if not batting or any(b.get(k) is None for b in batting for k in fields[:2]): raise ValueError("opponent AB/BB unavailable")
            known=sum(b.get(k) or 0 for b in batting for k in fields)
            if bf<known or (all(b.get(k) is not None for b in batting for k in fields) and bf!=known): raise ValueError("opponent PA conflicts with BF")
        changes=[(p,bf) for p,bf in matches if p["pitching"].get("battersFaced") is None]
        return dict(result,status="recovered",method=method,pitchers=len(matches),added=len(changes),values=[{"player_id":p["player_id"],"team":p["team"],"BF":bf} for p,bf in matches]),changes
    except Exception as e: return dict(result,status="unresolved",reason=str(e)),[]
with ThreadPoolExecutor(max_workers=5) as pool: results=list(pool.map(inspect,games))
report=[]
for result,changes in results:
    report.append(result)
    for p,bf in changes: p["pitching"]["battersFaced"]=bf
    print(result["game_id"],result["status"],result.get("added",result.get("reason","")),flush=True)
if any(x["status"]=="recovered" and x["added"] for x in report): dump("player_stats.json",rows)
dump("bf_audit_2019.json",{"scope":"2019 college baseball only; exact official BF; missing fields only","games":report})
