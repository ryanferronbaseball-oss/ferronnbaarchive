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
# import_one also applies source-PBP-confirmed unindented defensive substitutions
# for two explicitly user-confirmed corrected-date 2022/2023 gamebooks.
from import_2026_remaining_ncaa import import_one
from import_2024_statcrew import import_statcrew
from import_2024_pdf import parse as parse_pdf
from import_2018_original_pdf_transcripts import parse as parse_2018_uploaded_pdf, SOURCES as UPLOADED_2018_GAMEBOOKS
from import_2018_asu_reconciled import parse as parse_2018_asu, GAME_ID as RECONCILED_ASU_GAME_ID
from import_2025_verified_queue import scorer_labels

DATA = Path(__file__).resolve().parents[1] / "data"
YEARS = tuple(range(2017, 2024))
MAX_ORIGINAL = 444

# Explicit user attestation on 2026-10-17. Keep the immutable original
# worksheet date in its own field, retain the historic attendance ID, and show
# the source-verifiable actual game date on the finished site.
CONFIRMED_DATE_CORRECTIONS = {
    "cb-2022-04-21-grand-canyon-stanford-att0151": ("2022-04-21", "2022-04-22"),
    "cb-2023-02-25-unlv-uc-irvine-att0184": ("2023-02-25", "2023-02-26"),
    "cb-2023-02-25-unlv-san-diego-att0185": ("2023-02-25", "2023-02-26"),
    "cb-2023-02-26-uc-irvine-san-diego-att0186": ("2023-02-26", "2023-02-27"),
}

