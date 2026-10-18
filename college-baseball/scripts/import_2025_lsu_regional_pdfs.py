#!/usr/bin/env python3
"""Precisely transcribe and independently verify two official LSU Regional PDFs.

May 31 Dallas Baptist at LSU (LSU531.pdf) and June 1 LSU at Little Rock
(LSU601.pdf). Originals: LSU athletics single-page gamebooks. Do not infer
data not in source. Every batting row is tied to its original position and
every pitching line is reconciled against opponent totals. Preserve 2026.
"""
from pathlib import Path
import json
import hashlib
import re
import requests
import pymupdf
from import_sidearm_pilot import slug

D=Path(__file__).resolve().parents[1]/"data"
def B(name,pos,ab,r,h,rbi,bb,so):return [name,pos,ab,r,h,rbi,bb,so]
def P(name,outs,h,r,er,bb,so,np):return [name,outs,h,r,er,bb,so,np]
GAMES=[
dict(id="cb-2025-06-01-lsu-little-rock-att0369",date="2025-06-01",
 url="https://static.lsusports.net/assets/docs/bb/25stats/LSU601.pdf",
 away="LSU",home="Little Rock",score=[4,10],hits=[11,8],errors=[0,2],
 innings=[[3,0],[0,2],[0,4],[0,0],[1,0],[0,0],[0,0],[0,4],[0,None]],
 pitchers={"LSU":[
 P("Jaden Noot",4,3,2,2,2,2,50),P("Chase Shores",3,1,4,4,3,2,39),
 P("Cooper Williams",11,3,0,0,1,4,52),P("Jacob Mayers",4,0,4,4,4,2,36),
 P("Mavrick Rizy",2,1,0,0,1,0,21)],
 "Little Rock":[
 P("Noah Burkey",5,6,3,3,0,1,40),P("Brenden Katz",5,2,0,0,2,1,37),
 P("Hunter Royal",1,0,0,0,1,0,8),P("Malcolm Brown",16,3,1,1,1,3,89)]},
 bats={"LSU":[
 [B("Derek Curiel","LF",4,1,3,0,1,0)],
 [B("Jared Jones","1B",5,1,1,0,0,1)],
 [B("Daniel Dickinson","2B",3,1,1,0,1,0),B("Dalton Beck","PH",1,0,0,0,0,1)],
 [B("Jake Brown","RF",2,0,0,0,0,0),B("John Pearson","PH",1,0,0,0,0,0),B("Josh Pearson","PR/RF",2,0,0,0,0,1)],
 [B("Ethan Frey","DH",4,0,0,0,1,1)],
 [B("Steven Milam","SS",3,0,2,2,1,0)],
 [B("Luis Hernandez","C",4,1,3,0,0,0)],
 [B("Michael Braswell III","3B",2,0,0,0,0,0),B("Ashton Larson","PH",1,0,1,0,0,0),B("Tanner Reaves","3B",1,0,0,0,0,0)],
 [B("Chris Stanfield","CF",4,0,0,0,0,1)]],
 "Little Rock":[
 [B("Alex Seguine","SS",3,1,0,0,2,1)],
 [B("Zach Henry","CF",4,0,1,1,0,2)],
 [B("Ryan Geck","DH",3,0,0,0,0,0),B("Jayce Blalock","PH/DH",1,1,0,0,1,1)],
 [B("Ty Rhoades","3B",4,1,0,1,1,2)],
 [B("Cade Martin","C",3,1,1,0,2,1)],
 [B("Cooper Chaplain","2B",3,2,2,1,2,1)],
 [B("Angel Cano","1B",5,2,2,5,0,1)],
 [B("Sammy Harris","RF",3,1,2,0,1,0)],
 [B("Reed Willbanks","LF",1,1,0,1,2,1)]]},
 official_batting={"LSU":[37,4,11,2,4,5],"Little Rock":[30,10,8,9,11,10]},
 decisions={"win":"Brenden Katz","loss":"Chase Shores","save":"Malcolm Brown"},
 pdf_markers=["NCAA Baton Rouge Regional","#1 LSU at Little Rock","Jun 01, 2025","LSU 4","Little Rock 10","Score by Innings"]),
dict(id="cb-2025-05-31-dallas-baptist-lsu-att0367",date="2025-05-31",
 url="https://static.lsusports.net/assets/docs/bb/25stats/LSU531.pdf",
 away="Dallas Baptist",home="LSU",score=[0,12],hits=[4,10],errors=[4,0],
 innings=[[0,2],[0,1],[0,3],[0,0],[0,1],[0,2],[0,0],[0,3],[0,None]],
 pitchers={"Dallas Baptist":[
 P("Micah Bucknam",8,4,6,3,2,2,65),P("James Ellwanger",13,4,3,3,3,5,92),
 P("Avery Duncan",2,2,3,2,1,1,23),P("Zach Todd",1,0,0,0,1,0,10)],
 "LSU":[
 P("Kade Anderson",21,4,0,0,2,11,106),P("DJ Primeaux",1,0,0,0,2,0,18),
 P("Jacob Mayers",2,0,0,0,1,1,13),P("William Schmidt",3,0,0,0,0,3,30)]},
 bats={"Dallas Baptist":[
 [B("Michael Dattalo","3B",4,0,0,0,1,3)],
 [B("Nathan Humphreys","CF",3,0,0,0,1,1)],
 [B("Grant Jay","LF",4,0,0,0,0,3)],
 [B("Tom Poole","DH",3,0,1,0,1,1)],
 [B("Chayton Krauss","1B",3,0,0,0,1,1)],
 [B("Keaton Grady","2B",3,0,1,0,0,1),B("Landon Underhill","PH",1,0,0,0,0,1)],
 [B("Ben Tryon","RF",4,0,1,0,0,1)],
 [B("Adam Berghult","C",3,0,0,0,0,2),B("Joey Nerat","PH",1,0,0,0,0,1)],
 [B("Luke Heefner","SS",2,0,1,0,0,0),B("Cody Grebeck","SS",0,0,0,0,1,0)]],
 "LSU":[
 [B("Derek Curiel","LF",3,0,1,1,2,0),B("Josh Pearson","PH/LF",1,0,0,0,0,1)],
 [B("Jared Jones","1B",5,0,0,0,0,3)],
 [B("Daniel Dickinson","2B",3,1,0,0,2,1),B("John Pearson","PR/3B",0,0,0,0,0,0)],
 [B("Jake Brown","RF/CF",5,1,0,0,0,1)],
 [B("Ethan Frey","DH",4,3,2,2,1,1)],
 [B("Steven Milam","SS",2,4,2,0,2,0)],
 [B("Luis Hernandez","C",2,1,1,2,0,0),B("Cade Arrambide","PH/C",1,1,1,0,0,0)],
 [B("Michael Braswell III","3B",3,0,0,0,0,1),B("Ashton Larson","PH/RF",0,0,0,1,0,0)],
 [B("Chris Stanfield","CF",4,1,3,3,0,0),B("Dalton Beck","PH",1,0,0,0,0,0),B("Tanner Reaves","2B",0,0,0,0,0,0)]]},
 official_batting={"Dallas Baptist":[31,0,4,0,5,15],"LSU":[34,12,10,9,7,8]},
 decisions={"win":"Kade Anderson","loss":"Micah Bucknam","save":None},
 pdf_markers=["NCAA Baton Rouge Regional","#20 Dallas Baptist at #1 LSU","May 31, 2025","Dallas Baptist 0","LSU 12","Score by Innings"])
]

