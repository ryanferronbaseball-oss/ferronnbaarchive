#!/usr/bin/env python3
"""Correct attendee's Apr 14/Apr 13 2024 GT/VT game mismatch, replacing ALL player
lines with official Georgia Tech original seven-inning April 13 scorebook.

Original workbook row + attendance ID and original erroneous date are preserved.
No other game ID, official player row, or original JUCO exclusion is modified.
Run strict PDF parser before mutating output files, fail closed on mismatches.
"""
from pathlib import Path
from copy import deepcopy
from collections import Counter
import csv
import hashlib
import io
import json
import requests
from import_2024_pdf import parse as parse_university_pdf

D=Path(__file__).resolve().parents[1]/"data"
OLD="cb-2024-04-14-virginia-tech-georgia-tech-att0268"
NEW="cb-2024-04-13-virginia-tech-georgia-tech-att0268"
SOURCE="https://storage.googleapis.com/ramblinwreck-com-prod/2024/04/gt041324.pdf"
RHE={"away":(0,3,1),"home":(19,11,0)}
INNINGS=([0,0,0,0,0,0,0],[1,6,1,0,8,3,0])

def check(cond,message):
    if not cond:raise ValueError("User-verified April 13 game correction: "+message)

def read(name):
    return json.loads((D/name).read_text(encoding="utf-8"))

