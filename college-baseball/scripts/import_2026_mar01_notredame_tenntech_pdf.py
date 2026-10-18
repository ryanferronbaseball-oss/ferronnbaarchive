#!/usr/bin/env python3
"""Official 2026-03-01 Notre Dame–Tennessee Tech PDF scorebook transcription.

Batter rows, 1–9 order, pinch substitutions, innings, pitchers and decisions
are transcribed from the single-page Notre Dame athletics official gamebook.
Re-read official source PDF and verify school/game/date, identities, table totals,
pitching reconciliation and full row counts before setting verified status.
No inferred professional statistics or JUCO imports.
"""
from pathlib import Path
import hashlib
import json
import re

import fitz
import requests
from import_sidearm_pilot import slug

DATA = Path(__file__).resolve().parents[1] / "data"
GAME_ID = "cb-2026-03-01-notre-dame-tennessee-tech-att0383"
URL = "https://storage.googleapis.com/fightingirish-com/2026/03/3126_ND.pdf"
AWAY = "Notre Dame"
HOME = "Tennessee Tech"

# Team order: original batting slots 1–9; nested entries are source substitutions.
# Fields: display name, field position, AB, R, H, RBI, BB, K
BATS = {
    AWAY: [
        [("Drew Berkland","LF",4,2,1,0,1,1)],
        [("Noah Coy","SS",3,2,2,1,2,0)],
        [("Mark Quatrani","C",4,1,3,5,0,0)],
        [("Bino Watters","DH",5,2,2,4,0,0)],
        [("Jayce Lee","RF",5,1,4,0,0,1)],
        [("Parker Brzustewicz","1B",5,0,1,0,0,1)],
        [("Mason Barth","2B",4,1,1,0,0,1)],
        [("Jamie Zee","3B",3,1,2,1,0,1)],
        [("Brandon Logan","CF",2,0,0,0,0,1),
         ("Dylan Passo","PH",0,0,0,0,0,0),
         ("Andrew Graham","PH",0,0,0,0,1,0),
         ("Caleb Ricks","PR/LF",1,1,0,0,0,0)]
    ],
    HOME: [
        [("Landon Smelser","CF",3,0,1,0,0,1),
         ("Ty Denton","PH",1,0,0,0,0,0)],
        [("Eddie Garza","2B",2,0,0,0,1,0)],
        [("Jorsixt Jimenez","DH",2,0,1,0,1,0)],
        [("Connor Crowson","3B",3,0,0,0,0,1)],
        [("Owen Lee","SS",2,0,0,0,1,0)],
        [("Manny Garza","C",3,0,0,0,0,0)],
        [("Nash Crowell","1B",3,0,0,0,0,1)],
        [("Jackson Rooker","LF",2,0,0,0,0,0),
         ("Cade Fuller","PH",1,0,0,0,0,0)],
        [("Luke Bragga","RF",2,0,0,0,0,0),
         ("Aaron Moffitt","PH",1,0,0,0,0,1)]
    ]
}
# Name, outs, hits, runs, earned runs, walks, strikeouts, pitches.
PITCHERS = {
    AWAY:[
        ("Ty Uber",15,2,0,0,2,2,74),
        ("Kellan Klosterman",2,0,0,0,1,1,19),
        ("Eli Thurmond",4,0,0,0,0,0,11),
        ("Dylan Singleton",3,0,0,0,0,1,11),
    ],
    HOME:[
        ("Logan Moller",12,1,0,0,1,5,50),
        ("Carter Casabella",7,7,2,2,0,1,45),
        ("Eli Huddleston",0,0,1,1,1,0,9),
        ("Reece McDuffie",4,5,5,5,1,0,32),
        ("Micah Summar",0,3,3,3,1,0,16),
        ("Carson Davis",1,0,0,0,0,0,7),
    ]
}
INNINGS = [(0,0),(0,0),(0,0),(0,0),(1,0),(0,0),(5,0),(5,0)]
TOTALS = {AWAY:(36,11,16,11,4,6),HOME:(25,0,2,0,3,4)}
EXPECTED_SCORE = (11,0)
EXPECTED_HITS = (16,2)
SOURCE_PRINTED_TYPO = {"Brzustewciz,Parker":"Parker Brzustewicz"}


