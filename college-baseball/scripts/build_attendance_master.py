#!/usr/bin/env python3
"""Expand a lossless 444-row source file into verified + attendance-only games."""
import base64, csv, io, json, re, sys, unicodedata, zlib
from collections import Counter
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
DATA=ROOT/"data"
COLS=["date","away","home","ballpark","city","state","neutral_site","game_number","game_type","postseason_round","away_score","home_score","source_url","notes"]
ALIASES={"North Carolina State":"NC State","Central Florida":"UCF"}
CONFIRMED_BALLPARK_EXCEPTIONS={
    "2018-02-23": {("Cal Poly", "Arkansas"): ("Tony Gwynn Stadium", "San Diego", "CA")},
    "2019-02-19": {("UC Irvine", "San Diego State"): ("Tony Gwynn Stadium", "San Diego", "CA")},
    "2019-02-26": {("San Diego", "San Diego State"): ("Tony Gwynn Stadium", "San Diego", "CA")},
    "2019-03-05": {("San Diego", "UC Riverside"): ("Riverside Sports Complex", "Riverside", "CA")},
    "2019-03-26": {("San Diego", "UC Irvine"): ("Anteater Ballpark", "Irvine", "CA")},
    **{d: {("San Diego", "Santa Clara"): ("Stephen Schott Stadium", "Santa Clara", "CA")}
       for d in ("2019-05-03", "2019-05-04", "2019-05-05")},
}


CONFIRMED_2021_BALLPARK_DATES={
    "2021-02-19": ("Tony Gwynn Stadium", "San Diego", "CA"),
    "2021-02-20": ("Tony Gwynn Stadium", "San Diego", "CA"),
    "2021-03-04": ("Triton Ballpark", "La Jolla", "CA"),
    "2021-03-05": ("Triton Ballpark", "La Jolla", "CA"),
    "2021-03-11": ("Triton Ballpark", "La Jolla", "CA"),
    "2021-03-23": ("Dedeaux Field", "Los Angeles", "CA"),
    "2021-04-02": ("Goodwin Field", "Fullerton", "CA"),
    "2021-04-24": ("Triton Ballpark", "La Jolla", "CA"),
}


CONFIRMED_2022_BALLPARK_DATES={
    **{f"2022-03-{day:02d}": ("Brazell Field", "Phoenix", "AZ") for day in (11, 12, 13)},
    **{f"2022-03-{day:02d}": ("Eddy D. Field Stadium", "Malibu", "CA") for day in (18, 19, 20)},
    "2022-03-29": ("James W. Totman Stadium", "Riverside", "CA"),
    **{f"2022-04-{day:02d}": ("Benedetti Diamond", "San Francisco", "CA") for day in (1, 2, 3)},
    "2022-04-05": ("Triton Ballpark", "La Jolla", "CA"),
    "2022-05-22": ("Triton Ballpark", "La Jolla", "CA"),
    "2022-04-08": ("Joe Etzel Field", "Portland", "OR"),
    "2022-04-09": ("Joe Etzel Field", "Portland", "OR"),
    "2022-04-18": ("Tony Gwynn Stadium", "San Diego", "CA"),
    "2022-04-22": ("Tony Gwynn Stadium", "San Diego", "CA"),
    "2022-04-26": ("Goodwin Field", "Fullerton", "CA"),
    "2022-05-03": ("Anteater Ballpark", "Irvine", "CA"),
    "2022-05-06": ("Klein Family Field", "Stockton", "CA"),
    "2022-05-07": ("Klein Family Field", "Stockton", "CA"),
    "2022-05-08": ("Klein Family Field", "Stockton", "CA"),
    **{f"2022-05-{day:02d}": ("Banner Island Ballpark", "Stockton", "CA") for day in (25, 26, 27, 28)},
    **{f"2022-06-{day:02d}": ("Goss Stadium", "Corvallis", "OR") for day in (3, 4, 5)},
}


