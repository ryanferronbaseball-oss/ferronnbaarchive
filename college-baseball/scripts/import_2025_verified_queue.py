#!/usr/bin/env python3
"""Source-gated import of 2025 four-year college baseball gamebooks.

Every import is tied to an unchanged original attendance row and a human-identified
official university box-score URL. Require exact school/date, R/H/E and inning line,
all player hitting/pitching totals, real nine-slot batting order, source substitutions,
and unique official win/loss/save decisions. Preserve verified 2026 and all JUCO.
"""
from copy import deepcopy
from pathlib import Path
import json
import re
import requests
from bs4 import BeautifulSoup
from import_2026_remaining_ncaa import import_one
from reconcile_2026_official_pitching_decisions import name_variants

DATA=Path(__file__).resolve().parents[1]/"data"
def read(name):return json.loads((DATA/name).read_text(encoding="utf-8"))
def write(name,obj):(DATA/name).write_text(json.dumps(obj,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")

def scorer_labels(page, rows, gid):
    text=BeautifulSoup(page,"html.parser").get_text(" ",strip=True)
    found={}
    for label in ("Win","Loss","Save"):
        # Source is always the originally identified official university gamebook.
        pattern=(rf"\b{label}\s*:\s*([^\n:]*?)\s*\(\d+-\d+\)"
            if label!="Save" else r"\bSave\s*:\s*([^\n:]*?)\s*\(\d+\)")
        match=re.search(pattern,text,re.I)
        if not match:
            if label=="Save":
                found["save"]=None
                continue
            raise ValueError(f"Source does not state official {label}: {gid}")
        name=match.group(1).strip(" ,;.")
        pitchers=[r for r in rows if "pitching" in r]
        matches=[r for r in pitchers if name_variants(r["player"]) & name_variants(name)]
        if not matches:
            # Some old Sidearm gamebooks show just the pitcher's last name.
            surname_matches=[r for r in pitchers if r["player"].split()[-1].casefold()==name.casefold()]
            if len(surname_matches)==1:matches=surname_matches
        if len(matches)!=1:
            raise ValueError(f"Official {label} scorer {name!r} not uniquely matched among source pitchers {gid}")
        found[label.lower()]=matches[0]["player"]
    if found["win"]==found["loss"]:
        raise ValueError("Official scorer W and L identical")
    for r in rows:
        if "pitching" in r:
            for label,field in (("win","wins"),("loss","losses"),("save","saves")):
                r["pitching"][field]=int(found[label] is not None and r["player"]==found[label])
    return found

def main():
    games=read("games.json")
    original_count=len(games)
    players=read("player_stats.json")
    report=read("import_report.json")
    queue=read("2025_official_source_queue.json")
    byid={g["id"]:g for g in games}
    assert original_count==444==len(byid)
    before_2026={g["id"]:deepcopy(g) for g in games if g["date"].startswith("2026")}
    before_stats_2026=[deepcopy(s) for s in players if s["game_id"] in before_2026]
    before_pre2025={g["id"]:deepcopy(g) for g in games if g["date"]<"2025-01-01"}
    before_2025_rows={g["id"]:g for g in games if g["date"].startswith("2025")}
    assert len(before_2025_rows)==74
    global_keys={(s["game_id"],s["player_id"]) for s in players}
    assert len(global_keys)==len(players)
    verified=[];pending=[]
    session=requests.Session()
    session.headers["User-Agent"]="Mozilla/5.0 Courtside Archive Official Source Audit"
    source_keys=set()
    for item in queue["source_queue"]:
        gid=item["game_id"]
        if gid in source_keys:raise ValueError("Duplicate 2025 source queue game ID "+gid)
        source_keys.add(gid)
        game=byid.get(gid)
        if game is None or not game["date"].startswith("2025") or game.get("boxscore_backfill_excluded"):
            raise ValueError("Source queue game outside 2025 approved eligible scope "+gid)
        if any(game.get(k)!=item[k] for k in ("date","away","home")):
            raise ValueError("Official source game identity disagrees with original attendance "+gid)
        url=item["source_url"]
        # Capture this game's own identity before any request or parser failure.
        # Never reuse a prior loop iteration's snapshot for a different game.
        snapshot=deepcopy(game)
        snapshot_keys=set(global_keys)
        if game["verification"]=="official_boxscore_verified":
            prior=[p for p in players if p["game_id"]==gid]
            if not prior or game.get("source_url")!=url or len(prior)<18:
                raise ValueError("Previously verified stats unexpectedly changed "+gid)
            continue
        if game["verification"]!="attendance_only":
            pending.append({"game_id":gid,"reason":"Original status is not attendance-only"})
            continue
        try:
            if url.lower().split("?")[0].endswith(".pdf"):
                raise ValueError("Official source PDF identified; separate PDF line transcription required")
            # Source dates are visibly checked, not inferred from a relative URL.
            resp=session.get(url,timeout=40)
            resp.raise_for_status()
            soup=BeautifulSoup(resp.text,"html.parser")
            src=soup.get_text(" ",strip=True)
            yy,mm,dd=(int(n) for n in game["date"].split("-"))
            visible_date=f"{mm}/{dd}/{yy}"
            if visible_date not in src and f"{mm}/{dd:02d}/{yy}" not in src and f"{mm:02d}/{dd:02d}/{yy}" not in src and f"{mm:02d}/{dd}/{yy}" not in src:
                raise ValueError("Official school boxscore doesn't visibly confirm attendance date")
            # import_one itself re-reads the page and reconciles both official
            # batter/pitcher tables and nine source starter/substitution slots.
            rows,audit=import_one(game,item,global_keys)
            # Mississippi State's 2025 May 21 university stat table truncates
            # the losing pitcher's visible name to "Mcpherson", while its
            # *same official gamebook* credits "Mcpherson, Ryan (4-1)".
            # Use the full verified scorer name to avoid a false player ID.
            if gid=="cb-2025-05-21-texas-a-m-mississippi-state-att0353":
                matches=[p for p in rows if p["team"]=="Mississippi State"
                         and p["player"].casefold()=="mcpherson" and "pitching" in p]
                if len(matches)!=1:
                    raise ValueError("Cannot map official Mississippi State scorer to single source pitcher")
                p=matches[0]
                old=p["player_id"]
                p["player"]="Ryan Mcpherson"
                p["player_id"]="cb-mississippi-state-ryan-mcpherson"
                global_keys.remove((gid,old))
                if (gid,p["player_id"]) in global_keys:
                    raise ValueError("Official Mississippi State pitcher identity collision")
                global_keys.add((gid,p["player_id"]))
            decisions=scorer_labels(resp.text,rows,gid)
            game.update({
               "game_type":item["game_type"],
               "postseason_round":item["postseason_round"],
               "ballpark":item["ballpark"],
               "city":item["city"],"state":item["state"],
               "neutral_site":True,
               "pitching_decisions":decisions,
               "source_type":item["source_type"],
            })
            if game["game_type"]=="ncaa_postseason":
                game["postseason_round"]="NCAA Regional"
            players.extend(rows)
            verified.append({"game_id":gid,"source_url":url,"score":item["official_score"],
                             "source_game_id":item["source_game_id"],"player_rows":len(rows),
                             "source_stat_audit":audit,"pitching_decisions":decisions})
            print("PASS 2025",gid,len(rows),flush=True)
        except Exception as exc:
            # No partial score or player results from a failed official gamebook.
            game.clear();game.update(snapshot)
            global_keys.clear();global_keys.update(snapshot_keys)
            pending.append({"game_id":gid,"source_url":url,"reason":str(exc)})
            print("REVIEW 2025",gid,str(exc),flush=True)
    assert len(games)==444 and len({g["id"] for g in games})==444
    assert all(byid[k]==v for k,v in before_2026.items())
    assert all(byid[k]==v for k,v in before_pre2025.items())
    assert [s for s in players if s["game_id"] in before_2026]==before_stats_2026
    assert len(players)==len({(s["game_id"],s["player_id"]) for s in players})
    players.sort(key=lambda r:(r["game_id"],r["team"],r.get("batting_slot",99),
                              r.get("batting_sub_index",99),
                              r.get("pitching_appearance_index",99),r["player_id"]))
    num_2025=sum(g["date"].startswith("2025") and g["verification"]=="official_boxscore_verified" for g in games)
    if verified:
        report["official_player_boxscores_imported"]=sum(g["verification"]=="official_boxscore_verified" for g in games)
        report["official_score_and_inning_lines_matched"]=sum(g["verification"]!="attendance_only" for g in games)
        report["attendance_only_pending_official_verification"]=sum(g["verification"]=="attendance_only" for g in games)
        report["player_stat_rows"]=len(players)
        report["unique_player_ids"]=len({s["player_id"] for s in players})
        report["latest_verified_batch"]="2025 official university scorebooks, reverse-chronological source-gated imports"
        report["2025_backfill"]={"authorized":True,"total_original_games":74,
             "verified_player_gamebooks":num_2025,
             "source_queue_pending_review":len(pending),
             "remaining_attendance_only":74-num_2025}
        report["warning"]="2025 backfill in progress, verified games only. 2026 preserved. Older years and publication not approved."
    audit={"status":"PASS" if not pending else "PARTIAL_REVIEW_REQUIRED",
           "scope":"Only 2025 approved NCAA/four-year games; no 2024, no release",
           "original_attendance_entries":444,
           "verified_2026_unchanged":68,
           "total_2025_attendance":74,"completed_in_this_run":len(verified),
           "verified_2025_total":num_2025,
           "linked_source_games":len(queue["source_queue"]),
           "passed_games":verified,"pending_review":pending}
    if verified:
        write("games.json",games);write("player_stats.json",players)
        write("import_report.json",report)
    write("2025_source_import_audit.json",audit)
    print(json.dumps({"status":audit["status"],"new":len(verified),
                      "2025_verified":num_2025,"pending_review":len(pending)},indent=2),flush=True)

if __name__=="__main__":main()
