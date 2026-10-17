#!/usr/bin/env python3
"""Source-gated 2024 college-baseball import, respecting original 444 attendance IDs.

The user explicitly authorized all 2024 four-year NCAA games on 2026-10-17.
Preserve approved verified 2025/2026 player gamebooks and every pre-2024 row.
Exclude any JUCO; include properly verified NCAA Division II scorebooks.
Never publish or import 2023 and earlier.
"""
from collections import Counter
from copy import deepcopy
from pathlib import Path
import json
import requests
from bs4 import BeautifulSoup
from import_2026_remaining_ncaa import import_one
from import_2025_verified_queue import scorer_labels

DATA=Path(__file__).resolve().parents[1]/"data"
YEAR="2024"
def read(name):return json.loads((DATA/name).read_text(encoding="utf-8"))
def write(name,obj):(DATA/name).write_text(json.dumps(obj,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")

def main():
    games=read("games.json")
    players=read("player_stats.json")
    report=read("import_report.json")
    source=read("2024_official_source_queue.json")
    assert len(games)==444==len({g["id"] for g in games})
    byid={g["id"]:g for g in games}
    original_2024={g["id"]:deepcopy(g) for g in games if g["date"].startswith(YEAR)}
    assert len(original_2024)==71
    protected_games={g["id"]:deepcopy(g) for g in games if not g["date"].startswith(YEAR)}
    protected_player_game_ids=set(protected_games)
    protected_rows=[deepcopy(p) for p in players if p["game_id"] in protected_player_game_ids]
    player_keys={(p["game_id"],p["player_id"]) for p in players}
    assert len(player_keys)==len(players)
    sessions=requests.Session()
    sessions.headers["User-Agent"]="Mozilla/5.0 Courtside Archive source audit (official university pages)"
    queue_ids=set()
    added=[];pending=[]
    for item in source["source_queue"]:
        gid=item["game_id"]
        if gid in queue_ids:raise ValueError("2024 source queue has duplicate attendance ID: "+gid)
        queue_ids.add(gid)
        g=byid.get(gid)
        if g is None or not g["date"].startswith(YEAR) or g.get("boxscore_backfill_excluded"):
            raise ValueError("Source queue outside 2024 approved NCAA/four-year scope: "+gid)
        if any(g.get(k)!=item[k] for k in ("date","away","home","source_worksheet_row") if k in item):
            raise ValueError("Official university source does not match original attendance identity: "+gid)
        if g.get("source_worksheet_row")!=item["worksheet_row"]:
            raise ValueError("Original workbook row differs from source queue: "+gid)
        url=item["source_url"]
        if g.get("verification")=="official_boxscore_verified":
            known=[p for p in players if p["game_id"]==gid]
            if g.get("source_url")!=url or len(known)<18:
                raise ValueError("Previously verified 2024 gamebook has changed source/players: "+gid)
            continue
        if g.get("verification") not in ("attendance_only", "source_matched"):
            pending.append({"game_id":gid,"source_url":url,"reason":"Prior source state requires review"})
            continue
        snapshot=deepcopy(g)
        original_keys=set(player_keys)
        try:
            if not url.startswith("https://") or url.lower().split("?")[0].endswith(".pdf"):
                raise ValueError("Not a verifiable official university HTML boxscore; PDF requires separate source transcription")
            response=sessions.get(url,timeout=45);response.raise_for_status()
            src=BeautifulSoup(response.text,"html.parser").get_text(" ",strip=True)
            yy,mm,dd=(int(n) for n in item["date"].split("-"))
            formats={f"{mm}/{dd}/{yy}",f"{mm:02d}/{dd:02d}/{yy}",
                f"{mm}/{dd:02d}/{yy}",f"{mm:02d}/{dd}/{yy}",
                f"{mm}/{dd}/{yy%100:02d}",f"{mm:02d}/{dd:02d}/{yy%100:02d}",
                f"{mm}/{dd:02d}/{yy%100:02d}"}
            if item.get("legacy_statcrew_source"):
                from datetime import date as _date
                dt=_date(yy,mm,dd)
                formats.update({dt.strftime("%b %d, %Y"),
                                dt.strftime("%B %d, %Y"),
                                dt.strftime("%b %d, %Y").replace(" 0"," "),
                                dt.strftime("%B %d, %Y").replace(" 0"," ")})
                soup=BeautifulSoup(response.text,"html.parser")
                sample_pres=[p.get_text() for p in soup.find_all("pre")]
                sample_tables=soup.find_all("table")
                print("STATCREW-DIAG",gid,"bytes",len(response.content),
                      "pre",len(sample_pres),"table",len(sample_tables),
                      "first_pre",repr(next((p[:1300] for p in sample_pres if "Player" in p or "Box Score" in p),"")),
                      "first_table",repr(next((t.get_text(" ",strip=True)[:500] for t in sample_tables
                                               if "Player" in t.get_text(" ",strip=True)),"")),
                      flush=True)
                if "virginiasports.com/custompages" in url:
                    print("STATCREW-VA-DETAIL",gid,
                          "tables",[(i, len(t.find_all("tr")),
                                     [c.get_text(" ",strip=True) for c in t.find_all("tr")[:3]][:3])
                                    for i,t in enumerate(sample_tables)],
                          "pres",[(len(p),repr(p[:850])) for p in sample_pres],flush=True)
            if not any(v in src for v in formats):
                # 2024 opening-day Duke vs Indiana: Indiana's official
                # 2024 text schedule explicitly says Friday Feb 16, while
                # BOTH universities' archived individual boxscore headers
                # incorrectly read Feb 15 for the identical 6-3 contest.
                # Preserve the attended/official-schedule date and document
                # this ONE exception instead of rewriting it to the error.
                duke_iu_date_exception=(
                    gid=="cb-2024-02-16-duke-indiana-att0225"
                    and item.get("source_date_exception")=="indiana_2024_official_schedule_feb16"
                    and "2/15/2024" in src
                    and item["official_score"]==[6,3])
                if not duke_iu_date_exception:
                    raise ValueError("University scorebook does not visibly confirm attendance date")
            rows,stat_audit=import_one(g,item,player_keys)
            # Charleston's official February 19 scorebook abbreviates its
            # two winning/closing pitchers in the batting/pitching tables
            # as E. Bice / D. Aiken, but explicitly credits Emmett Bice
            # (W) and Davis Aiken (SV) with the full given names.
            # Require exact original abbreviated rows and exact game/team.
            if gid=="cb-2024-02-19-marshall-college-of-charleston-att0231":
                for abbreviated,canonical in (
                    ("E. Bice","Emmett Bice"),("D. Aiken","Davis Aiken")):
                    matches=[p for p in rows if p["team"]=="College of Charleston"
                             and p["player"]==abbreviated and "pitching" in p]
                    if len(matches)!=1:
                        raise ValueError("Official Charleston pitcher abbreviation not uniquely resolved: "+abbreviated)
                    p=matches[0]
                    old_key=(gid,p["player_id"])
                    new_id="cb-college-of-charleston-"+canonical.lower().replace(" ","-")
                    new_key=(gid,new_id)
                    if old_key not in player_keys or (new_key in player_keys and new_key!=old_key):
                        raise ValueError("Charleston pitcher identity mapping collision")
                    player_keys.remove(old_key); player_keys.add(new_key)
                    p["player"]=canonical
                    p["player_id"]=new_id
            decision=scorer_labels(response.text,rows,gid)
            g.update({"game_type":item["game_type"],
                      "postseason_round":item.get("postseason_round"),
                      "ballpark":item["ballpark"],"city":item["city"],"state":item["state"],
                      "neutral_site":bool(item.get("neutral_site",False)),
                      "source_type":item["source_type"],
                      "pitching_decisions":decision})
            if g["verification"]!="official_boxscore_verified" or len(rows)<18:
                raise ValueError("Source did not yield fully reconciled gamebook")
            players.extend(rows)
            added.append({"game_id":gid,"source_url":url,"score":item["official_score"],
                          "player_game_rows":len(rows),"pitching_decisions":decision,
                          "stat_audit":stat_audit})
            print("PASS 2024",gid,len(rows),flush=True)
        except Exception as err:
            g.clear();g.update(snapshot)
            player_keys.clear();player_keys.update(original_keys)
            pending.append({"game_id":gid,"source_url":url,"reason":str(err)})
            print("REVIEW 2024",gid,str(err),flush=True)
    assert len(games)==444 and len({g["id"] for g in games})==444
    assert all(byid[gid]==old for gid,old in protected_games.items()),"2025/2026 or prior record changed!"
    assert [p for p in players if p["game_id"] in protected_player_game_ids]==protected_rows
    assert all(byid[gid].get("verification")=="attendance_only"
               for gid,g in original_2024.items() if g.get("boxscore_backfill_excluded"))
    assert len(player_keys)==len({(p["game_id"],p["player_id"]) for p in players})==len(players)
    players.sort(key=lambda p:(p["game_id"],p["team"],p.get("batting_slot",99),
               p.get("batting_sub_index",99),p.get("pitching_appearance_index",99),p["player_id"]))
    total=sum(g["date"].startswith(YEAR) and g["verification"]=="official_boxscore_verified" for g in games)
    months=Counter(g["date"][:7] for g in games if g["date"].startswith(YEAR) and g["verification"]=="official_boxscore_verified")
    if added:
        report["official_player_boxscores_imported"]=sum(g["verification"]=="official_boxscore_verified" for g in games)
        report["official_score_and_inning_lines_matched"]=sum(g["verification"]!="attendance_only" for g in games)
        report["attendance_only_pending_official_verification"]=sum(g["verification"]=="attendance_only" for g in games)
        report["player_stat_rows"]=len(players)
        report["unique_player_ids"]=len({p["player_id"] for p in players})
        report["latest_verified_batch"]="2024 official university baseball gamebooks including NCAA Division II"
    report["2024_backfill"]={"authorized":True,"original_attendance_games":71,
                           "verified_full_player_gamebooks":total,
                           "source_queue_size":len(queue_ids),
                           "linked_source_exceptions":len(pending),
                           "remaining_attendance_only":71-total}
    gate=report.setdefault("monthly_review_gate",{})
    gate["season_2024"]={"approved":True,"complete":total,"eligible":71,"status":"in_progress"}
    gate["season_2023"]={"approved":False}
    gate["publication"]={"approved":False}
    report["warning"]=("2024–2026 four-year NCAA/four-year verified source-gamebooks only; "
        "all junior colleges excluded from backfill. 2023 and earlier, merge/publication unapproved.")
    audit={"status":"PASS" if not pending else "PARTIAL_REVIEW_REQUIRED",
           "approval":"2024–2026 official four-year source backfill; no 2023 or earlier, no release",
           "original_attendance":444,"attendance_2024":71,
           "verified_2024_total":total,"remaining_2024":71-total,
           "2025_gamebooks_preserved":sum(g["date"].startswith("2025") and g["verification"]=="official_boxscore_verified" for g in games),
           "2026_gamebooks_preserved":sum(g["date"].startswith("2026") and g["verification"]=="official_boxscore_verified" for g in games),
           "completed_in_this_run":len(added),"linked_2024_sources":len(queue_ids),
           "months_verified":dict(sorted(months.items())),"passed_games":added,
           "pending_review":pending}
    if added:
        write("games.json",games)
        write("player_stats.json",players)
    write("import_report.json",report)
    write("2024_source_import_audit.json",audit)
    print(json.dumps({"status":audit["status"],"new":len(added),"verified_2024":total,
         "previous_seasons_verified":audit["2025_gamebooks_preserved"]+audit["2026_gamebooks_preserved"],
         "pending_source_exceptions":len(pending)},indent=2),flush=True)

if __name__=="__main__":main()