CONFIRMED_2023_BALLPARK_DATES={
    "2023-02-21": ("Tony Gwynn Stadium", "San Diego", "CA"),
    "2023-04-18": ("Tony Gwynn Stadium", "San Diego", "CA"),
    **{f"2023-03-{day:02d}": ("PK Park", "Eugene", "OR") for day in (2, 3, 4, 5)},
    "2023-03-07": ("Goss Stadium", "Corvallis", "OR"),
    "2023-03-28": ("Matador Field", "Northridge", "CA"),
    "2023-04-04": ("Triton Ballpark", "La Jolla", "CA"),
    "2023-05-07": ("Triton Ballpark", "La Jolla", "CA"),
    **{f"2023-04-{day:02d}": ("Patterson Baseball Complex", "Spokane", "WA") for day in (6, 7, 8)},
    **{f"2023-04-{day:02d}": ("Page Stadium", "Los Angeles", "CA") for day in (28, 29, 30)},
    **{f"2023-05-{day:02d}": ("Louie Guisto Field", "Moraga", "CA") for day in (12, 13, 14)},
    "2023-05-24": ("Las Vegas Ballpark", "Las Vegas", "NV"),
}


CONFIRMED_2024_BALLPARK_DATES={
    "2024-02-19": ("Patriots Point", "Mount Pleasant", "SC"),
    "2024-02-21": ("Founders Park", "Columbia", "SC"),
    **{f"2024-02-{day:02d}": ("VyStar Ballpark", "Jacksonville", "FL")
       for day in (23, 24, 25)},
}


CONFIRMED_2024_BALLPARK_MATCHUPS={
    ("2024-03-01", "Cal State Fullerton", "Southeastern Louisiana"):
        ("Lewis Field at Clark-LeClair Stadium", "Greenville", "NC"),
    ("2024-03-02", "Illinois", "Western Michigan"):
        ("Fluor Field", "Greenville", "SC"),
    ("2024-03-02", "Florida State", "Illinois"):
        ("Fluor Field", "Greenville", "SC"),
    ("2024-03-03", "Maine", "Winthrop"):
        ("Winthrop Ballpark", "Rock Hill", "SC"),
    ("2024-03-08", "Binghamton", "VMI"):
        ("Lamore Field at Gray-Minor Stadium", "Lexington", "VA"),
    ("2024-03-26", "William and Mary", "VCU"):
        ("The Diamond", "Richmond", "VA"),
    ("2024-03-29", "Sam Houston State", "Liberty"):
        ("Worthington Field at Liberty Baseball Stadium", "Lynchburg", "VA"),
    ("2024-03-30", "South Alabama", "Old Dominion"):
        ("Bud Metheny Ballpark", "Norfolk", "VA"),
    ("2024-04-21", "Connecticut", "Georgetown"):
        ("Capital One Park", "Tysons", "VA"),
}


CONFIRMED_2026_HOME_BALLPARKS={
    "Tennessee": ("Lindsey Nelson Stadium", "Knoxville", "TN"),
    "Louisville": ("Jim Patterson Stadium", "Louisville", "KY"),
    "Kentucky": ("Kentucky Proud Park", "Lexington", "KY"),
    "Vanderbilt": ("Hawkins Field", "Nashville", "TN"),
}


def confirmed_ballpark(game):
    """User-confirmed historical locations; respect 2024 partial-year updates."""
    if game["season"]==2021:
        return CONFIRMED_2021_BALLPARK_DATES.get(
            game["date"], ("Fowler Park", "San Diego", "CA"))
    if game["season"]==2022:
        return CONFIRMED_2022_BALLPARK_DATES.get(
            game["date"], ("Fowler Park", "San Diego", "CA"))
    if game["season"]==2026:
        if (game.get("game_type")=="conference_tournament"
            or "SEC Tournament" in str(game.get("postseason_round") or "")
            or game.get("neutral_site") is True):
            return None
        return CONFIRMED_2026_HOME_BALLPARKS.get(game["home"])
    if game["season"]==2024:
        return (CONFIRMED_2024_BALLPARK_MATCHUPS.get(
            (game["date"], game["away"], game["home"]))
            or CONFIRMED_2024_BALLPARK_DATES.get(game["date"]))
    if game["season"]==2023:
        return CONFIRMED_2023_BALLPARK_DATES.get(
            game["date"], ("Fowler Park", "San Diego", "CA"))
    if game["season"] not in (2017, 2018, 2019, 2020):
        return None
    return CONFIRMED_BALLPARK_EXCEPTIONS.get(game["date"], {}).get(
        (game["away"], game["home"]), ("Fowler Park", "San Diego", "CA")
    )