def read_pdf():
    response=requests.get(URL,headers={"User-Agent":"Mozilla/5.0"},timeout=45)
    response.raise_for_status()
    raw=response.content
    if not raw.startswith(b"%PDF"):
        raise ValueError("Official source link did not return raw gamebook PDF")
    pdf=fitz.open(stream=raw,filetype="pdf")
    if pdf.page_count != 1:
        raise ValueError("Unexpected gamebook PDF page count")
    content=pdf[0].get_text("text")
    normalized=" ".join(content.split())
    # Embedded PDF font kerning sometimes splits names (e.g. "Ber kland").
    # Match identities after removing only whitespace/punctuation, never digits.
    condensed=re.sub(r"[^a-z0-9]+","",normalized.lower())
    # The official scorebook's PDF extractor may insert spaces between
    # comma-separated first/last names. Verify identities as individual
    # source tokens and reconcile all numeric player totals below.
    for token in ("Official Box Score", "Notre Dame", "Tennessee Tech",
                  "03/01/2026", "Uber", "Casabella", "Berkland",
                  "Brzustewciz", "Smelser", "Moffitt"):
        if re.sub(r"[^a-z0-9]+","",token.lower()) not in condensed:
            raise ValueError("Official PDF identity token missing: "+token)
    # Full player-name membership is a second independent PDF safeguard.
    for team, slots in BATS.items():
        for spot in slots:
            for name,*_ in spot:
                surname=name.rsplit(" ",1)[-1]
                if name=="Parker Brzustewicz":
                    surname="Brzustewciz"  # University PDF misprint; roster correct.
                if surname.lower() not in condensed:
                    raise ValueError("Source-PDF player identity not found: "+name)
    for team, pitchers in PITCHERS.items():
        for name,*_ in pitchers:
            if name.rsplit(" ",1)[-1].lower() not in condensed:
                raise ValueError("Official PDF pitcher missing: "+name)
    return hashlib.sha256(raw).hexdigest(),len(raw)


