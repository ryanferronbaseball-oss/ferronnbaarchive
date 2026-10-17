#!/usr/bin/env python3
"""Expand a lossless 444-row source file into verified + attendance-only games."""
import base64, csv, io, json, re, sys, unicodedata, zlib
from collections import Counter
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
DATA=ROOT/"data"
COLS=["date","away","home","ballpark","city","state","neutral_site","game_number","game_type","postseason_round","away_score","home_score","source_url","notes"]
ALIASES={"North Carolina State":"NC State","Central Florida":"UCF"}

def clean(s):
    t=unicodedata.normalize("NFKD",s).encode("ascii","ignore").decode().lower()
    return re.sub(r"(^-+|-+$)","",re.sub(r"-+","-",re.sub(r"[^a-z0-9]+","-",t)))

def load_source():
    raw=base64.b64decode((DATA/"attendance_source_444.deflate.b64").read_text().strip(),validate=True)
    rows=json.loads(zlib.decompress(raw))
    assert len(rows)==444 and all(len(x)==len(COLS) for x in rows),"invalid attendance source"
    return [dict(zip(COLS,x)) for x in rows]

def build(source,prior):
    official={g["source_worksheet_row"]:g for g in prior if g.get("verification")=="official_boxscore_verified"}
    assert len(official)>=6 and len(official)==len(set(official)),"missing official scorebooks"
    doubles=Counter((x["date"],x["away"].lower(),x["home"].lower()) for x in source)
    result=[]
    for number,row in enumerate(source,1):
        sheetrow=number+1
        date=row["date"]
        away=ALIASES.get(row["away"],row["away"])
        home=ALIASES.get(row["home"],row["home"])
        assert re.fullmatch(r"\d{4}-\d{2}-\d{2}",date) and away!=home
        if sheetrow in official:
            g=official[sheetrow]
            assert (g["date"],g["away"],g["home"])==(date,away,home),"pilot source conflict"
            result.append(g)
            continue
        a,b=row["away_score"],row["home_score"]
        assert bool(a)==bool(b),"partial scores in attendance source"
        neutral={"yes":True,"no":False,"":None}.get(row["neutral_site"].lower())
        g={
            "id":f"cb-{date}-{clean(away)}-{clean(home)}-att{number:04d}",
            "attendance_id":f"cb-attended-{number:04d}",
            "source_worksheet_row":sheetrow,
            "date":date,"season":int(date[:4]),"away":away,"home":home,
            "ballpark":row["ballpark"] or None,"city":row["city"] or None,
            "state":row["state"] or None,"neutral_site":neutral,
            "game_number":None,"game_type":row["game_type"] or None,
            "postseason_round":row["postseason_round"] or None,
            "away_score":int(a) if a else None,"home_score":int(b) if b else None,
            "score_provenance":"user_attendance_log" if a else None,
            "source_url":row["source_url"] or None,
            "verification":"attendance_only","official_boxscore_status":"not_imported",
            "possible_same_day_doubleheader":doubles[(date,row["away"].lower(),row["home"].lower())]>1,
            "provisional_worksheet_game_sequence":int(row["game_number"]) if row["game_number"] else None,
            "notes":row["notes"] or None
        }
        result.append(g)
    assert len(result)==len({g["id"] for g in result})==444
    assert len({g["source_worksheet_row"] for g in result})==444
    assert (result[265]["date"],result[265]["away"],result[265]["home"])==("2024-03-30","South Alabama","Old Dominion")
    assert (result[-1]["away"],result[-1]["home"])==("UCF","Auburn")
    return result

def main():
    source=load_source()
    previous=json.loads((DATA/"games.json").read_text())
    entries=build(source,previous)
    official=sum(g["verification"]=="official_boxscore_verified" for g in entries)
    print("Attendance",len(entries),"Official gamebooks",official,"Attendance only",len(entries)-official)
    if "--validate-only" in sys.argv:return
    (DATA/"games.json").write_text(json.dumps(entries,indent=2,ensure_ascii=False)+"\n")
    with (DATA/"attendance_master_444.csv").open("w",newline="",encoding="utf-8") as h:
        fields=["attendance_id","source_worksheet_row"]+COLS
        writer=csv.DictWriter(h,fieldnames=fields)
        writer.writeheader()
        for i,r in enumerate(source,1):
            writer.writerow({"attendance_id":f"cb-attended-{i:04d}","source_worksheet_row":i+1,**r})
    rp=DATA/"import_report.json"
    report=json.loads(rp.read_text())
    report.update({
        "status":"all_attendance_staged_source_verification_in_progress",
        "staged_games":444,"all_attendance_entries_staged":444,
        "unimported_worksheet_rows":0,
        "attendance_only_pending_official_verification":444-official,
        "official_player_boxscores_imported":official,
        "source":"User workbook; 444 original rows, two user-corrected entries.",
        "warning":"All 444 attendance matchups listed. Only individually sourced gamebooks have verified scores and player statistics. Unresolved doubleheaders retain distinct source IDs; original ordering is not taken as official."
    })
    rp.write_text(json.dumps(report,indent=2,ensure_ascii=False)+"\n")
if __name__=="__main__":main()