# Exclude NJCAA/junior-college games from box-score backfill; retain source attendance rows.
JUNIOR_COLLEGE_TEAMS={"Walters State","Pellissippi State","USC Salkehatchie","Wabash Valley"}


def clean(s):
    t=unicodedata.normalize("NFKD",s).encode("ascii","ignore").decode().lower()
    return re.sub(r"(^-+|-+$)","",re.sub(r"-+","-",re.sub(r"[^a-z0-9]+","-",t)))

def load_source():
    raw=base64.b64decode((DATA/"attendance_source_444.deflate.b64").read_text().strip(),validate=True)
    rows=json.loads(zlib.decompress(raw))
    assert len(rows)==444 and all(len(x)==len(COLS) for x in rows),"invalid attendance source"
    return [dict(zip(COLS,x)) for x in rows]

def build(source,prior):
    # Preserve independently verified gamebooks, source-matched scoreboards and
    # user-confirmed attendance identities when rebuilding from the old workbook.
    # Otherwise the source-only rows and confirmed doubleheader game numbers get wiped.
    retained={g["source_worksheet_row"]:g for g in prior if g.get("verification") in (
        "official_boxscore_verified","official_scoreboard_verified","source_matched"
    )}
    assert len(retained)>=6 and len(retained)==len(set(retained)),"missing imported game records"
    approved_date_corrections={287:("2024-05-23","2024-05-24")}
    doubles=Counter((x["date"],x["away"].lower(),x["home"].lower()) for x in source)
    result=[]
    for number,row in enumerate(source,1):
        sheetrow=number+1
        date=row["date"]
        away=ALIASES.get(row["away"],row["away"])
        home=ALIASES.get(row["home"],row["home"])
        assert re.fullmatch(r"\d{4}-\d{2}-\d{2}",date) and away!=home
        if sheetrow in retained:
            g=retained[sheetrow]
            # The original workbook date was explicitly corrected by the user.
            date_is_approved=(
                sheetrow in approved_date_corrections
                and approved_date_corrections[sheetrow]==(date,g["date"])
            )
            assert (g["date"]==date or date_is_approved) and (
                g["away"],g["home"]
            )==(away,home),"source/verified game identity conflict"
            venue=confirmed_ballpark(g)
            if venue:
                g={**g,"ballpark":venue[0],"city":venue[1],"state":venue[2]}
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
        if away in JUNIOR_COLLEGE_TEAMS or home in JUNIOR_COLLEGE_TEAMS:
            g["boxscore_backfill_excluded"]=True
            g["boxscore_backfill_exclusion_reason"]="junior_college"
        venue=confirmed_ballpark(g)
        if venue:
            g.update(zip(("ballpark","city","state"),venue))
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
    scores=sum(g["verification"]=="official_scoreboard_verified" for g in entries)
    matched=sum(g["verification"]=="source_matched" for g in entries)
    pending=sum(g["verification"]=="attendance_only" for g in entries)
    assert official+scores+matched+pending==444
    print("Attendance",len(entries),"Official gamebooks",official,"Scores only",scores,
          "Source matched",matched,"Attendance only",pending)
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
        "attendance_only_pending_official_verification":pending,
        "official_score_and_inning_lines_matched":sum(
            bool(g.get("innings")) and g.get("away_score") is not None
            and g.get("home_score") is not None for g in entries
        ),
        "official_scoreboard_player_lines_pending":scores+matched,
        "source_matched_player_lines_pending":matched,
        "official_player_boxscores_imported":official,
        "source":"User workbook; 444 original rows, two user-corrected entries.",
        "warning":"All 444 attendance matchups listed. Full player statistics count only after complete gamebook verification; source-matched records are still pending. User-confirmed 2024 doubleheader identities and 2024-05-24 Florida State–Virginia date are preserved."
    })
    rp.write_text(json.dumps(report,indent=2,ensure_ascii=False)+"\n")
if __name__=="__main__":main()
