#!/usr/bin/env python3
"""Import and independently reconcile the five official Auburn Regional boxscores.

Reads Sidearm HTML from each university athletics source linked in the reviewed
pilot manifest, rejects incomplete stats, identity collisions, and team-level
AB/R/H/RBI/BB/SO inconsistencies. Draft branch only; NEVER published directly.
"""
import hashlib
import json
import re
import unicodedata
from collections import defaultdict
from pathlib import Path

import requests
from bs4 import BeautifulSoup

ROOT=Path(__file__).resolve().parents[1]
D=ROOT/"data"
PILOT=json.loads((D/"verified_batches/2026_auburn_regional_pilot.json").read_text())["games"]
session=requests.Session()
session.headers["User-Agent"]="Mozilla/5.0 (compatible; CourtsideArchive Official-Gamebook-Audit/1.0)"

def slug(s):
    s=unicodedata.normalize("NFKD",s).encode("ascii","ignore").decode().lower()
    return re.sub(r"(^-|-$)","",re.sub(r"-+","-",re.sub(r"[^a-z0-9]+","-",s)))

def normalize_name(text,position=None):
    text=re.sub(r"\([^)]*\)$","",text).strip()
    text=re.sub(r"\s+"," ",text).strip()
    # Sidearm Milwaukee marks certain name cells "rf McCraine, Mason".
    if position and text.lower().startswith(position.lower()+" "):
        text=text[len(position):].strip()
    text=re.sub(r"^(?:\d+\s+)?(?:ph|pr|dh|ss|cf|rf|lf|1b|2b|3b|c|p|of|if|ph/dh|pr/dh)\s+","",text,flags=re.I)
    if "," in text:
        last,first=text.split(",",1)
        text=first.strip()+" "+last.strip()
    return text.strip()

def table_head(table):
    thead=table.find("thead")
    if not thead:return []
    return [th.get_text(" ",strip=True).strip() for th in thead.find_all("th")]

def table_rows(table,head):
    body=table.find("tbody")
    trs=body.find_all("tr",recursive=False) if body else table.find_all("tr")[1:]
    foot=table.find("tfoot")
    if foot:trs+=foot.find_all("tr",recursive=False)
    result=[]
    for tr in trs:
        cells=tr.find_all(["td","th"],recursive=False)
        vals=[]
        for cell in cells:
            text=cell.get_text(" ",strip=True)
            span=int(cell.get("colspan","1"))
            if span>1 and text.strip().casefold()=="totals":
                vals.extend([""]*(span-1)+[text])
            else:
                vals.extend([text]*span)
        # Some Sidearm composite tables render batting lines as two physical
        # cells: position, then "name AB R H ... PO A", even though the header
        # exposes 20 logical columns. Reconstruct exactly the final 18 integers.
        if len(vals)!=len(head) and len(head)==20 and len(vals)==2:
            tokens=vals[1].split()
            if len(tokens)>=19 and all(re.fullmatch(r"\d+",x) for x in tokens[-18:]):
                vals=[vals[0]," ".join(tokens[:-18]),*tokens[-18:]]
        if len(vals)!=len(head):
            continue
        if any(x.strip().lower()=="totals" for x in vals[:2]):
            result.append({"_totals":True,**{h:v for h,v in zip(head,vals)}})
            continue
        if not any(vals):continue
        result.append(dict(zip(head,vals)))
    return result

def number(v,key,where):
    v=str(v).strip()
    if not re.fullmatch(r"\d+",v):
        raise ValueError(f"{where} - invalid {key} {v!r}")
    return int(v)

def innings_outs(v,where):
    match=re.fullmatch(r"(\d+)\.([012])",str(v).strip())
    if not match:
        raise ValueError(f"{where} - Invalid baseball innings {v!r}; decimals are outs, not tenths")
    return 3*int(match.group(1))+int(match.group(2))