def verified_user_date_correction(gid, row, original):
    expected = CONFIRMED_DATE_CORRECTIONS.get(gid)
    return bool(expected and expected == (original, row.get("official_date"))
                and row.get("attendance_identity_user_confirmed") is True
                and row.get("attendance_user_confirmation_date") == "2026-10-17")


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
    if row.get("official_date") and row["official_date"] != original and not verified_user_date_correction(game["id"], row, original):
        raise ValueError("Official and original dates differ without matching verified user-confirmed correction")
    if year == 2018 and row.get("data_evidence_path") and not (
        game["id"] == RECONCILED_ASU_GAME_ID
        and row.get("asu_source_reconstruction_confirmed") == "2026-10-18"
        and row.get("source_scoreboard_screenshot_file_id")
            == "file_0000000045a081f5b589dd3a9489b970"):
        # Do not bypass other data-evidence holds: only the exact supplied
        # ASU original inning screenshot and explicit user substitutions.
        raise ValueError("2018 ASU full gamebook source identity and owner reconciliation not verified")
    # The source is an official seven-inning TIE (16–16), not a
    # nine-inning game with an invented winner or loser. Narrow exception:
    # original university 2/20/2023 full gamebook R/H/E corroborated.
    is_seven_inning_nebraska_tie = (game["id"] == "cb-2023-02-20-nebraska-san-diego-att0181"
        and row["official_score"] == "Nebraska 16, San Diego 16 (7-inning tie)")
    scores = [16, 16] if is_seven_inning_nebraska_tie else score_pair(row["official_score"])
    if scores[0] == scores[1] and not is_seven_inning_nebraska_tie:
        raise ValueError("Other tied games require separately audited draw import")
    url = (row.get("official_boxscore_page_url")
           if year == 2018 and game["id"] == RECONCILED_ASU_GAME_ID
           and row.get("asu_source_reconstruction_confirmed") == "2026-10-18"
           else source_url(row))
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
            if args.season == 2018 and gid == RECONCILED_ASU_GAME_ID:
                # Original ASU gamebook's batter SO field is wrong; the
                # archive owner separately reconstructed individual Ks and
                # supplied the exact original score-by-inning source image
                # plus replacement-to-predecessor links for all substitutes.
                # The dedicated parser reconciles every available source
                # column and the exact nine-slot batting orders, fail-closed.
                rows, trace = parse_2018_asu(g, row, keys)
                decision = g.get("pitching_decisions")
            elif args.season == 2018 and gid in UPLOADED_2018_GAMEBOOKS:
                # Only two exact source-verified original USD Automated
                # ScoreBook PDFs supplied by this archive's owner.
                # Their complete, line-preserving transcriptions are
                # committed locally because USD now returns HTML landing
                # pages instead of the original PDF bytes.
                rows, trace = parse_2018_uploaded_pdf(g, row, keys)
                decision = g.get("pitching_decisions")
            else:
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
                        # 2022 NCAA Corvallis Regional: university official
                        # home/away designates Oregon State visiting 12 and
                        # USD home 3 at OSU's own stadium. The original personal
                        # worksheet calls USD "away" and Oregon State "home".
                        # Preserve original worksheet ID and team labels, but
                        # parse the university GAMEBOOK side first, and then
                        # map every official R/H/E and inning field back.
                        reversed_2022_regional = (
                            gid=="cb-2022-06-04-san-diego-oregon-state-att0175"
                            and scores==[3,12]
                            and (g["away"],g["home"])==("San Diego","Oregon State"))
                        if reversed_2022_regional:
                            source_game=deepcopy(g)
                            source_game["away"],source_game["home"] = g["home"],g["away"]
                            normalized["official_score"]=[12,3]
                            rows,trace=import_one(source_game,normalized,keys)
                            if (source_game["away_score"],source_game["home_score"],
                                source_game["away_hits"],source_game["home_hits"],
                                source_game["away_errors"],source_game["home_errors"]) != (12,3,13,7,0,2):
                                raise ValueError("2022 Oregon State official source-side checksum failed")
                            g.update({
                                "source_url":url,"verification":"official_boxscore_verified",
                                "official_boxscore_status":"verified",
                                "score_provenance":"official_boxscore",
                                "away_score":source_game["home_score"],
                                "home_score":source_game["away_score"],
                                "away_hits":source_game["home_hits"],
                                "home_hits":source_game["away_hits"],
                                "away_errors":source_game["home_errors"],
                                "home_errors":source_game["away_errors"],
                                "innings":[{"inning":i["inning"],"away":i["home"],"home":i["away"]}
                                           for i in source_game["innings"]],
                                "source_home_away_side_reversed_for_attendance":True,
                                "source_home_away_note":"University official designated Oregon State as visitor despite Corvallis venue. Original personal worksheet USD-away/OSU-home identity preserved; full source RHE and inning columns mapped explicitly."
                            })
                            trace["original_attendance_team_order"]=["San Diego","Oregon State"]
                            trace["official_university_team_order"]=["Oregon State","San Diego"]
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
            # Only after the full original gamebook (lineups, player totals,
            # pitching decisions and inning line) passes all checks may the
            # official display date differ from the original user's sheet.
            original_date = original_date_for(gid, originals)
            if verified_user_date_correction(gid, row, original_date):
                g["original_worksheet_date"] = original_date
                g["date"] = row["official_date"]
                g["date_correction_user_confirmed"] = "2026-10-17"
                g["date_correction_provenance"] = "Official university gamebook plus explicit user attestation"
                trace["date_correction"] = {
                    "original_worksheet_date": original_date,
                    "verified_official_date": g["date"],
                    "user_confirmed": "2026-10-17",
                }
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
            for k in ("id","attendance_id","source_worksheet_row","away","home","season"):
                if current[k] != prior[k]:
                    raise ValueError("Original identity was changed: " + gid)
            if current["date"] != prior["date"]:
                row = queue.get(gid, {})
                if not (verified_user_date_correction(gid, row, prior["date"])
                        and current["date"] == row["official_date"]
                        and current.get("original_worksheet_date") == prior["date"]
                        and current.get("date_correction_user_confirmed") == "2026-10-17"):
                    raise ValueError("Non-attested change to attendance game date: " + gid)
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