def main():
    games=json.loads((DATA/"games.json").read_text(encoding="utf-8"))
    players=json.loads((DATA/"player_stats.json").read_text(encoding="utf-8"))
    report=json.loads((DATA/"import_report.json").read_text(encoding="utf-8"))
    if len(games)!=444:
        raise ValueError("Original attendance master changed")
    game=next((g for g in games if g["id"]==GAME_ID),None)
    if game is None or (game["date"],game["away"],game["home"])!=("2026-03-01",AWAY,HOME):
        raise ValueError("Official PDF identity does not match attendance")
    if game.get("boxscore_backfill_excluded"):
        raise ValueError("JUCO exclusions cannot be imported")
    if game["verification"]=="official_boxscore_verified":
        if not any(r["game_id"]==GAME_ID for r in players):
            raise ValueError("Game claims verified but rows missing")
        print("PASS prior official 03/01 PDF gamebook unchanged")
        return
    if game["verification"]!="attendance_only" or any(r["game_id"]==GAME_ID for r in players):
        raise ValueError("Unexpected existing game data; refusing overwrite")
    source_sha,bytes_count=read_pdf()
    if tuple(map(sum,zip(*INNINGS)))!=EXPECTED_SCORE or len(INNINGS)!=8:
        raise ValueError("Official eight-inning line-score mismatch")
    records=[]
    keys={(r["game_id"],r["player_id"]) for r in players}
    audits=[]
    for team in (AWAY,HOME):
        batter_rows=[]
        for slot,entries in enumerate(BATS[team],1):
            for index,(name,pos,ab,r,h,rbi,bb,k) in enumerate(entries):
                if min(ab,r,h,rbi,bb,k)<0 or h>ab:
                    raise ValueError("Impossible hitter row: "+name)
                pid="cb-"+slug(team)+"-"+slug(name)
                rec={
                    "game_id":GAME_ID,"player_id":pid,"player":name,"team":team,
                    "position":pos,"source_url":URL,"source_type":"official_university_pdf",
                    "verification":"official_boxscore_verified",
                    "batting_slot":slot,"batting_sub_index":index,
                    "batting_appearance_index":len(batter_rows),
                    "batting":{"atBats":ab,"runs":r,"hits":h,"rbi":rbi,
                               "baseOnBalls":bb,"strikeOuts":k,
                               "doubles":0,"triples":0,"homeRuns":
                                 (2 if name=="Bino Watters" else 1 if name=="Mark Quatrani" else 0),
                               "stolenBases":0,"caughtStealing":int(name=="Noah Coy"),
                               "hitByPitch":0,"sacBunts":int(name=="Jamie Zee"),
                               "sacFlies":int(name=="Mark Quatrani")}
                }
                records.append(rec);batter_rows.append(rec)
        summary=tuple(sum(r["batting"][fld] for r in batter_rows)
                      for fld in ("atBats","runs","hits","rbi","baseOnBalls","strikeOuts"))
        if summary!=TOTALS[team]:
            raise ValueError(f"PDF batting totals {team} mismatch {summary} != {TOTALS[team]}")
        pitcher_rows=[]
        for index,(name,outs,h,r,er,bb,k,np) in enumerate(PITCHERS[team]):
            pid="cb-"+slug(team)+"-"+slug(name)
            candidates=[rec for rec in records if rec["player_id"]==pid and rec["team"]==team]
            if len(candidates)>1:raise ValueError("Duplicate two-way athlete name")
            if candidates:rec=candidates[0]
            else:
                rec={"game_id":GAME_ID,"player_id":pid,"player":name,"team":team,
                     "position":"P","source_url":URL,"source_type":"official_university_pdf",
                     "verification":"official_boxscore_verified"}
                records.append(rec)
            rec["pitching_appearance_index"]=index
            rec["pitching"]={"outs":outs,"hits":h,"runs":r,"earnedRuns":er,
                            "baseOnBalls":bb,"strikeOuts":k,"numberOfPitches":np,
                            "wins":int(name=="Ty Uber"),"losses":int(name=="Carter Casabella"),
                            "saves":0}
            pitcher_rows.append(rec)
        psummary=tuple(sum(r["pitching"][fld] for r in pitcher_rows)
                       for fld in ("outs","hits","runs","baseOnBalls","strikeOuts"))
        other=HOME if team==AWAY else AWAY
        if psummary[:3]!=(24,TOTALS[other][2],TOTALS[other][1]):
            raise ValueError(f"PDF opposing pitching reconciliation failed {team}: {psummary}")
        if psummary[3:]!=(TOTALS[other][4],TOTALS[other][5]):
            raise ValueError("PDF pitcher walks and strikeouts do not reconcile opponent")
        audits.append({"team":team,"original_lineup_slots":9,"batters":len(batter_rows),
                       "pitchers":len(pitcher_rows),"total_ab_runs_hits_rbi_bb_so":summary,
                       "pitcher_outs_hits_runs_bb_so":psummary})
    new_keys={(r["game_id"],r["player_id"]) for r in records}
    if len(new_keys)!=len(records) or (new_keys & keys):
        raise ValueError("Duplicate PDF player stat identity")
    game.update({
        "verification":"official_boxscore_verified","official_boxscore_status":"verified",
        "source_url":URL,"score_provenance":"official_boxscore",
        "away_score":11,"home_score":0,"away_hits":16,"home_hits":2,
        "away_errors":0,"home_errors":0,
        "innings":[{"inning":i+1,"away":a,"home":h} for i,(a,h) in enumerate(INNINGS)],
        "pitching_decisions":{"win":"Ty Uber","loss":"Carter Casabella","save":None},
        "ballpark":"Bush Stadium at Averitt Baseball Complex","city":"Cookeville","state":"TN",
        "neutral_site":False,"game_type":"regular_season","postseason_round":None,
        "first_pitch_local":"14:05","source_attendance":1001
    })
    players.extend(records)
    players.sort(key=lambda r:(r["game_id"],r["team"],r.get("batting_slot",99),
                              r.get("batting_sub_index",99),
                              r.get("pitching_appearance_index",99),r["player_id"]))
    report.update({
        "official_player_boxscores_imported":sum(g["verification"]=="official_boxscore_verified" for g in games),
        "official_score_and_inning_lines_matched":sum(g["verification"]!="attendance_only" for g in games),
        "attendance_only_pending_official_verification":sum(g["verification"]=="attendance_only" for g in games),
        "player_stat_rows":len(players),"unique_player_ids":len({r["player_id"] for r in players}),
        "latest_verified_batch":"March 1 official Notre Dame–Tennessee Tech PDF; complete 2026 March",
    })
    audit={"status":"PASS","game_id":GAME_ID,"source_url":URL,
           "official_pdf_sha256":source_sha,"pdf_bytes":bytes_count,
           "source_date":"2026-03-01","source_score":[11,0],"innings":INNINGS,
           "player_rows_added":len(records),"team_audits":audits,
           "pdf_printed_name_correction":SOURCE_PRINTED_TYPO}
    for file,obj in [("games.json",games),("player_stats.json",players),
                     ("import_report.json",report),
                     ("2026_mar01_notredame_tenntech_pdf_audit.json",audit)]:
        (DATA/file).write_text(json.dumps(obj,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print("PASS university official PDF",GAME_ID,len(records),"player rows",flush=True)


if __name__=="__main__":
    main()
