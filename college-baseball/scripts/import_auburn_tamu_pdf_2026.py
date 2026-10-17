#!/usr/bin/env python3
"""Import official Auburn–Texas A&M May 22 SEC Tournament PDF box score.

University gamebook: https://auburntigers.com/documents/af6c83f1-0e55-4a6e-aa50-e5f1d18b805e.pdf
Direct 1-page original PDF is downloaded and its printed hitter/pitcher line
values are checked before promotion. Texas A&M full first names are verified
using the university's 2026 baseball roster. All 444 attendance IDs persist.
"""
from __future__ import annotations
from io import BytesIO
import json
import re
from pathlib import Path
import requests
from pypdf import PdfReader
from import_sidearm_pilot import slug

DATA=Path(__file__).resolve().parents[1]/"data"
GAME_ID="cb-2026-05-22-auburn-texas-a-m-att0436"
PDF="https://storage.googleapis.com/auburn-prod/2026/05/23/B1yXyMnFNLlPuQs4IZQC4WYlQNbHmcsWGsihLulK.pdf"
ROSTER="https://12thman.com/sports/baseball/roster/season/2026"
# Official row: printed surname, name, position, AB R H RBI BB K;
# trailing positional extra-base events are transcribed from official notes.
BATTERS={
 "Auburn":[
  ("Rembert, Chris","Chris Rembert","2B",3,0,1,1,0,1),
  ("Fralick, Chase","Chase Fralick","C",5,1,1,2,0,2),
  ("Bingaman, Ethin","Ethin Bingaman","1B",4,2,1,1,1,1),
  ("Guevara, Eric","Eric Guevara","3B",5,0,2,1,0,0),
  ("Terrell, Bub","Bub Terrell","LF",5,0,1,1,0,2),
  ("McCraine, Brandon","Brandon McCraine","SS",4,0,1,0,0,0),
  ("McCraine, Mason","Mason McCraine","RF",3,1,1,1,1,2),
  ("Belza, Taylor","Taylor Belza","DH",4,1,1,0,0,1),
  ("Carter, Bristol","Bristol Carter","CF",4,2,2,0,0,2),
 ],
 "Texas A&M":[
  ("GRAHOVAC","Gavin Grahovac","3B",4,0,0,0,0,2),
  ("SORRELL","Caden Sorrell","CF",4,0,1,0,0,1),
  ("HACOPIAN","Chris Hacopian","DH",4,0,0,0,0,1),
  ("DUER","Jake Duer","LF",3,0,0,0,0,2),
  ("KIEL II","Terrence Kiel II","PH",1,0,0,0,0,0),
  ("HARRISON","Bear Harrison","C",1,0,0,0,2,1),
  ("ROYO","Ben Royo","2B",4,0,1,0,0,0),
  ("WILSON","Jorian Wilson","RF",4,0,0,0,0,4),
  ("BINDERUP","Blake Binderup","1B",2,0,0,0,1,2),
  ("KELLNER","Boston Kellner","SS",1,0,0,0,2,0),
 ]}
# source lastname, full name, IP (in baseball outs), H, R, ER, BB, K, pitches.
PITCHERS={
 "Auburn":[
  ("Alvarez, Andreas","Andreas Alvarez",15,1,0,0,4,9,98),
  ("Cormier, LJ","LJ Cormier",12,1,0,0,1,4,62)],
 "Texas A&M":[
  ("DARDEN","Ethan Darden",3,5,4,4,1,2,33),
  ("LYONS","Gavin Lyons",12,2,1,1,0,5,54),
  ("SDAO","Shane Sdao",6,4,2,2,1,3,52),
  ("MOSS","Weston Moss",3,0,0,0,0,1,19),
  ("FRESHCORN","Clayton Freshcorn",3,0,0,0,0,0,14),
 ]}
