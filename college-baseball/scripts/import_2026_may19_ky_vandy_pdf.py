#!/usr/bin/env python3
"""Import official Vanderbilt/Kentucky May 19 SEC Tournament PDF gamebook.

Every printed athlete batting/pitching row and inning score is matched to
Vanderbilt's original two-page tournament gamebook before stats are committed.
"""
from io import BytesIO
import json
import re
from pathlib import Path
import requests
from pypdf import PdfReader
from import_sidearm_pilot import slug
from import_auburn_tamu_pdf_2026 import require_line

DATA=Path(__file__).resolve().parents[1]/"data"
ID="cb-2026-05-19-kentucky-vanderbilt-att0426"
PDF="https://storage.googleapis.com/vucommodores-prod/2026/05/VU57-vs-Kentucky-SECT-Box.pdf"
B={
 "Kentucky":[
  ("Jayce Tharnish","CF",4,0,0,0,0,2),
  ("Tyler Bell","SS",4,2,2,1,0,0),
  ("Luke Lawrence","2B",3,0,2,2,0,1),
  ("Ethan Hindle","DH",4,0,0,0,0,1),
  ("Hudson Brown","1B",4,0,0,0,0,0),
  ("Will Marcy","LF",3,1,0,0,1,3),
  ("Carson Hansen","RF",4,1,2,1,0,0),
  ("Owen Jenkins","C",4,0,2,1,0,1),
  ("Caeden Cloud","3B",3,1,0,0,1,2),
 ],
 "Vanderbilt":[
  ("Brodie Johnston","3B",4,1,2,3,1,0),
  ("Mike Mancini","2B",4,0,1,0,1,1),
  ("Braden Holcomb","LF",4,0,1,0,1,1),
  ("Logan Johnstone","RF",3,1,0,0,2,3),
  ("Tommy Goodin","1B",5,1,2,0,0,1),
  ("Ryker Waite","SS",4,1,1,1,0,1),
  ("Rustan Rigdon","CF",4,2,2,1,0,0),
  ("Colin Barczi","DH",4,1,2,1,0,1),
  ("Korbin Reynolds","C",3,1,1,0,0,0),
 ],
}
P={
 "Kentucky":[
  ("Jaxon Jelkin",17,7,5,4,3,4,99),
  ("Jack Sams",5,3,2,2,1,2,46),
  ("Nile Adcock",2,2,1,1,1,2,18)],
 "Vanderbilt":[
  ("Connor Fennell",14,7,4,4,1,5,90),
  ("Alex Kranzler",13,1,1,1,1,5,55)],
}
EXTRAS={
 "Tyler Bell":{"doubles":1,"homeRuns":1},
 "Luke Lawrence":{"doubles":1,"hitByPitch":1},
 "Carson Hansen":{"homeRuns":1,"stolenBases":1},
 "Caeden Cloud":{"stolenBases":1},
 "Colin Barczi":{"doubles":1},
 "Brodie Johnston":{"homeRuns":1},
 "Korbin Reynolds":{"hitByPitch":1},
 "Mike Mancini":{"stolenBases":1},
 "Rustan Rigdon":{"stolenBases":2},
}
TOTALS={
 "Kentucky":{"atBats":33,"runs":5,"hits":8,"rbi":5,"baseOnBalls":2,"strikeOuts":10},
 "Vanderbilt":{"atBats":35,"runs":8,"hits":12,"rbi":6,"baseOnBalls":5,"strikeOuts":8}
}
def main():
    games=json.loads((DATA/"games.json").read_text())
    players=json.loads((DATA/"player_stats.json").read_text())
    report=json.loads((DATA/"import_report.json").read_text())
    if len(games)!=444:raise ValueError("Incomplete attendance history")
    g=next(x for x in games if x["id"]==ID)
    existing=[r for r in players if r["game_id"]==ID]
    if existing:
        if (g["verification"]!="official_boxscore_verified" or len(existing)!=23
            or any(r["source_url"]!=PDF for r in existing)):
            raise ValueError("Existing prior Vanderbilt gamebook inconsistent")
        print("PASS source-verified Vanderbilt–Kentucky previously imported")
        return
    if (g["date"],g["away"],g["home"],g["verification"])!=(
         "2026-05-19","Kentucky","Vanderbilt","attendance_only"):
        raise ValueError("Original user-attended game identity mismatch")
    res=requests.get(PDF,timeout=35,headers={"User-Agent":"CourtsideArchive Official-PDF-Audit/1.0"})
    res.raise_for_status()
    if not res.content.startswith(b"%PDF-") or len(res.content)<20000:
        raise ValueError("Vanderbilt original PDF unavailable")
    pages=PdfReader(BytesIO(res.content)).pages
    if len(pages)!=2:raise ValueError("Expected original two-page Vanderbilt official PDF")
    source=re.sub(r"\s+"," ",pages[0].extract_text())
    for phrase in ("May 19, 2026","Kentucky 5","Vanderbilt 8","Win - Kranzler",
                   "Loss - J. Jelkin","Attendance: 6748"):
        if phrase not in source:raise ValueError("Official source not matched: "+phrase)
    for team,batters in B.items():
        for name,pos,ab,r,h,rbi,bb,k in batters:
            require_line(source,name,pos,[ab,r,h,rbi,bb,k])
    for team,pitchers in P.items():
        for name,outs,h,r,er,bb,k,np in pitchers:
            require_line(source,name,"",[f"{outs//3}.{outs%3}",h,r,er,bb,k],kind="pitching")
    for fragment in ("2B - T. Bell", "HR -","HBP - L. Lawrence","Rigdon 2."):
        if fragment not in source:raise ValueError("Extra-base source event missing "+fragment)
    new=[]
    for team in ("Kentucky","Vanderbilt"):
        batting=[]
        for i,(name,pos,ab,r,h,rbi,bb,k) in enumerate(B[team]):
            vals={"atBats":ab,"runs":r,"hits":h,"rbi":rbi,
               "baseOnBalls":bb,"strikeOuts":k,"doubles":0,"triples":0,"homeRuns":0,
               "stolenBases":0,"caughtStealing":0,"hitByPitch":0,"sacBunts":0,"sacFlies":0}
            vals.update(EXTRAS.get(name,{}))
            batting.append({"game_id":ID,"player_id":"cb-"+slug(team)+"-"+slug(name),
               "player":name,"team":team,"position":pos,"source_url":PDF,
               "source_type":"official_vanderbilt_gamebook_pdf",
               "verification":"official_boxscore_verified","batting":vals,
               "batting_slot":i+1,"batting_sub_index":0,"batting_appearance_index":i})
        for stat,n in TOTALS[team].items():
            if sum(r["batting"][stat] for r in batting)!=n:
                raise ValueError(f"{team} official total mismatch: {stat}")
        pitching=[]
        for i,(name,outs,h,r,er,bb,k,np) in enumerate(P[team]):
            v={"outs":outs,"hits":h,"runs":r,"earnedRuns":er,"baseOnBalls":bb,
              "strikeOuts":k,"numberOfPitches":np,
              "hitBatsmen":int(name in ("Jaxon Jelkin","Connor Fennell")),
              "wins":int(name=="Alex Kranzler"),"losses":int(name=="Jaxon Jelkin"),"saves":0}
            pitching.append({"game_id":ID,"player_id":"cb-"+slug(team)+"-"+slug(name),
                "player":name,"team":team,"position":None,"source_url":PDF,
                "source_type":"official_vanderbilt_gamebook_pdf",
                "verification":"official_boxscore_verified",
                "pitching":v,"pitching_appearance_index":i})
        opp="Kentucky" if team=="Vanderbilt" else "Vanderbilt"
        if (sum(r["pitching"]["outs"] for r in pitching) !=
            (24 if team=="Kentucky" else 27) or
            sum(r["pitching"]["hits"] for r in pitching)!=TOTALS[opp]["hits"] or
            sum(r["pitching"]["runs"] for r in pitching)!=TOTALS[opp]["runs"] or
            sum(r["pitching"]["strikeOuts"] for r in pitching)!=TOTALS[opp]["strikeOuts"]):
            raise ValueError("Official pitching vs opposing batting parity mismatch "+team)
        new.extend(batting+pitching)
    if len(new)!=23 or len({r["player_id"] for r in new})!=23:
        raise ValueError("Expected 23 source-distinct player entries")
    prev={(r["game_id"],r["player_id"]) for r in players}
    if prev & {(r["game_id"],r["player_id"]) for r in new}:
        raise ValueError("Conflicting historical athlete identity")
    g.update({"verification":"official_boxscore_verified","source_url":PDF,
      "official_boxscore_status":"verified","score_provenance":"official_boxscore",
      "away_score":5,"home_score":8,"away_hits":8,"home_hits":12,
      "away_errors":2,"home_errors":1,
      "innings":[{"inning":i+1,"away":a,"home":h} for i,(a,h) in enumerate(zip(
        [1,0,1,1,1,0,0,0,1],[0,0,1,0,0,4,0,3,None]))],
      "pitching_decisions":{"win":"Alex Kranzler","loss":"Jaxon Jelkin","save":None},
      "source_attendance":6748,"first_pitch_local":"14:00",
      "ballpark":"Hoover Met","city":"Hoover","state":"AL","neutral_site":True,
      "game_type":"conference_tournament","postseason_round":"SEC Tournament · First Round",
      "recap_source_url":"https://vucommodores.com/on-to-the-next-round-2/"})
    players.extend(new)
    players.sort(key=lambda r:(r["game_id"],r["team"],r.get("batting_slot",99),
      r.get("batting_sub_index",99),r.get("pitching_appearance_index",99),r["player_id"]))
    report.update({
      "official_player_boxscores_imported":sum(x["verification"]=="official_boxscore_verified" for x in games),
      "official_score_and_inning_lines_matched":sum(x["verification"]!="attendance_only" for x in games),
      "official_scoreboard_player_lines_pending":sum(x["verification"]=="official_scoreboard_verified" for x in games),
      "attendance_only_pending_official_verification":sum(x["verification"]=="attendance_only" for x in games),
      "player_stat_rows":len(players),"unique_player_ids":len({r["player_id"] for r in players}),
      "latest_verified_batch":"SEC Tournament May 19, 2026 · Kentucky/Vanderbilt official PDF"
    })
    report["remaining_official_boxscore_work"]=report["official_scoreboard_player_lines_pending"]
    report.setdefault("additional_official_gamebooks",[]).append({
       "game_id":ID,"source_url":PDF,"verification":"official_boxscore_verified"})
    audit={"status":"PASS","game_id":ID,"source_url":PDF,
      "official_pdf_pages":len(pages),"download_bytes":len(res.content),
      "athlete_game_records":len(new),"source_team_totals":TOTALS,
      "batting_slot_source_verified":True,"pitcher_outs_reconciled":True,
      "pitching_decisions_verified":True}
    for fname,v in (("games.json",games),("player_stats.json",players),
      ("import_report.json",report),("2026_sec_may19_kentucky_vanderbilt_pdf_audit.json",audit)):
        (DATA/fname).write_text(json.dumps(v,ensure_ascii=False,indent=2)+"\n")
    print("PASS May 19 Kentucky 5 Vanderbilt 8 official PDF,",
      len(new),"verified player records; total complete games",report["official_player_boxscores_imported"])
if __name__=="__main__":main()