def verify_source(g):
    response=requests.get(g["url"],timeout=40,headers={"User-Agent":"Mozilla/5.0 Courtside Archive source checker"})
    response.raise_for_status()
    data=response.content
    if not data.startswith(b"%PDF"):raise ValueError("University source did not return PDF bytes")
    pdf=pymupdf.open(stream=data,filetype="pdf")
    if pdf.page_count!=1:raise ValueError("University one-page regional gamebook changed")
    txt=" ".join(pdf[0].get_text("text").split())
    condensed=re.sub(r"[^a-z0-9]+","",txt.lower())
    for m in g["pdf_markers"]:
        if re.sub(r"[^a-z0-9]+","",m.lower()) not in condensed:
            raise ValueError("Official PDF identity or score not present: "+m)
    for team,entries in g["bats"].items():
        for slot in entries:
            for name,*_ in slot:
                # PDF's layout may separate name components; match surname,
                # when unique, with full identity separately in typed manifest.
                last=name.split()[-1].lower()
                if last=="iii":last="braswell"
                if last not in condensed:
                    raise ValueError("PDF source batter surname missing: "+name)
    return hashlib.sha256(data).hexdigest()

def main():
    games=json.loads((D/"games.json").read_text())
    rows=json.loads((D/"player_stats.json").read_text())
    report=json.loads((D/"import_report.json").read_text())
    byid={g["id"]:g for g in games}
    keys={(r["game_id"],r["player_id"]) for r in rows}
    original_2026={g["id"]:json.dumps(g,sort_keys=True) for g in games if g["date"].startswith("2026")}
    prior_2026_rows=[r for r in rows if r["game_id"] in original_2026]
    if len(games)!=444 or len(keys)!=len(rows):raise ValueError("Original attendance or player IDs not intact")
    audits=[];newgames=0
    for source in GAMES:
        g=byid[source["id"]]
        if (g["date"],g["away"],g["home"])!=(source["date"],source["away"],source["home"]):
            raise ValueError("LSU PDF identity differs from original attendance")
        if g.get("boxscore_backfill_excluded"):raise ValueError("JUCO not eligible")
        if g["verification"]=="official_boxscore_verified":
            if not any(r["game_id"]==g["id"] for r in rows):raise ValueError("Already verified game missing player stats")
            continue
        if g["verification"]!="attendance_only":raise ValueError("Unexpected prior source status")
        sha=verify_source(source)
        team_audits=[];new_rows=[]
        if len(source["innings"])!=9 or any(len(p)!=2 for p in source["innings"]):
            raise ValueError("Incomplete NCAA innings")
        if [sum(x[i] or 0 for x in source["innings"]) for i in range(2)]!=source["score"]:
            raise ValueError("PDF final score does not match innings")
        for team in (source["away"],source["home"]):
            bat=[]
            for i,slot in enumerate(source["bats"][team],1):
                for ix,(name,pos,ab,runs,hits,rbi,bb,so) in enumerate(slot):
                    if any(v<0 for v in (ab,runs,hits,rbi,bb,so)) or hits>ab:
                        raise ValueError("Impossible source hitter stats "+name)
                    bat.append({"game_id":g["id"],"player_id":"cb-"+slug(team)+"-"+slug(name),
                      "player":name,"team":team,"position":pos,"source_url":source["url"],
                      "source_type":"official_university_pdf","verification":"official_boxscore_verified",
                      "batting_slot":i,"batting_sub_index":ix,"batting_appearance_index":len(bat),
                      "batting":{"atBats":ab,"runs":runs,"hits":hits,"rbi":rbi,
                                 "baseOnBalls":bb,"strikeOuts":so,
                                 "doubles":None,"triples":None,"homeRuns":None,
                                 "stolenBases":None,"caughtStealing":None,
                                 "hitByPitch":None,"sacBunts":None,"sacFlies":None}})
            if len(source["bats"][team])!=9:raise ValueError("Nine original batting slots required")
            abtot=[sum(x["batting"][s] for x in bat) for s in ("atBats","runs","hits","rbi","baseOnBalls","strikeOuts")]
            if abtot!=source["official_batting"][team]:
                raise ValueError(f"Official PDF batter totals mismatch {team}: {abtot}")
            new_rows.extend(bat)
            pitchers=[]
            for ix,(name,outs,hits,runs,er,bb,so,np) in enumerate(source["pitchers"][team]):
                pid="cb-"+slug(team)+"-"+slug(name)
                found=[a for a in new_rows if a["player_id"]==pid and a["team"]==team]
                if len(found)>1:raise ValueError("Two-way duplicate in university PDF")
                if found:rec=found[0]
                else:
                    rec={"game_id":g["id"],"player_id":pid,"player":name,"team":team,
                         "position":"P","source_url":source["url"],
                         "source_type":"official_university_pdf","verification":"official_boxscore_verified"}
                    new_rows.append(rec)
                rec["pitching_appearance_index"]=ix
                rec["pitching"]={"outs":outs,"hits":hits,"runs":runs,"earnedRuns":er,
                   "baseOnBalls":bb,"strikeOuts":so,"numberOfPitches":np,
                   "wins":int(name==source["decisions"]["win"]),
                   "losses":int(name==source["decisions"]["loss"]),
                   "saves":int(name==source["decisions"]["save"])}
                pitchers.append(rec)
            opp=source["home"] if team==source["away"] else source["away"]
            oi=source["score"][1] if team==source["away"] else source["score"][0]
            hi=source["hits"][1] if team==source["away"] else source["hits"][0]
            if (sum(p["pitching"]["runs"] for p in pitchers)!=oi or
                sum(p["pitching"]["hits"] for p in pitchers)!=hi):
                raise ValueError("PDF pitcher vs opposing hitter/score totals mismatch "+team)
            if sum(p["pitching"]["outs"] for p in pitchers)!=(24 if team==source["away"] and source["score"][1]>=source["score"][0] else 27):
                raise ValueError("PDF pitcher recorded outs mismatch "+team)
            team_audits.append({"team":team,"batters":len(bat),"pitchers":len(pitchers),
                               "batting_totals":abtot})
        newkeys={(x["game_id"],x["player_id"]) for x in new_rows}
        if len(newkeys)!=len(new_rows) or newkeys&keys:raise ValueError("PDF player ID collision")
        rows.extend(new_rows);keys.update(newkeys)
        g.update({"verification":"official_boxscore_verified","official_boxscore_status":"verified",
           "source_url":source["url"],"source_type":"official_university_pdf",
           "score_provenance":"official_boxscore","game_type":"ncaa_postseason",
           "postseason_round":"NCAA Regional","neutral_site":True,
           "ballpark":"Alex Box Stadium / Skip Bertman Field","city":"Baton Rouge","state":"LA",
           "away_score":source["score"][0],"home_score":source["score"][1],
           "away_hits":source["hits"][0],"home_hits":source["hits"][1],
           "away_errors":source["errors"][0],"home_errors":source["errors"][1],
           "pitching_decisions":source["decisions"],
           "innings":[{"inning":i+1,"away":x[0],"home":x[1]}
                      for i,x in enumerate(source["innings"])],
        })
        newgames+=1
        audits.append({"game_id":g["id"],"source_url":source["url"],"source_sha256":sha,
                       "score":source["score"],"teams":team_audits,
                       "rows_added":len(new_rows),"lineup_slots":9,
                       "decisions":source["decisions"]})
        print("PASS official one-page PDF",g["id"],len(new_rows),flush=True)
    if not newgames:
        print("Prior official LSU PDFs already imported; no change",flush=True)
        return
    if any(json.dumps(byid[k],sort_keys=True)!=val for k,val in original_2026.items()):
        raise ValueError("2026 changed during PDF import")
    if [r for r in rows if r["game_id"] in original_2026]!=prior_2026_rows:
        raise ValueError("2026 player rows changed")
    rows.sort(key=lambda r:(r["game_id"],r["team"],r.get("batting_slot",99),
                            r.get("batting_sub_index",99),
                            r.get("pitching_appearance_index",99),r["player_id"]))
    report.update({"official_player_boxscores_imported":sum(g["verification"]=="official_boxscore_verified" for g in games),
       "player_stat_rows":len(rows),"unique_player_ids":len({r["player_id"] for r in rows}),
       "official_score_and_inning_lines_matched":sum(g["verification"]!="attendance_only" for g in games),
       "attendance_only_pending_official_verification":sum(g["verification"]=="attendance_only" for g in games),
       "latest_verified_batch":"2025 LSU official NCAA Regional PDFs (5/31 and 6/1)"})
    report.setdefault("2025_backfill",{})["verified_player_gamebooks"]=sum(g["date"].startswith("2025") and g["verification"]=="official_boxscore_verified" for g in games)
    report["2025_backfill"]["remaining_attendance_only"]=74-report["2025_backfill"]["verified_player_gamebooks"]
    audit={"status":"PASS","official_source":"Louisiana State University athletics NCAA Baton Rouge Regional single-page PDFs",
           "games":audits,"2026_untouched":True,"original_attendance_games":len(games)}
    for fname,obj in [("games.json",games),("player_stats.json",rows),("import_report.json",report),
                       ("2025_lsu_regional_pdf_audit.json",audit)]:
        (D/fname).write_text(json.dumps(obj,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print("LSU PDF final reconciliation PASS",newgames,"games",flush=True)

if __name__=="__main__":main()