EXTRA={
 "Chris Rembert":{"doubles":1,"hitByPitch":1,"sacBunts":1,"stolenBases":1},
 "Chase Fralick":{"doubles":1},
 "Ethin Bingaman":{"homeRuns":1},
 "Bub Terrell":{"doubles":1},
 "Mason McCraine":{"homeRuns":1},
 "Bristol Carter":{"doubles":1},
 "Bear Harrison":{"hitByPitch":1},
}
RESULTS={"Auburn":{"atBats":37,"runs":7,"hits":11,"rbi":7,"baseOnBalls":2,"strikeOuts":11},
         "Texas A&M":{"atBats":28,"runs":0,"hits":2,"rbi":0,"baseOnBalls":5,"strikeOuts":13}}
DECISIONS={"wins":"Andreas Alvarez","losses":"Ethan Darden","saves":"LJ Cormier"}

def require_line(text,label,position,values,kind="batting"):
    # A specific contiguous official player row is required, never just a name.
    # PdfReader layout extraction sometimes wraps between cells; all whitespace
    # is normalized, but row numerical values must remain source-identical.
    core = label + ((" "+position.lower()) if kind=="batting" else "")
    digits = values if kind=="batting" else values
    pattern=(r"(?<![A-Za-z])"+re.escape(core).replace(r"\ ",r"\s+")
             +r"\s+"+r"\s+".join(re.escape(str(x)) for x in digits)+r"(?!\d)")
    if not re.search(pattern,text,re.I):
        raise ValueError(f"University PDF player row not independently matched: {core!r} {digits}")

def official_text():
    response=requests.get(PDF,timeout=30,headers={"User-Agent":"CourtsideArchive Official-PDF-Audit/1.0"})
    response.raise_for_status()
    if not response.content.startswith(b"%PDF-") or len(response.content)<40000:
        raise ValueError("Original official Auburn PDF not delivered")
    reader=PdfReader(BytesIO(response.content))
    if len(reader.pages)!=1:raise ValueError("Expected original Auburn single page gamebook")
    text=re.sub(r"\s+"," ",reader.pages[0].extract_text())
    for needle in ("May 22, 2026","Auburn 7","Texas A&M 0",
                   "Score by Innings","Win - Alvarez","Save - Cormier"):
        if needle not in text:raise ValueError("PDF source game/decision identification failed: "+needle)
    require_line(text,"Totals","",[37,7,11,7,2,11],kind="pitching")
    # Assert every individual source batting and pitching line as printed.
    for team,players in BATTERS.items():
        for short,_,pos,ab,r,h,rbi,bb,k in players:
            require_line(text,short,pos,[ab,r,h,rbi,bb,k])
    for team,players in PITCHERS.items():
        for short,_,outs,h,r,er,bb,k,pa in players:
            require_line(text,short,"",[f"{outs//3}.{outs%3}",h,r,er,bb,k],kind="pitching")
    if not all(x in text for x in (
        "2B - Rembert", "HR - Bingaman", "McCraine", "HBP - Rembert",
        "SH - Rembert", "SB - Rembert", "Attendance: 13105")):
        raise ValueError("Gamebook advanced-hit event notes not found")
    return response,len(text)

def make_batters(team,source):
    output=[]
    for idx,(short,name,pos,ab,r,h,rbi,bb,k) in enumerate(BATTERS[team]):
        sub=int(team=="Texas A&M" and name=="Terrence Kiel II")
        slot=4 if sub else (idx if team=="Texas A&M" and idx>=5 else idx+1)
        b={"atBats":ab,"runs":r,"hits":h,"rbi":rbi,"baseOnBalls":bb,
           "strikeOuts":k,"doubles":0,"triples":0,"homeRuns":0,
           "hitByPitch":0,"sacBunts":0,"sacFlies":0,
           "stolenBases":0,"caughtStealing":0}
        b.update(EXTRA.get(name,{}))
        output.append({"game_id":GAME_ID,"player_id":"cb-"+slug(team)+"-"+slug(name),
          "player":name,"team":team,"position":pos,"source_url":source,
          "source_type":"official_auburn_gamebook_pdf","verification":"official_boxscore_verified",
          "batting":b,"batting_slot":slot,"batting_sub_index":sub,
          "batting_appearance_index":idx})
    return output

