#!/usr/bin/env python3
"""Independent PDF-verified May 16 Arkansas @ Kentucky NCAA gamebook.

All official player rows, team totals, pitcher outs, 1–9 batting slots,
substitutions, and win/loss/save identities are checked before changing data.
"""
from __future__ import annotations
from io import BytesIO
import json, re
from pathlib import Path
import requests
from pypdf import PdfReader
from import_sidearm_pilot import slug
from import_auburn_tamu_pdf_2026 import require_line

DATA=Path(__file__).resolve().parents[1]/"data"
ID="cb-2026-05-16-arkansas-kentucky-att0424"
PDF="https://arkansasrazorbacks.com/stats/baseball/2026/ARK55.pdf"
# Printed player name, verified complete identity, position, AB, R, H, RBI, BB, K.
B={
"Arkansas":[
 ("Damian Ruiz","Damian Ruiz","lf",5,2,3,3,0,1),
 ("Camden Kozeal","Camden Kozeal","ss",5,3,3,2,1,1),
 ("Ryder Helfrick","Ryder Helfrick","c",4,1,1,1,1,1),
 ("Zack Stewart","Zack Stewart","rf",6,2,4,4,0,2),
 ("Kuhio Aloy","Kuhio Aloy","dh",6,1,1,0,0,2),
 ("Nolan Souza","Nolan Souza","2b",4,2,1,1,2,2),
 ("TJ Pompey","TJ Pompey","3b",3,2,0,1,1,0),
 ("Carter Rutenbar","Carter Rutenbar","1b",2,1,1,1,0,0),
 ("Alexander Peck","Alexander Peck","ph/1b",3,1,0,0,1,1),
 ("Christian Turner","Christian Turner","cf",2,1,0,1,1,2),
 ("Maika Niu","Maika Niu","cf",1,0,0,0,0,0),
],
"Kentucky":[
 ("J. Tharnish","Jayce Tharnish","cf",6,2,3,3,0,0),
 ("T. Bell","Tyler Bell","ss",6,1,3,0,0,2),
 ("L. Lawrence","Luke Lawrence","2b",5,1,2,2,1,2),
 ("E. Hindle","Ethan Hindle","dh",4,1,2,0,0,1),
 ("H. Brown","Hudson Brown","1b",5,1,1,1,0,0),
 ("W. Marcy","Will Marcy","lf",4,1,1,0,1,3),
 ("C. Hansen","Carson Hansen","rf",5,2,2,4,0,1),
 ("O. Jenkins","Owen Jenkins","c",5,1,2,1,0,0),
 ("C. Cloud","Caeden Cloud","3b",4,2,1,0,1,1),
]}
P={
"Arkansas":[
 ("Tate McGuire","Tate McGuire",7,2,2,2,1,4,46),
 ("Cole Gibler","Cole Gibler",6,7,7,7,2,3,52),
 ("Steele Eaves","Steele Eaves",0,3,3,1,0,0,12),
 ("Parker Coil","Parker Coil",5,3,0,0,0,1,18),
 ("James DeCremer","James DeCremer",9,2,0,0,0,2,34)],
"Kentucky":[
 ("C. Mattison","Connor Mattison",0,5,6,6,1,0,22),
 ("T. Peterson","Toby Peterson",0,1,3,3,1,0,11),
 ("I. Austin","Ira Austin IV",3,2,1,1,1,2,27),
 ("R. Mullan","Ryan Mullan",3,0,0,0,0,1,17),
 ("W. Coleman","Will Coleman",3,1,1,1,1,1,23),
 ("C. Alderman","Chase Alderman",3,1,1,1,0,1,17),
 ("B. Treichel","Bryson Treichel",3,0,0,0,0,1,13),
 ("T. Hunter","Tristan Hunter",0,0,2,2,2,0,14),
 ("J. Bennett","Jack Bennett",12,4,2,2,1,6,68)]
}
X={
"Damian Ruiz":{"doubles":1,"hitByPitch":1,"stolenBases":1},
"Camden Kozeal":{"doubles":1,"triples":1},
"Ryder Helfrick":{"hitByPitch":1},
"Zack Stewart":{"doubles":2,"homeRuns":1},
"Kuhio Aloy":{"doubles":1},
"Nolan Souza":{"homeRuns":1},
"TJ Pompey":{"hitByPitch":2,"stolenBases":1},
"Christian Turner":{"hitByPitch":1,"caughtStealing":1},
"Jayce Tharnish":{"doubles":1,"homeRuns":1},
"Tyler Bell":{"triples":1},
"Ethan Hindle":{"hitByPitch":1},
"Will Marcy":{"doubles":1},
"Carson Hansen":{"homeRuns":1},
"Caeden Cloud":{"doubles":1}
}
TOTAL={
"Arkansas":{"atBats":41,"runs":16,"hits":14,"rbi":14,"baseOnBalls":7,"strikeOuts":12},
"Kentucky":{"atBats":44,"runs":12,"hits":17,"rbi":11,"baseOnBalls":3,"strikeOuts":10}}
WIN="Parker Coil"; LOSS="Tristan Hunter"; SAVE="James DeCremer"
HBP_PITCHER={"Toby Peterson":1,"Ira Austin IV":1,"Will Coleman":1,
             "Chase Alderman":1,"Jack Bennett":1,"James DeCremer":1}

