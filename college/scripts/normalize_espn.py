#!/usr/bin/env python3
"""Transform ESPN college box scores into the NBA site's data contract, with QA.

No player stat is certified until BOTH teams' PTS and minutes reconcile.
Raw imported games with incomplete rosters stay in audit JSON, not leaderboards.
Never alter data from the live NBA archive.
"""
import argparse
import csv
import json
import re
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
GAME_FIELDS = (
    "id", "date", "away", "home", "arena", "espn_event_id",
    "away_score", "home_score", "away_team_id", "home_team_id", "boxscore_status"
)

def read_csv(path):
    with open(path, encoding="utf-8-sig", newline="") as fh:
        return list(csv.DictReader(fh))

def write_csv(path, columns, rows):
    with open(path, "w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, columns, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)

def int_or_none(value):
    if value is None or str(value).strip() in ("", "-", "--", "DNP"):
        return None
    return int(str(value).strip())

def minutes_number(value):
    """Read team player-minute totals, including MM:SS when ESPN supplies it."""
    if value is None or str(value).strip() in ("", "--", "DNP"):
        return None
    text = str(value).strip()
    if re.fullmatch(r"\d+:\d{2}", text):
        mm, ss = map(int, text.split(":"))
        return mm + ss / 60
    try:
        return float(text)
    except ValueError:
        return None

def split_shot(value):
    if value is None or not re.fullmatch(r"\d+-\d+", str(value)):
        return (None, None)
    made, attempts = map(int, str(value).split("-"))
    if made > attempts:
        raise ValueError("made shots exceed attempts: " + str(value))
    return made, attempts

def normalize_player(item, game, school_name, other_school):
    raw = item["raw_stats"]
    fgm, fga = split_shot(raw.get("fg"))
    fg3m, fg3a = split_shot(raw.get("3pt"))
    ftm, fta = split_shot(raw.get("ft"))
    player = {
        "game_id": str(game["attendance_id"]),
        "espn_event_id": str(game["espn_event_id"]),
        "date": game["date"],
        "player_id": item["player_id"],
        "player": item["player"],
        "team_id": str(item["team_id"]),
        "team": school_name,
        "opponent": other_school,
        "minutes": raw.get("min"),
        "pts": int_or_none(raw.get("pts")),
        "reb": int_or_none(raw.get("reb")),
        "ast": int_or_none(raw.get("ast")),
        "fgm": fgm, "fga": fga, "fg3m": fg3m, "fg3a": fg3a,
        "ftm": ftm, "fta": fta,
        "oreb": int_or_none(raw.get("oreb")),
        "dreb": int_or_none(raw.get("dreb")),
        "stl": int_or_none(raw.get("stl")),
        "blk": int_or_none(raw.get("blk")),
        "tov": int_or_none(raw.get("to")),
        "pf": int_or_none(raw.get("pf")),
        "source": item.get("source_name") or "ESPN summary API",
        "source_url": item.get("source_url") or None,
        "supplemental_official_source": bool(item.get("supplemental_official_source")),
        "official_override_source": bool(item.get("official_override_source")),
    }
    if player["pts"] is not None and None not in (fgm, fg3m, ftm):
        # Field goals include 3-pointers, which add one extra point each.
        computed = 2 * fgm + fg3m + ftm
        if computed != player["pts"]:
            raise ValueError(f"Individual scoring mismatch for {item['player']} event {game['espn_event_id']}: {computed} vs {player['pts']}")
    return player

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--attendance", default=str(ROOT / "data" / "attendance.csv"))
    parser.add_argument("--matches", default=str(ROOT / "output" / "matches.csv"))
    parser.add_argument("--raw", default=str(ROOT / "output" / "player_boxscores_raw.json"))
    parser.add_argument("--supplements", default=str(ROOT / "data" / "official_boxscore_supplements.csv"))
    parser.add_argument("--overrides", default=str(ROOT / "data" / "official_boxscore_overrides.csv"))
    parser.add_argument("--output", default=str(ROOT / "output"))
    parser.add_argument("--expected-games", type=int, default=94)
    args = parser.parse_args()

    out = Path(args.output)
    out.mkdir(parents=True, exist_ok=True)
    attendance = read_csv(args.attendance)
    matches = read_csv(args.matches)
    imported = json.loads(Path(args.raw).read_text(encoding="utf-8"))
    attendance_by_id = {g["attendance_id"]: g for g in attendance}
    match_by_id = {g["attendance_id"]: g for g in matches}
    if len(attendance) != args.expected_games or len(attendance_by_id) != args.expected_games:
        raise ValueError(f"Attendance ID count mismatch: {len(attendance)} rows, {len(attendance_by_id)} IDs")
    if len(matches) != args.expected_games or set(match_by_id) != set(attendance_by_id):
        raise ValueError("Matched-game rows do not cover all attendance IDs exactly once")
    if any(g["match_status"] != "matched" for g in matches):
        raise ValueError("One or more attended games did not match ESPN")
    event_ids = [g["espn_event_id"] for g in matches]
    if len(set(event_ids)) != len(event_ids):
        raise ValueError("Duplicate ESPN event IDs in game matches")

    raw_by_attendance = defaultdict(list)
    id_and_event = set()
    team_name_candidates = defaultdict(Counter)
    for item in imported:
        game_id = str(item["attendance_id"])
        if game_id not in attendance_by_id:
            raise ValueError("Unknown attendance ID in player row: " + game_id)
        if str(item["event_id"]) != match_by_id[game_id]["espn_event_id"]:
            raise ValueError("Event ID conflicts with matched game " + game_id)
        key = (game_id, item["player_id"])
        if key in id_and_event:
            raise ValueError("Duplicate player-game occurrence: " + str(key))
        id_and_event.add(key)
        raw_by_attendance[game_id].append(item)
        team_name_candidates[str(item["team_id"])][item["team"]] += 1


    # A recorded ESPN line can contain incorrect minutes/steals/blocks/etc.
    # Record both sides of each override for forensic review. Exact IDs and
    # game IDs are required; we never overwrite the original import artifact.
    overrides = read_csv(args.overrides) if Path(args.overrides).exists() else []
    override_audit = []
    correction_keys = set()
    for correction in overrides:
        gid = correction["attendance_id"]
        game = match_by_id.get(gid)
        if not game or correction["espn_event_id"] != game["espn_event_id"]:
            raise ValueError("Override not linked to confirmed attendance and ESPN event")
        key = (gid, correction["player_id"])
        if key in correction_keys:
            raise ValueError("Duplicate official override for player game " + str(key))
        correction_keys.add(key)
        if not re.fullmatch(r"espn:\d+", correction["player_id"]):
            raise ValueError("Override must reference an existing ESPN player ID")
        if correction["team_id"] not in (game["away_team_id"], game["home_team_id"]):
            raise ValueError("Override team ID does not match event")
        if not correction["source_url"].startswith("https://") or not correction["source_name"]:
            raise ValueError("Official override missing public source")
        original = [p for p in raw_by_attendance[gid]
                    if p["player_id"] == correction["player_id"]]
        if len(original) != 1 or original[0]["team_id"] != correction["team_id"]:
            raise ValueError("Override must match exactly one ESPN player appearance")
        if original[0]["player"] != correction["player"]:
            raise ValueError("Override name mismatch: " + correction["player"])
        before = original[0]["raw_stats"]
        after = {k: correction[k] for k in (
            "min", "pts", "fg", "3pt", "ft", "reb", "ast", "to",
            "stl", "blk", "oreb", "dreb", "pf"
        )}
        override_audit.append({
            "attendance_id": gid, "espn_event_id": game["espn_event_id"],
            "player_id": correction["player_id"], "player": correction["player"],
            "original_espn_raw_stats": before, "official_corrected_stats": after,
            "source_name": correction["source_name"],
            "source_url": correction["source_url"],
        })
        original[0]["raw_stats"] = after
        original[0]["source_name"] = correction["source_name"]
        original[0]["source_url"] = correction["source_url"]
        original[0]["official_override_source"] = True

    # The ESPN feed occasionally omits an entire player who appears in the
    # official school box score. Supplements are append-only, attributable
    # corrections, never destructive changes to the ESPN source data.
    supplements = read_csv(args.supplements) if Path(args.supplements).exists() else []
    for row in supplements:
        game_id = str(row["attendance_id"])
        if game_id not in match_by_id:
            raise ValueError("Unknown supplemented attendance ID: " + game_id)
        game = match_by_id[game_id]
        if row["espn_event_id"] != game["espn_event_id"]:
            raise ValueError("Supplement ESPN event ID mismatch for attendance " + game_id)
        if not re.fullmatch(r"(?:espn:\d+|official:[a-z0-9-]+:[a-z0-9-]+)", row["player_id"]):
            raise ValueError("Supplement requires a stable provider-qualified athlete ID")
        if row["team_id"] not in (game["away_team_id"], game["home_team_id"]):
            raise ValueError("Supplement team ID mismatches game for attendance " + game_id)
        if not row["source_url"].startswith("https://") or not row["source_name"]:
            raise ValueError("Supplement must cite an official source for attendance " + game_id)
        key = (game_id, row["player_id"])
        if key in id_and_event:
            raise ValueError("Supplement duplicates an imported player-game: " + str(key))
        id_and_event.add(key)
        stats = {k: row[k] for k in (
            "min", "pts", "fg", "3pt", "ft", "reb", "ast", "to",
            "stl", "blk", "oreb", "dreb", "pf"
        )}
        school = game["away"] if row["team_id"] == game["away_team_id"] else game["home"]
        raw_by_attendance[game_id].append({
            "attendance_id": game_id, "event_id": row["espn_event_id"],
            "player_id": row["player_id"], "player": row["player"],
            "team_id": row["team_id"], "team": school,
            "raw_stats": stats,
            "source_name": row["source_name"],
            "source_url": row["source_url"],
            "supplemental_official_source": True,
        })
        team_name_candidates[row["team_id"]][school] += 1

    (out / "official_override_audit.json").write_text(
        json.dumps(override_audit, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8")

    players_all, players_certified, qa_rows, games = [], [], [], []
    for record in attendance:
        gid = record["attendance_id"]
        match = match_by_id[gid]
        if any(match[k] != record[k] for k in ("date", "away", "home")):
            raise ValueError("Date or school mismatch in attended game " + gid)
        away_id, home_id = str(match.get("away_team_id") or ""), str(match.get("home_team_id") or "")
        if not away_id or not home_id or away_id == home_id:
            raise ValueError("Missing or ambiguous ESPN team ID for game " + gid)
        scores = {"away": int_or_none(match["away_score"]), "home": int_or_none(match["home_score"])}
        if scores["away"] is None or scores["home"] is None:
            raise ValueError("Missing final team score for game " + gid)

        player_lines = []
        for item in raw_by_attendance[gid]:
            tid = str(item["team_id"])
            if tid == away_id:
                school, opponent = match["away"], match["home"]
            elif tid == home_id:
                school, opponent = match["home"], match["away"]
            else:
                raise ValueError(f"Unrecognized player team {tid} in attendance ID {gid}")
            player_lines.append(normalize_player(item, match, school, opponent))
        totals = Counter()
        counts = Counter()
        for player in player_lines:
            totals[player["team_id"]] += player["pts"] or 0
            counts[player["team_id"]] += 1
        away_total, home_total = totals[away_id], totals[home_id]
        scoring_consistent = (
            bool(player_lines) and counts[away_id] > 0 and counts[home_id] > 0
            and away_total == scores["away"] and home_total == scores["home"]
        )
        team_minutes = {}
        all_minutes_known = True
        for team_id in (away_id, home_id):
            vals = [minutes_number(p["minutes"]) for p in player_lines if p["team_id"] == team_id]
            if not vals or any(v is None for v in vals):
                all_minutes_known = False
            team_minutes[team_id] = sum(v or 0 for v in vals)
        # NCAA regulation = 200 player minutes per team (five on court x 40).
        # Each five-minute overtime adds 25 player minutes to each team.
        valid_minute_totals = {200 + 25 * n for n in range(8)}
        minutes_consistent = (
            all_minutes_known and
            any(abs(team_minutes[away_id] - n) <= .1 and
                abs(team_minutes[home_id] - n) <= .1 for n in valid_minute_totals)
        )
        certified = scoring_consistent and minutes_consistent
        status = "complete" if certified else "partial"
        for p in player_lines:
            p["boxscore_complete"] = certified
        players_all.extend(player_lines)
        if certified:
            players_certified.extend(player_lines)
        venue = match.get("arena") or ""
        games.append({
            "id": gid, "date": match["date"], "away": match["away"], "home": match["home"],
            "arena": venue, "espn_event_id": match["espn_event_id"],
            "away_score": scores["away"], "home_score": scores["home"],
            "away_team_id": away_id, "home_team_id": home_id,
            "boxscore_status": status,
        })
        qa_rows.append({
            "attendance_id": gid, "date": match["date"], "away": match["away"], "home": match["home"],
            "espn_event_id": match["espn_event_id"],
            "away_score": scores["away"], "away_player_points": away_total,
            "away_points_missing": scores["away"] - away_total,
            "home_score": scores["home"], "home_player_points": home_total,
            "home_points_missing": scores["home"] - home_total,
            "away_player_lines": counts[away_id], "home_player_lines": counts[home_id],
            "away_player_minutes": round(team_minutes[away_id], 2),
            "home_player_minutes": round(team_minutes[home_id], 2),
            "points_reconciled": scoring_consistent,
            "minutes_reconciled": minutes_consistent,
            "official_supplement_lines": sum(bool(p["supplemental_official_source"]) for p in player_lines),
            "boxscore_status": status,
        })

    teams = {
        tid: {"id": tid, "name": names.most_common(1)[0][0]}
        for tid, names in team_name_candidates.items()
    }
    # Keep every source appearance for auditing and backfill.
    (out / "site_players_all_audit.json").write_text(
        json.dumps(players_all, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    # The public-facing data contract intentionally excludes incomplete games.
    (out / "site_players_certified.json").write_text(
        json.dumps(players_certified, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    (out / "site_teams.json").write_text(
        json.dumps(teams, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    write_csv(out / "site_games.csv", GAME_FIELDS, games)
    write_csv(out / "qa_reconciliation.csv", list(qa_rows[0]), qa_rows)
    incomplete = [r for r in qa_rows if r["boxscore_status"] == "partial"]
    by_player = defaultdict(set)
    for player in players_all:
        by_player[player["player_id"]].add(player["team_id"])
    report = {
        "games_identified": len(games),
        "games_points_reconciled": sum(r["points_reconciled"] for r in qa_rows),
        "games_minutes_reconciled": sum(r["minutes_reconciled"] for r in qa_rows),
        "minute_audit_attendance_ids": [int(r["attendance_id"]) for r in qa_rows
            if r["points_reconciled"] and not r["minutes_reconciled"]],
        "games_complete": len(games) - len(incomplete),
        "games_partial": len(incomplete),
        "raw_player_lines": len(imported),
        "official_supplement_lines": len(supplements),
        "official_corrected_existing_lines": len(overrides),
        "provisional_official_athlete_ids": sorted({p["player_id"] for p in players_all if p["player_id"].startswith("official:")}),
        "combined_player_lines": len(players_all),
        "certified_player_lines": len(players_certified),
        "unique_players": len(by_player),
        "multi_school_players": sum(len(tids) > 1 for tids in by_player.values()),
        "incomplete_attendance_ids": [int(r["attendance_id"]) for r in incomplete],
        "safe_to_publish_all_game_leaderboards": not incomplete,
        "policy": "Only games matching both official final scores and expected NCAA team minutes enter certified leaderboards; raw and sourced records remain auditable.",
    }
    (out / "qa_report.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))
    if report["games_identified"] != args.expected_games:
        raise AssertionError("Game count changed")

if __name__ == "__main__":
    main()