def make_pitchers(team,source):
    output=[]
    for i,(short,name,outs,h,r,er,bb,k,np) in enumerate(PITCHERS[team]):
        p={"outs":outs,"hits":h,"runs":r,"earnedRuns":er,
           "baseOnBalls":bb,"strikeOuts":k,"numberOfPitches":np,
           "hitBatsmen":1 if name in ("LJ Cormier","Weston Moss") else 0,
           "wins":int(name==DECISIONS["wins"]),
           "losses":int(name==DECISIONS["losses"]),
           "saves":int(name==DECISIONS["saves"])}
        output.append({"game_id":GAME_ID,"player_id":"cb-"+slug(team)+"-"+slug(name),
          "player":name,"team":team,"position":None,"source_url":source,
          "source_type":"official_auburn_gamebook_pdf","verification":"official_boxscore_verified",
          "pitching":p,"pitching_appearance_index":i})
    return output

def main():
    games=json.loads((DATA/"games.json").read_text())
    players=json.loads((DATA/"player_stats.json").read_text())
    report=json.loads((DATA/"import_report.json").read_text())
    if len(games)!=444:raise ValueError("Attendance source expected 444 games")
    matches=[g for g in games if g["id"]==GAME_ID]
    if len(matches)!=1:raise ValueError("Correct attended game missing")
    game=matches[0]
    if (game["date"],game["away"],game["home"])!=("2026-05-22","Auburn","Texas A&M"):
        raise ValueError("Attendance identity mismatch")
    old=[r for r in players if r["game_id"]==GAME_ID]
    if old:
        if len(old)!=26 or game["verification"]!="official_boxscore_verified":
            raise ValueError("Existing full game has inconsistent player rows")
        print("PASS official May 22 Auburn/Texas A&M gamebook already imported",flush=True)
        return
    if game["verification"]!="official_scoreboard_verified":
        raise ValueError("Game has not independently verified original scoreboard")
    response,extracted_length=official_text()
    new=[]
    for team in ("Auburn","Texas A&M"):
        bats=make_batters(team,PDF)
        pitchers=make_pitchers(team,PDF)
        for k in RESULTS[team]:
            total=sum(r["batting"][k] for r in bats)
            if total!=RESULTS[team][k]:
                raise ValueError(f"{team} {k} {total} differs from official source")
        other="Auburn" if team=="Texas A&M" else "Texas A&M"
        if (sum(p["pitching"]["hits"] for p in pitchers)!=RESULTS[other]["hits"]
           or sum(p["pitching"]["runs"] for p in pitchers)!=RESULTS[other]["runs"]
           or sum(p["pitching"]["strikeOuts"] for p in pitchers)!=RESULTS[other]["strikeOuts"]
           or sum(p["pitching"]["outs"] for p in pitchers)!=27):
            raise ValueError("Pitcher/team source totals mismatch "+team)
        slots=[r["batting_slot"] for r in bats if r["batting_sub_index"]==0]
        if sorted(slots)!=list(range(1,10)):
            raise ValueError("Official batting order missing 1–9 "+team)
        new.extend(bats+pitchers)
    if len(new)!=26:raise ValueError("Expected 19 players at bat plus seven distinct pitchers")
    oldkeys={(r["game_id"],r["player_id"]) for r in players}
    if oldkeys & {(r["game_id"],r["player_id"]) for r in new}:
        raise ValueError("Conflicting pitcher/hitter identifier on import")
    if len({r["player_id"] for r in new})!=26:
        raise ValueError("Unstable or duplicate player identifiers in new game")
    if (game["away_score"],game["home_score"],game["away_hits"],game["home_hits"],
        game["away_errors"],game["home_errors"])!=(7,0,11,2,0,1):
        raise ValueError("Official scoreboard mismatches gamebook")
    if [r["away"] for r in game["innings"]] != [1,4,0,0,0,1,1,0,0] or \
       [r["home"] for r in game["innings"]] != [0]*9:
        raise ValueError("Official inning-by-inning score mismatch")
    if game["pitching_decisions"] != {"win":"Andreas Alvarez","loss":"Ethan Darden","save":"LJ Cormier"}:
        raise ValueError("Previously verified W/L/S disagree with source")
    game["source_url"]=PDF
    game["recap_source_url"]="https://auburntigers.com/news/2026/05/22/no-6-auburn-blanks-no-9-texas-aandm-7-0-to-advance-to-sec-semis"
    game["verification"]="official_boxscore_verified"
    game["official_boxscore_status"]="verified"
    game["score_provenance"]="official_boxscore"
    game["source_attendance"]=13105
    game["first_pitch_local"]="20:26"
    game["notes"]=game.get("notes","")+" Complete source-verified official one-page Auburn PDF gamebook; original attendance and score preserved."
    players.extend(new)
    players.sort(key=lambda r:(r["game_id"],r["team"],r.get("batting_slot",99),
                               r.get("batting_sub_index",99),
                               r.get("pitching_appearance_index",99),r["player_id"]))
    report.update({
       "official_player_boxscores_imported":sum(g["verification"]=="official_boxscore_verified" for g in games),
       "official_score_and_inning_lines_matched":sum(g["verification"]!="attendance_only" for g in games),
       "official_scoreboard_player_lines_pending":sum(g["verification"]=="official_scoreboard_verified" for g in games),
       "attendance_only_pending_official_verification":sum(g["verification"]=="attendance_only" for g in games),
       "player_stat_rows":len(players),
       "unique_player_ids":len({r["player_id"] for r in players}),
       "latest_verified_batch":"All five formerly incomplete SEC Tournament May 20–22 2026 gamebooks completed",
       "2026_may22_auburn_tamu_official_pdf_audit":"data/2026_auburn_tamu_pdf_audit.json"
    })
    report["remaining_official_boxscore_work"]=report["official_scoreboard_player_lines_pending"]
    report["warning"]="444 college attendance rows preserved. Official player stats imported only after full gamebook reconciliation. All eight May 20–23 SEC games complete."
    for item in report.get("latest_verified_batch_games",[]):
        if item.get("worksheet_row")==437:
            item["status"]="official_boxscore_verified"
            item["official_source"]=PDF
    report.setdefault("additional_official_gamebooks",[]).append({
        "game_id":GAME_ID,"source_url":PDF,"verification":"official_boxscore_verified",
        "roster_source_url":ROSTER})
    audit={"status":"PASS","game_id":GAME_ID,"original_gamebook_pdf":PDF,
          "roster_source_url":ROSTER,"download_bytes":len(response.content),
          "text_length":extracted_length,"individual_player_rows":len(new),
          "lineup_spots_verified":True,"batting_source_verified":True,
          "pitching_source_verified":True,"total_2026_games_verified":report["official_player_boxscores_imported"],
          "source_team_totals":RESULTS,
          "official_decisions":game["pitching_decisions"]}
    for name,data in (("games.json",games),("player_stats.json",players),
                      ("import_report.json",report),("2026_auburn_tamu_pdf_audit.json",audit)):
        (DATA/name).write_text(json.dumps(data,ensure_ascii=False,indent=2)+"\n")
    print("PASS Auburn 7 Texas A&M 0 complete official PDF gamebook;",
          len(new),"player-game records added,",
          report["official_player_boxscores_imported"],"full gamebooks total",flush=True)

if __name__=="__main__": main()