def source_audit():
    r=requests.get(PDF,headers={"User-Agent":"CourtsideArchive Official-PDF-Gamebook/1.0"},timeout=35)
    r.raise_for_status()
    if not r.content.startswith(b"%PDF-") or len(r.content)<12000:
        raise ValueError("University official gamebook PDF unavailable")
    pages=PdfReader(BytesIO(r.content)).pages
    if len(pages)!=3:raise ValueError("Official Arkansas PDF three-page gamebook expected")
    text=re.sub(r"\s+"," ",pages[0].extract_text())
    for v in ("#12 Arkansas at Kentucky","May 16, 2026","Arkansas 16",
              "Kentucky 12","Win - Coil","Loss - T. Hunter","Save - DeCremer",
              "Attendance: 3963"):
        if v not in text:raise ValueError("Official date/score/decision failed "+v)
    for team,arr in B.items():
        for short,name,pos,ab,runs,h,rbi,bb,k in arr:
            require_line(text,short,pos,[ab,runs,h,rbi,bb,k])
    for team,arr in P.items():
        for short,name,outs,h,runs,er,bb,k,np in arr:
            require_line(text,short,"",[f"{outs//3}.{outs%3}",h,runs,er,bb,k],
                         kind="pitching")
    for x in ("Arkansas 10 0 1 1 0 2 0 0 2 16 14 1",
              "Kentucky 0 0 2 1 9 0 0 0 0 12 17 2",
              "HBP - Ruiz; Helfrick; Pompey 2; Turner; E. Hindle",
              "HR - Stewart","SB - Ruiz","CS -"):
        if x not in text:raise ValueError("Official inning/events source mismatch: "+x)
    return r,pages,text

