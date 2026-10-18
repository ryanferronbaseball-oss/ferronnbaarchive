#!/usr/bin/env python3
"""Fail-closed, repeatable historical source-to-site player stat importer.

Strict university gamebook parsing. Keep original 444 attendance identities,
all non-target player stats, and excluded JUCO intact. No release or merge.
"""
import argparse
import json
import re
from collections import Counter
from copy import deepcopy
from datetime import date
from pathlib import Path

import requests
from bs4 import BeautifulSoup
from import_2026_remaining_ncaa import import_one
from import_2024_statcrew import import_statcrew
from import_2024_pdf import parse as parse_pdf
from import_2025_verified_queue import scorer_labels

DATA = Path(__file__).resolve().parents[1] / "data"
YEARS = tuple(range(2017, 2024))
MAX_ORIGINAL = 444


def load(name):
    return json.loads((DATA / name).read_text(encoding="utf-8"))


def dump(name, data):
    (DATA / name).write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def score_pair(raw):
    if isinstance(raw, list) and len(raw) == 2:
        return [int(v) for v in raw]
    if isinstance(raw, str):
        # Older source queue: "Saint Mary's 17, San Diego 8".
        parts = re.findall(r"\b\d+\b", raw)
        if len(parts) == 2:
            return [int(v) for v in parts]
    raise ValueError("Source queue lacks exactly two numeric scores")


def source_entries(year):
    queue = load(f"{year}_official_source_queue.json")
    entries = queue["source_queue"] if year in (2021, 2022, 2023) else queue["rows"]
    if len(entries) != {2017:1, 2018:30, 2019:41, 2020:11, 2021:32, 2022:62, 2023:47}[year]:
        raise ValueError("Source queue size differs from original year")
    results = {}
    for row in entries:
        gid = row["game_id"]
        if gid in results:
            raise ValueError("Duplicate source queue game ID: " + gid)
        results[gid] = row
    return results


def exact_date_in_page(html, expected):
    source = BeautifulSoup(html, "html.parser").get_text(" ", strip=True)
    yr, month, day = map(int, expected.split("-"))
    d = date(yr, month, day)
    variants = {
        f"{month}/{day}/{yr}", f"{month:02d}/{day:02d}/{yr}",
        f"{month}/{day}/{yr%100:02d}", f"{month:02d}/{day:02d}/{yr%100:02d}",
        d.strftime("%b %d, %Y"), d.strftime("%B %d, %Y"),
        d.strftime("%b %d, %Y").replace(" 0", " "),
        d.strftime("%B %d, %Y").replace(" 0", " "),
        d.strftime("%b %d %Y"), d.strftime("%B %d %Y"),
    }
    return any(v in source for v in variants)


def source_url(row):
    return row.get("official_full_gamebook_url") or row.get("source_url")