def batting_rows(table_s,table_d,game_id,team,url):
    h1=table_head(table_s);h2=table_head(table_d)
    short=table_rows(table_s,h1);detail=table_rows(table_d,h2)
    if len(short)!=len(detail) or len(short)<9:
        print("DEBUG COMPOSITE",game_id,team,"headers",h2,"counts",len(short),len(detail),flush=True)
        for tr in table_d.find_all("tr")[:5]:
            print("DEBUG CELLS",[{"text":td.get_text(" ",strip=True)[:60],
                "span":td.get("colspan","1")} for td in tr.find_all(["td","th"],recursive=False)][:28],flush=True)
        raise ValueError(f"{game_id} {team}: simple/detail row count mismatch {len(short)} vs {len(detail)}")
    people=[];totals=None
    for i,(s,x) in enumerate(zip(short,detail)):
        if s.get("_totals") or x.get("_totals"):
            if not s.get("_totals") or not x.get("_totals"):
                raise ValueError(f"{game_id} {team}: batting totals not aligned")
            totals={key:number(s[key],key,f"{team}: totals") for key in ("AB","R","H","RBI","BB","SO")}
            assert totals["AB"]==number(x["AB"],"AB",team)
            continue
        for key in ("AB","R","H","RBI","BB","SO"):
            if number(s[key],key,team)!=number(x[key],key,team):
                raise ValueError(f"{game_id} {team} row {i}: summary/composite {key} disagree")
        pos=(s.get("Position") or s.get("Pos") or x.get("POS") or "").strip()
        pname=normalize_name(s["Player"],pos)
        if not pname or pname.casefold()=="totals":
            raise ValueError(f"{game_id} {team}: invalid hitter name {s.get('Player')}")
        vals={key:number(x[key],key,pname) for key in ("AB","R","H","RBI","2B","3B","HR","BB","SB","CS","HBP","SH","SF","SO")}
        # A listed pitcher with no offensive contribution did not necessarily
        # take a plate appearance. Keep them through the pitching table only.
        if pos.lower()=="p" and not any(vals.values()):
            continue
        record={
          "game_id":game_id,"player_id":"cb-"+slug(team)+"-"+slug(pname),"player":pname,
          "team":team,"position":pos or None,"source_url":url,
          "source_type":"official_sidearm_boxscore","verification":"official_boxscore_verified",
          "batting":{"atBats":vals["AB"],"runs":vals["R"],"hits":vals["H"],
            "doubles":vals["2B"],"triples":vals["3B"],"homeRuns":vals["HR"],
            "rbi":vals["RBI"],"baseOnBalls":vals["BB"],"strikeOuts":vals["SO"],
            "stolenBases":vals["SB"],"caughtStealing":vals["CS"],
            "hitByPitch":vals["HBP"],"sacBunts":vals["SH"],"sacFlies":vals["SF"]}}
        people.append(record)
    if totals is None:
        for label,table in (("simple",table_s),("details",table_d)):
            print("DEBUG TOTALS",game_id,team,label,"tr count",len(table.find_all("tr")),
                "tfoot",bool(table.find("tfoot")),flush=True)
            for tr in table.find_all("tr")[-3:]:
                print("DEBUG ROW",label,[{"text":cell.get_text(" ",strip=True)[:35],
                    "span":cell.get("colspan","1")} for cell in tr.find_all(["td","th"],recursive=False)],flush=True)
        raise ValueError(f"{game_id} {team}: batting totals missing")
    for k,field in [("AB","atBats"),("R","runs"),("H","hits"),("RBI","rbi"),("BB","baseOnBalls"),("SO","strikeOuts")]:
        actual=sum(p["batting"][field] for p in people)
        if actual!=totals[k]:
            raise ValueError(f"{game_id} {team}: batter {k} total {actual} != official {totals[k]}")
    if len({p["player_id"] for p in people})!=len(people):
        raise ValueError(f"{game_id} {team}: duplicate hitter identity")
    return people,totals