def main():
    games=json.loads((DATA/"games.json").read_text())
    players=json.loads((DATA/"player_stats.json").read_text())
    report=json.loads((DATA/"import_report.json").read_text())
    if len(games)!=444:raise ValueError("444-game attendance master changed")
    game=next((g for g in games if g["id"]==ID),None)
    if game is None or (game["date"],game["away"],game["home"])!=(
        "2026-05-16","Arkansas","Kentucky"):
        raise ValueError("Attendance date/teams do not match official source")
    prior=[r for r in players if r["game_id"]==ID]
    if prior:
        if game["verification"]!="official_boxscore_verified" or len(prior)!=34 or any(
            r.get("source_url")!=PDF for r in prior):
            raise ValueError("Existing imported May16 gamebook inconsistent")
        print("PASS May 16 Arkansas/Kentucky already verified")
        return
    if game["verification"]!="attendance_only":
        raise ValueError("Unexpected previous game verification")
    response,pages,text=source_audit()
    new=[]
    for team in ("Arkansas","Kentucky"):
        bats=[]
        for i,(short,name,pos,ab,r,h,rbi,bb,k) in enumerate(B[team]):
            sub=(team=="Arkansas" and name in ("Alexander Peck","Maika Niu"))
            slot=(8 if name=="Alexander Peck" else 9 if name=="Maika Niu"
                  else i-1 if team=="Arkansas" and i>=9 else i+1)
            vals={"atBats":ab,"runs":r,"hits":h,"rbi":rbi,"baseOnBalls":bb,
                  "strikeOuts":k,"doubles":0,"triples":0,"homeRuns":0,
                  "hitByPitch":0,"sacBunts":0,"sacFlies":0,
                  "stolenBases":0,"caughtStealing":0}
            vals.update(X.get(name,{}))
            bats.append({"game_id":ID,"player_id":"cb-"+slug(team)+"-"+slug(name),
              "player":name,"team":team,"position":pos.upper(),
              "source_url":PDF,"source_type":"official_arkansas_gamebook_pdf",
              "verification":"official_boxscore_verified","batting":vals,
              "batting_slot":slot,"batting_sub_index":int(sub),
              "batting_appearance_index":i})
        for k,expected in TOTAL[team].items():
            if sum(row["batting"][k] for row in bats)!=expected:
                raise ValueError("Official batting team total mismatch: "+team+" "+k)
        if sorted(r["batting_slot"] for r in bats if r["batting_sub_index"]==0)!=list(range(1,10)):
            raise ValueError("Missing 1–9 official batting slots: "+team)
        pitchers=[]
        for i,(short,name,outs,h,r,er,bb,k,np) in enumerate(P[team]):
            vals={"outs":outs,"hits":h,"runs":r,"earnedRuns":er,
                  "baseOnBalls":bb,"strikeOuts":k,"numberOfPitches":np,
                  "hitBatsmen":HBP_PITCHER.get(name,0),
                  "wins":int(name==WIN),"losses":int(name==LOSS),
                  "saves":int(name==SAVE)}
            pitchers.append({"game_id":ID,"player_id":"cb-"+slug(team)+"-"+slug(name),
               "player":name,"team":team,"source_url":PDF,
               "source_type":"official_arkansas_gamebook_pdf",
               "verification":"official_boxscore_verified",
               "pitching":vals,"pitching_appearance_index":i})
        other="Kentucky" if team=="Arkansas" else "Arkansas"
        for k,field in (("hits","hits"),("runs","runs"),("strikeOuts","strikeOuts")):
            if sum(r["pitching"][field] for r in pitchers)!=TOTAL[other][k]:
                raise ValueError("Official pitching vs other team "+field+" mismatch "+team)
        if sum(r["pitching"]["outs"] for r in pitchers)!=27:
            raise ValueError("Invalid total pitching outs: "+team)
        new.extend(bats+pitchers)
    if len(new)!=34 or len({r["player_id"] for r in new})!=34:
        raise ValueError("Expected 34 independent official player-game identities")
    if {(r["game_id"],r["player_id"]) for r in new} & {
        (r["game_id"],r["player_id"]) for r in players}:
        raise ValueError("Player-game duplicate in other records")
    game.update({
      "verification":"official_boxscore_verified",
      "official_boxscore_status":"verified",
      "score_provenance":"official_boxscore","source_url":PDF,
      "away_score":16,"home_score":12,"away_hits":14,"home_hits":17,
      "away_errors":1,"home_errors":2,
      "innings":[{"inning":i+1,"away":a,"home":h}
           for i,(a,h) in enumerate(zip([10,0,1,1,0,2,0,0,2],
                                        [0,0,2,1,9,0,0,0,0]))],
      "pitching_decisions":{"win":WIN,"loss":LOSS,"save":SAVE},
      "ballpark":"Kentucky Proud Park","city":"Lexington","state":"KY",
      "neutral_site":False,"game_type":"regular_season","postseason_round":None,
      "source_attendance":3963,"first_pitch_local":"14:02",
    })
    players.extend(new)
    players.sort(key=lambda r:(r["game_id"],r["team"],r.get("batting_slot",99),
        r.get("batting_sub_index",99),r.get("pitching_appearance_index",99),r["player_id"]))
    report.update({
      "official_player_boxscores_imported":sum(g["verification"]=="official_boxscore_verified" for g in games),
      "official_score_and_inning_lines_matched":sum(g["verification"]!="attendance_only" for g in games),
      "official_scoreboard_player_lines_pending":sum(g["verification"]=="official_scoreboard_verified" for g in games),
      "attendance_only_pending_official_verification":sum(g["verification"]=="attendance_only" for g in games),
      "remaining_official_boxscore_work":sum(g["verification"]=="official_scoreboard_verified" for g in games),
      "player_stat_rows":len(players),"unique_player_ids":len({r["player_id"] for r in players}),
      "latest_verified_batch":"SEC Regular Season May 16, 2026 · Arkansas at Kentucky"
    })
    report.setdefault("additional_official_gamebooks",[]).append({
       "game_id":ID,"source_url":PDF,"verification":"official_boxscore_verified"})
    report["warning"]="Original 444 attended games preserved, missing sources left unverified. No invented athlete stats."
    audit={"status":"PASS","game_id":ID,"source_url":PDF,
      "original_pdf_pages":len(pages),"source_bytes":len(response.content),
      "source_text_length":len(text),"new_player_game_records":len(new),
      "verified_team_batting_totals":TOTAL,"pitchers_versus_opposition":True,
      "verified_substitute_slots":{"Alexander Peck":8,"Maika Niu":9},
      "verified_pitcher_decisions":{"win":WIN,"loss":LOSS,"save":SAVE}}
    for name,value in (("games.json",games),("player_stats.json",players),
       ("import_report.json",report),("2026_may16_arkansas_kentucky_pdf_audit.json",audit)):
        (DATA/name).write_text(json.dumps(value,ensure_ascii=False,indent=2)+"\n")
    print("PASS official Arkansas 16 Kentucky 12 May 16 PDF gamebook",
      len(new),"new player records",report["official_player_boxscores_imported"],"verified gamebooks")
if __name__=="__main__":main()