def write(name,body):
    (D/name).write_text(json.dumps(body,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")

def main():
    games=read("games.json")
    rows=read("player_stats.json")
    queue=read("2024_official_source_queue.json")
    report=read("import_report.json")
    check(len(games)==444 and report["official_player_boxscores_imported"]==437,"attendance or prior source verification changed")
    byid={g["id"]:g for g in games}
    check(len(byid)==444 and len(rows)==len({(r["game_id"],r["player_id"]) for r in rows})==report["player_stat_rows"],
          "original player rows not complete and unique")
    if NEW in byid and OLD not in byid:
        check(byid[NEW]["date"]=="2024-04-13" and byid[NEW]["source_url"]==SOURCE and
              (byid[NEW]["away_score"],byid[NEW]["home_score"])==(0,19),
              "Already migrated April 13 record differs from official source")
        print("April 13 corrected identity already installed; no duplicate modifications")
        return
    check(NEW not in byid and OLD in byid,"both original and corrected attended game identity present or missing")
    old=byid[OLD]
    check(old["date"]=="2024-04-14" and old["season"]==2024
          and (old["away"],old["home"])==("Virginia Tech","Georgia Tech")
          and (old["away_score"],old["home_score"])==(7,11)
          and old["source_worksheet_row"]==269
          and old["attendance_id"]=="cb-attended-0268"
          and old["source_url"].endswith("/gt041424.pdf")
          and old["verification"]=="official_boxscore_verified",
          "Original attendance April 14 wrongly sourced game identity mismatch")
    oldrows=[r for r in rows if r["game_id"]==OLD]
    check(len(oldrows)==34,"Original April 14 player-game record count differs from audited 34 rows")
    source_q=[x for x in queue["source_queue"] if x["game_id"]==OLD]
    check(len(source_q)==1 and source_q[0]["worksheet_row"]==269
          and source_q[0]["source_url"]==old["source_url"],"2024 university source queue wrong identity")
    # Parse source in-memory before editing any files.
    response=requests.get(SOURCE,timeout=45)
    response.raise_for_status()
    check(response.content.startswith(b"%PDF-") and len(response.content)>25000,
          "Expected actual original April 13 university PDF not provided")
    game=deepcopy(old)
    game.update({"id":NEW,"date":"2024-04-13",
                 "away_score":None,"home_score":None,
                 "attendance_date_original_worksheet":"2024-04-14",
                 "attendance_date_corrected_by_attendee":"2026-10-18",
                 "original_incorrect_game_id":OLD})
    item=deepcopy(source_q[0])
    item.update({"game_id":NEW,"date":"2024-04-13","source_url":SOURCE,
                 "official_score":[0,19],"expected_innings":7,
                 "attendee_corrected_from_date":"2024-04-14"})
    keys={(r["game_id"],r["player_id"]) for r in rows if r["game_id"]!=OLD}
    newrows,source_audit=parse_university_pdf(game,item,keys,response)
    check(len(newrows)==39 and len(source_audit["lineup_audit"])==2
          and [(x["team"],x["batter_rows"],x["substitutes"],x["pitcher_rows"])
               for x in source_audit["lineup_audit"]]==[
               ("Virginia Tech",14,5,8),("Georgia Tech",17,8,1)],
          "Original 4/13 source pinch-hitters, original nine slots or pitchers missing")
    check((game["away_score"],game["home_score"],
           game["away_hits"],game["home_hits"],
           game["away_errors"],game["home_errors"])==(0,19,3,11,1,0)
          and len(game["innings"])==7
          and ([x["away"] for x in game["innings"]],[x["home"] for x in game["innings"]])==INNINGS
          and game["pitching_decisions"]=={"win":"Cam Jones","loss":"Wyatt Parliament","save":None},
          "University original seven-inning R/H/E and scorer decisions mismatch")
    check(game["verification"]=="official_boxscore_verified"
          and len({r["batting_slot"] for r in newrows if r["team"]=="Georgia Tech" and "batting" in r})==9
          and any(r["player"]=="Cam Jones" and "pitching" in r and "batting" in r for r in newrows),
          "Missing source-verified Cam Jones two-way scorebook")
    index=games.index(old)
    games[index]=game
    players=[r for r in rows if r["game_id"]!=OLD]+newrows
    players.sort(key=lambda r:(r["game_id"],r["team"],r.get("batting_slot",99),
                r.get("batting_sub_index",99),r.get("pitching_appearance_index",99),r["player_id"]))
    check(len(players)==len(rows)+5==13188 and
          len({(r["game_id"],r["player_id"]) for r in players})==len(players)
          and all(r["game_id"]!=OLD for r in players),"Source correction did not fully replace April 14 rows")
    newgameids={x["id"] for x in games}
    check(len(games)==len(newgameids)==444 and
          set(g["id"] for g in games if g["id"] not in (NEW,OLD))==
          set(g["id"] for g in read("games.json") if g["id"] not in (OLD,NEW)),
          "Any unrelated game ID changed")
    all_verified=Counter(g["season"] for g in games if g["verification"]=="official_boxscore_verified")
    check(sum(all_verified.values())==437 and all_verified[2024]==71
          and sum(g.get("boxscore_backfill_excluded",False) for g in games)==7,
          "Original 437 official gamebooks or seven JUCO exclusions changed")
    q=source_q[0];q.clear();q.update(item)
    q.update({"game_type":"regular_season","ballpark":"Mac Nease Park","city":"Atlanta",
              "state":"GA","postseason_round":None,"neutral_site":False,
              "source_type":"official_university_pdf_scorebook",
              "verification":"attendee_corrected_attendance_date_exact_pdf_source_verified",
              "original_worksheet_date":"2024-04-14",
              "correction_source_pdf_sha256":source_audit["source_sha256"]})
    # Track original incorrectly imported date separately; player rows from
    # that April 14 matchup must not be retained in witnessed accumulations.
    game["notes"]=("User corrected original workbook row 269 attendance date from April 14 to "
                   "April 13, 2024 on October 18, 2026. Full source replaced, not shifted: "
                   "Georgia Tech 19-0 Virginia Tech, seven-inning mercy-rule game, "
                   "39 official player gamebook rows. Original imported April 14 game "
                   "was Georgia Tech 11-7 with 34 player rows and was NOT attended. "
                   "Source PDF "+SOURCE+".")
    game["game_type"]="regular_season"
    game["ballpark"]="Mac Nease Park"
    game["city"]="Atlanta"
    game["state"]="GA"
    game["source_type"]="official_university_pdf_scorebook"
    # Metadata and reporting
    report["player_stat_rows"]=len(players)
    report["unique_player_ids"]=len({r["player_id"] for r in players})
    report["official_player_boxscores_imported"]=437
    report["latest_verified_batch"]="User-confirmed original April 13 2024 GT–VT full gamebook replacement"
    report["last_attendee_game_identity_correction"]={"original_attendance_id":"cb-attended-0268",
        "worksheet_row":269,"original_date":"2024-04-14",
        "corrected_date":"2024-04-13",
        "old_game_id":OLD,"new_game_id":NEW,
        "old_player_game_rows_removed":34,"new_official_player_game_rows":39,
        "source":SOURCE}
    # Attendance CSV is a human-viewable correction layer. Original encoded
    # workbook history stays intact as provenance.
    csv_path=D/"attendance_master_444.csv"
    with csv_path.open(newline="",encoding="utf-8") as fp:
        reader=csv.DictReader(fp)
        records=list(reader);fields=reader.fieldnames
    matching=[v for v in records if v["attendance_id"]=="cb-attended-0268"]
    check(len(matching)==1 and matching[0]["date"]=="2024-04-14"
          and matching[0]["source_worksheet_row"]=="269"
          and matching[0]["away"]=="Virginia Tech" and matching[0]["home"]=="Georgia Tech",
          "Decoded original workbook CSV identity unexpected")
    matching[0].update({"date":"2024-04-13","away_score":"0","home_score":"19","source_url":SOURCE,
                        "ballpark":"Mac Nease Park","city":"Atlanta","state":"GA",
                        "notes":"User explicitly corrected workbook date 4/14 to 4/13 on Oct 18 2026; original workbook row 269 retained; official Georgia Tech 19-0 seven-inning scorebook."})
    check(len(records)==444,"Preserve original attendance source row count")
    audit={
        "status":"PASS",
        "user_attendance_date_correction_date":"2026-10-18",
        "attendance_id":"cb-attended-0268","worksheet_row":269,
        "original_worksheet_date":"2024-04-14",
        "corrected_attendance_date":"2024-04-13",
        "from_wrong_game_id":OLD,"to_correct_game_id":NEW,
        "wrong_unattended_original_2024_04_14_result":"Virginia Tech 7 Georgia Tech 11",
        "actual_attended_2024_04_13_result":"Virginia Tech 0 Georgia Tech 19 (7 innings)",
        "original_unattended_player_rows_removed":len(oldrows),
        "actual_attended_official_player_rows":len(newrows),
        "original_full_season_source_scorebook":SOURCE,
        "original_full_season_source_sha256":hashlib.sha256(response.content).hexdigest(),
        "official_source_audit":source_audit,
        "prior_player_rows":len(rows),"new_player_rows":len(players),
        "all_attendance_ids_preserved":444,"all_verified_games_preserved":437,
        "source_team_batting_slots":{"Virginia Tech":9,"Georgia Tech":9}
    }
    # Commit only after all preceding checks have passed.
    write("games.json",games)
    write("player_stats.json",players)
    write("2024_official_source_queue.json",queue)
    write("import_report.json",report)
    write("2024_apr13_attendee_correction_audit.json",audit)
    out=io.StringIO(newline="")
    w=csv.DictWriter(out,fieldnames=fields,lineterminator="\r\n")
    w.writeheader();w.writerows(records)
    csv_path.write_text(out.getvalue(),encoding="utf-8",newline="")
    print(json.dumps({"status":"PASS","corrected_game_id":NEW,
        "old_wrong_game_player_lines_removed":len(oldrows),
        "new_official_player_lines":len(newrows),
        "original_attendance_games":len(games),
        "total_player_stat_rows":len(players)},indent=2),flush=True)

if __name__=="__main__":
    main()