def resolve(year, game, row):
    if game.get("boxscore_backfill_excluded"):
        raise ValueError("JUCO explicitly excluded")
    # Older research queues use source_workbook_row; the original game file
    # consistently uses source_worksheet_row. Compare values, not field labels.
    source_row = row.get("source_worksheet_row", row.get("source_workbook_row"))
    if source_row is None or source_row != game.get("source_worksheet_row") or (
        game["away"], game["home"]) != (row["away"], row["home"]):
        raise ValueError("Source names or original attendance row differ")
    original = row.get("original_date", row.get("original_attendance_date"))
    if original != game["date"] or game["season"] != year:
        raise ValueError("Original attendance date or season differs")
    if row.get("needs_attendance_confirmation") or row.get("requires_user_date_reconciliation") or row.get("needs_attendance_order_confirmation"):
        raise ValueError("University source identity or doubleheader attendance order needs confirmation")
    if "date_conflict" in row.get("research_status", "") or row.get("source_identity_status") == "official_date_conflicts_with_attendance":
        raise ValueError("Unreconciled date conflict")
    if row.get("official_date") and row["official_date"] != original and not row.get("attendance_identity_user_confirmed"):
        raise ValueError("Official and original dates differ without explicit user confirmation")
    if year == 2018 and row.get("data_evidence_path"):
        # ASU batting data is documented, but its PDF score-by-innings and
        # exact substitution slots have not yet been independently reconciled.
        raise ValueError("2018 ASU screenshot evidence not yet a verified complete inning/lineup gamebook")
    # The source is an official seven-inning TIE (16–16), not a
    # nine-inning game with an invented winner or loser. Narrow exception:
    # original university 2/20/2023 full gamebook R/H/E corroborated.
    is_seven_inning_nebraska_tie = (game["id"] == "cb-2023-02-20-nebraska-san-diego-att0181"
        and row["official_score"] == "Nebraska 16, San Diego 16 (7-inning tie)")
    scores = [16, 16] if is_seven_inning_nebraska_tie else score_pair(row["official_score"])
    if scores[0] == scores[1] and not is_seven_inning_nebraska_tie:
        raise ValueError("Other tied games require separately audited draw import")
    url = source_url(row)
    if not url or not url.startswith("https://"):
        raise ValueError("Official HTTPS full gamebook URL missing")
    return url, scores


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--season", type=int, choices=YEARS, default=2023)
    p.add_argument("--month", type=int, choices=range(2, 7))
    p.add_argument("--limit", type=int, default=0, help="0 means every eligible game")
    args = p.parse_args()

    games = load("games.json")
    players = load("player_stats.json")
    report = load("import_report.json")
    if len(games) != MAX_ORIGINAL or len({g["id"] for g in games}) != MAX_ORIGINAL:
        raise ValueError("Original 444 attendance IDs must remain unique and intact")
    if len({(r["game_id"], r["player_id"]) for r in players}) != len(players):
        raise ValueError("Existing player data already has duplicate game-player identity")
    originals = {g["id"]: deepcopy(g) for g in games}
    orig_player_count = len(players)
    protected_players = deepcopy([r for r in players if not r["game_id"].startswith("cb-" + str(args.season) + "-")])
    queue = source_entries(args.season)
    byid = {g["id"]: g for g in games}
    keys = {(r["game_id"], r["player_id"]) for r in players}

    candidates = [g for g in games if g["season"] == args.season
                  and (args.month is None or int(g["date"][5:7]) == args.month)]
    candidates.sort(key=lambda g: (g["date"], g["source_worksheet_row"]), reverse=True)
    if args.limit:
        candidates = candidates[:args.limit]
    completed, pending, already_verified = [], [], []
    session = requests.Session()
    session.headers["User-Agent"] = "Mozilla/5.0 CourtsideArchive verified university backfill"
    for g in candidates:
        gid = g["id"]
        if g.get("boxscore_backfill_excluded"):
            continue
        row = queue.get(gid)
        if not row:
            pending.append({"game_id":gid,"reason":"No official source entry"})
            continue
        snapshot = deepcopy(g)
        prior_keys = set(keys)
        if g.get("verification") == "official_boxscore_verified":
            known = [v for v in players if v["game_id"] == gid]
            if len(known) < 18 or not g.get("source_url"):
                raise ValueError("Previously imported game has incomplete stats: " + gid)
            already_verified.append(gid)
            continue
        if g.get("verification") not in ("attendance_only", "source_matched"):
            pending.append({"game_id":gid,"reason":"Unexpected prior status: " + str(g.get("verification"))})
            continue
        try:
            url, scores = resolve(args.season, g, row)
            # One original USD 2017 archival gamebook is served on a
            # retired university FTP hostname with a certificate hostname
            # mismatch. For this single exact file, the official USD recap
            # links to the source directly, and the full player/scorebook
            # parser independently checks date, both teams, innings, R/H/E,
            # batting rows, pitching and official W/L/S. No credentials are
            # transmitted; preserve this one-host exception in the audit.
            legacy_2017_source = ("https://usandiego_ftp.sidearmsports.com/"
                "custompages/sports/m-basebl/stats/2016-201736.html")
            if url == legacy_2017_source and g["id"] == "cb-2017-04-20-byu-san-diego-att0001":
                import urllib3
                urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
                source = session.get(url, timeout=50, verify=False)
            else:
                source = session.get(url, timeout=50)
            source.raise_for_status()
            if len(source.content) < 2000:
                raise ValueError("Incomplete official source response")
            if url.lower().split("?")[0].endswith(".pdf"):
                if not source.content.startswith(b"%PDF"):
                    raise ValueError("University PDF download did not yield PDF bytes")
                normalized = {"source_url": url, "official_score": scores,
                              "official_doubleheader_game": row.get("official_doubleheader_game")}
                rows, trace = parse_pdf(g, normalized, keys, source)
                decision = g.get("pitching_decisions")
            else:
                if not exact_date_in_page(source.text, row.get("official_date", row.get("official_game_date", g["date"]))):
                    raise ValueError("Printed full gamebook does not visibly confirm official game date")
                normalized = {"source_url": url, "official_score": scores,
                              "official_doubleheader_game": row.get("official_doubleheader_game")}
                soup = BeautifulSoup(source.text, "html.parser")
                is_legacy = bool(soup.find("pre") and "Score by Innings" in source.text)
                if is_legacy:
                    rows, trace = import_statcrew(g, normalized, keys, source)
                    decision = g.get("pitching_decisions")
                else:
                    rows, trace = import_one(g, normalized, keys)
                    if g.get("official_draw") and gid == "cb-2023-02-20-nebraska-san-diego-att0181":
                        # No pitcher can be credited with Win/Loss/Save in a 16–16 tie.
                        decision = {"win": None, "loss": None, "save": None}
                        if g["pitching_decisions"] != decision:
                            raise ValueError("Tie gamebook unexpectedly lists pitcher decision")
                    else:
                        decision = scorer_labels(source.text, rows, gid)
                        g["pitching_decisions"] = decision
            if g.get("verification") != "official_boxscore_verified" or len(rows) < 18:
                raise ValueError("Incomplete player-gamebook parsing")
            if gid == "cb-2023-02-20-nebraska-san-diego-att0181" and g.get("official_draw"):
                if decision != {"win": None, "loss": None, "save": None} or len(g.get("innings", [])) != 7:
                    raise ValueError("Historical university tie must be 7 innings with no winning/losing pitcher")
            elif not decision or not decision.get("win") or not decision.get("loss"):
                raise ValueError("Official winning and losing pitchers missing")
            if any(k not in g for k in ("innings", "away_score", "home_score")):
                raise ValueError("Official score-by-innings or totals missing")
            if [g["away_score"],g["home_score"]] != scores:
                raise ValueError("Official final score mismatch")
            if any(not any(p["team"] == side and "pitching" in p for p in rows)
                   for side in (g["away"], g["home"])):
                raise ValueError("Missing complete pitching staff")
            if g["date"] != original_date_for(gid, originals):
                raise ValueError("Original attendance date mutated")
            if g["source_worksheet_row"] != originals[gid]["source_worksheet_row"]:
                raise ValueError("Original attendance source row mutated")
            g["game_type"] = row.get("game_type") or g.get("game_type") or "regular_season"
            g["source_import_season"] = args.season
            players.extend(rows)
            completed.append({"game_id":gid,"player_rows":len(rows),"source_url":url,
                              "win":decision["win"],"loss":decision["loss"],
                              "source_audit":trace})
            print("PASS HISTORICAL",gid,len(rows),flush=True)
        except Exception as ex:
            g.clear();g.update(snapshot)
            keys.clear();keys.update(prior_keys)
            pending.append({"game_id":gid,"source_url":source_url(row),"reason":str(ex)[:700]})
            print("REVIEW HISTORICAL",gid,str(ex)[:500],flush=True)

    for gid, prior in originals.items():
        current = byid[gid]
        if gid.startswith("cb-" + str(args.season) + "-"):
            for k in ("id","attendance_id","source_worksheet_row","date","away","home","season"):
                if current[k] != prior[k]:
                    raise ValueError("Original identity was changed: " + gid)
        elif current != prior:
            raise ValueError("Historical importer altered protected year: " + gid)
    if [r for r in players if not r["game_id"].startswith("cb-" + str(args.season) + "-")] != protected_players:
        raise ValueError("Historical importer altered protected player rows")
    if len({(r["game_id"],r["player_id"]) for r in players}) != len(players):
        raise ValueError("Duplicate player-game rows after import")
    if len(players) < orig_player_count:
        raise ValueError("Player rows lost during historical import")
    players.sort(key=lambda r:(r["game_id"],r["team"],r.get("batting_slot",99),
                              r.get("batting_sub_index",99),r.get("pitching_appearance_index",99),
                              r["player_id"]))
    verified = sum(g["verification"] == "official_boxscore_verified" for g in games)
    imported_this_year = sum(g["season"] == args.season and g["verification"] == "official_boxscore_verified" for g in games)
    report["official_player_boxscores_imported"] = verified
    report["player_stat_rows"] = len(players)
    report["unique_player_ids"] = len({r["player_id"] for r in players})
    report["attendance_only_pending_official_verification"] = sum(g["verification"] == "attendance_only" for g in games)
    report["latest_verified_batch"] = f"Historical official gamebooks {args.season} (development branch)"
    y = report.setdefault(f"{args.season}_backfill", {})
    y.update({"approved":True,"player_boxscore_imported":imported_this_year,
              "new_verified_gamebooks_last_run":len(completed),
              "last_run_pending_review":len(pending)})
    if "official_boxscores_player_rows_imported" in y:
        y["official_boxscores_player_rows_imported"] = imported_this_year
    if "stage" in y:
        y["stage"] = "historical_verified_player_stat_backfill_in_progress"
    gate=report.setdefault("monthly_review_gate",{}).setdefault("season_"+str(args.season),{})
    gate["full_player_boxscores_imported"] = imported_this_year
    gate["status"] = "in_progress" if pending or imported_this_year < len(queue) else "verified_complete"
    report["warning"] = ("Verified historical imports are source-gated and provisional on an unpublished development "
                         "branch; unresolved dates, ties, missing scorebooks and partial gamebooks remain pending. "
                         "No JUCO included. No production deployment or merge.")
    audit={"season":args.season, "month":args.month,"limit":args.limit,
           "status":"PASS" if not pending else "PARTIAL_REVIEW_REQUIRED",
           "original_attendance_games":MAX_ORIGINAL,
           "verified_this_run":len(completed),
           "verified_in_season":imported_this_year,
           "verified_overall":verified,
           "player_game_rows_total":len(players),
           "already_verified":already_verified,
           "completed":completed,"pending_review":pending,
           "release":"Draft branch only; never auto-publish or merge"}
    if completed:
        dump("games.json",games)
        dump("player_stats.json",players)
        dump("import_report.json",report)
    dump(f"{args.season}_historical_stat_import_audit.json",audit)
    print(json.dumps({"season":args.season,"new_gamebooks":len(completed),
                       "verified_season":imported_this_year,"pending":len(pending),
                       "player_stat_rows":len(players)},indent=2),flush=True)


def original_date_for(gid, original):
    return original[gid]["date"]


if __name__ == "__main__":
    main()