def pitching_rows(table,game_id,team,url):
    head=table_head(table)
    rows=table_rows(table,head)
    people=[]
    for r in rows:
        if r.get("_totals"):continue
        pname=normalize_name(r["Player"])
        if not pname:raise ValueError(f"{game_id}: missing pitcher")
        p={"outs":innings_outs(r["IP"],pname)}
        for name,key in [("H","hits"),("R","runs"),("ER","earnedRuns"),("BB","baseOnBalls"),
                         ("SO","strikeOuts"),("NP","numberOfPitches"),("HBP","hitBatsmen")]:
            p[key]=number(r[name],name,pname)
        people.append({"game_id":game_id,"player_id":"cb-"+slug(team)+"-"+slug(pname),
            "player":pname,"team":team,"source_url":url,"source_type":"official_sidearm_boxscore",
            "verification":"official_boxscore_verified","pitching":p})
    if len({p["player_id"] for p in people})!=len(people):
        raise ValueError(f"{game_id} {team}: duplicate pitcher identity")
    if not people:raise ValueError(f"{game_id} {team}: no pitchers parsed")
    return people

def official_tables(html,game):
    soup=BeautifulSoup(html,"html.parser")
    tables=soup.find_all("table")
    short=[];detail=[];pitch=[]
    for i,t in enumerate(tables):
        h=table_head(t)
        if all(x in h for x in ("AB","R","H","RBI","BB","SO")) and "2B" in h and "SF" in h:
            detail.append(t)
        elif all(x in h for x in ("AB","R","H","RBI","BB","SO")) and "2B" not in h:
            short.append(t)
        elif all(x in h for x in ("IP","H","R","ER","BB","SO","NP")):
            pitch.append(t)
    if [len(short),len(detail),len(pitch)]!=[2,2,2]:
        raise ValueError(f"{game['id']}: expected 2 batting summaries, 2 complete batting lines and 2 pitching sets; found {[len(short),len(detail),len(pitch)]}")
    return short,detail,pitch

