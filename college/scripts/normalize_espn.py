#!/usr/bin/env python3
"""Transform ESPN college box scores into the NBA site's data contract, with QA.

No player stat is certified until BOTH teams' summed player PTS match final scores.
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
        "source": "ESPN summary API",
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
        certified = (
            bool(player_lines) and counts[away_id] > 0 and counts[home_id] > 0
            and away_total == scores["away"] and home_total == scores["home"]
        )
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
        "games_complete": len(games) - len(incomplete),
        "games_partial": len(incomplete),
        "raw_player_lines": len(players_all),
        "certified_player_lines": len(players_certified),
        "unique_players": len(by_player),
        "multi_school_players": sum(len(tids) > 1 for tids in by_player.values()),
        "incomplete_attendance_ids": [int(r["attendance_id"]) for r in incomplete],
        "safe_to_publish_all_game_leaderboards": not incomplete,
        "policy": "Only both-teams-score-reconciled games appear in certified leaderboard data; incomplete games stay in audit data.",
    }
    (out / "qa_report.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))
    if report["games_identified"] != args.expected_games:
        raise AssertionError("Game count changed")

if __name__ == "__main__":
    main()