def scrape(game):
    url=game["source_url"]
    print("VERIFY",game["id"],url,flush=True)
    resp=session.get(url,timeout=30)
    resp.raise_for_status()
    html=resp.text
    if len(html)<50000:raise ValueError(f"{game['id']}: official boxscore HTML unexpectedly short")
    short,detail,pitch=official_tables(html,game)
    # Some Sidearm athletics feeds put the page's host school first even when
    # it is the designated home side. Identify each table by BOTH official
    # batting runs and hits, not its position or inferred home/away status.
    order=[]
    for batting_table in short:
        total=next((r for r in table_rows(batting_table,table_head(batting_table))
                    if r.get("_totals")),None)
        if total is None:raise ValueError(f"{game['id']}: missing table R/H totals for team ordering")
        rhs=(number(total["R"],"R",game["id"]),number(total["H"],"H",game["id"]))
        if rhs==(game["away_score"],game["away_hits"]):
            order.append(game["away"])
        elif rhs==(game["home_score"],game["home_hits"]):
            order.append(game["home"])
        else:
            raise ValueError(f"{game['id']}: batting R/H {rhs} matches neither team")
    if set(order)!={game["away"],game["home"]} or len(order)!=2:
        raise ValueError(f"{game['id']}: duplicated/unidentified team order {order}")
    teams=order
    row_by_id={}
    audit={"game_id":game["id"],"source":url,"http_code":resp.status_code,
           "source_bytes":len(resp.content),"source_sha256":hashlib.sha256(resp.content).hexdigest(),
           "teams":[]}
    for i,team in enumerate(teams):
        bats,total=batting_rows(short[i],detail[i],game["id"],team,url)
        pitchers=pitching_rows(pitch[i],game["id"],team,url)
        for person in bats+pitchers:
            pid=person["player_id"]
            if pid not in row_by_id:
                row_by_id[pid]={"game_id":game["id"],"player_id":pid,"player":person["player"],
                   "team":team,"position":person.get("position"),
                   "source_url":url,"source_type":"official_sidearm_boxscore",
                   "verification":"official_boxscore_verified"}
            rec=row_by_id[pid]
            for field in ("batting","pitching"):
                if field in person:
                    if field in rec:raise ValueError(f"Duplicate {field} player {pid} in {game['id']}")
                    rec[field]=person[field]
        side="away" if team==game["away"] else "home"
        if total["R"]!=game[side+"_score"]:
            raise ValueError(f"{game['id']} {team}: R mismatch vs known official scoreboard")
        if total["H"]!=game[side+"_hits"]:
            raise ValueError(f"{game['id']} {team}: H mismatch vs official scoreboard")
        audit["teams"].append({"name":team,"batters":len(bats),"pitchers":len(pitchers),"AB":total["AB"],
                                "R":total["R"],"H":total["H"],"RBI":total["RBI"],"BB":total["BB"],"SO":total["SO"],
                                "pitching_outs":sum(p["pitching"]["outs"] for p in pitchers),
                                "pitching_runs":sum(p["pitching"]["runs"] for p in pitchers),
                                "pitching_hits":sum(p["pitching"]["hits"] for p in pitchers)})
        print("TEAM",team,json.dumps(audit["teams"][-1]),flush=True)
    for i in range(2):
        own=audit["teams"][i];other=audit["teams"][1-i]
        if own["pitching_hits"]!=other["H"] or own["pitching_runs"]!=other["R"]:
            raise ValueError(f"{game['id']}: {own['name']} pitching totals don't reconcile opponent hitting")
    decisions={}
    audit["source_warnings"]=[]
    for result in ("winner","loser","save"):
        expected=game.get(result)
        matched=[r for r in row_by_id.values() if "pitching" in r and expected
                 and slug(r["player"])==slug(expected)]
        if not expected:
            decisions[result]=None
        elif len(matched)==1:
            decisions[result]=matched[0]["player_id"]
        else:
            # NCAA school webpages can contain a mismatch between the stated
            # W/L and the actual pitcher table. Preserve the published winner/
            # loser at GAME level but do not credit a nonexistent pitcher.
            decisions[result]=None
            audit["source_warnings"].append(
                f"Official {result} label {expected!r} does not appear in that game's pitcher lines; "
                "individual pitcher W/L attribution intentionally unavailable.")
    for r in row_by_id.values():
        if "pitching" in r:
            # Null is intentional: a source-disputed decision cannot be treated
            # as an actual recorded zero-loss event for every pitcher.
            for result,field in (("winner","wins"),("loser","losses"),("save","saves")):
                r["pitching"][field]=(int(r["player_id"]==decisions[result])
                    if decisions[result] else (0 if not game.get(result) else None))
    if audit["source_warnings"]:
        print("SOURCE WARNING",game["id"],json.dumps(audit["source_warnings"]),flush=True)
    if len(row_by_id)<17:
        raise ValueError(f"{game['id']}: too few player boxscore rows {len(row_by_id)}")
    audit["player_rows"]=len(row_by_id)
    audit["status"]="PASS"
    return list(row_by_id.values()),audit

def main():
    rows=[];reports=[]
    for g in PILOT:
        source_rows,report=scrape(g)
        rows.extend(source_rows);reports.append(report)
    if len(reports)!=5 or len(set(x["game_id"] for x in reports))!=5:
        raise ValueError("Pilot must contain exactly five different official games")
    if len({(x["game_id"],x["player_id"]) for x in rows})!=len(rows):
        raise ValueError("Duplicate player game ID in output")
    rows.sort(key=lambda x:(x["game_id"],x["team"],x["player"]))
    manifest={"status":"PASS","pilot_games":5,"player_rows":len(rows),
              "source":"official athletic department Sidearm gamebooks, matched by date/team/innings",
              "games":reports,"total_source_batters":sum(x["batters"] for r in reports for x in r["teams"]),
              "total_source_pitchers":sum(x["pitchers"] for r in reports for x in r["teams"])}
    out=D/"pilot_player_stats_verified.json"
    audit=D/"pilot_player_stat_audit.json"
    out.write_text(json.dumps(rows,indent=2,ensure_ascii=False)+"\n")
    audit.write_text(json.dumps(manifest,indent=2)+"\n")
    print("PILOT VERIFIED",len(reports),"games,",len(rows),"unique player-game rows. PARITY PASS",flush=True)

if __name__=="__main__":main()
