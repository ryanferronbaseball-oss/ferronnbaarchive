#!/usr/bin/env python3
"""Assemble only source-verified Statcast attendance rows into a staging artifact.

Never changes the published website. Stops on mismatched or missing games/events.
"""
import json
import sys
from collections import Counter
from pathlib import Path

DIR = Path(__file__).resolve().parents[1] / "data"
BATCH_IDS = ("02", "03", "04", "05", "06")
MIN_YEAR = 2015


def load(name):
    return json.loads((DIR / name).read_text())


def number(row, name):
    value = row.get(name)
    if value is None or value == "":
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def main():
    attendance = load("games.json")
    eligible = {int(g["game_pk"]): g for g in attendance
                if g.get("game_pk") and int(g["date"][:4]) >= MIN_YEAR}
    if len(eligible) != sum(1 for g in attendance
                            if g.get("game_pk") and int(g["date"][:4]) >= MIN_YEAR):
        raise ValueError("Duplicate eligible attendance game_pk")
    pilot = load("statcast_pilot.json")
    inputs = [(pilot, load("statcast_verification.json"))]
    for label in BATCH_IDS:
        inputs.append((load(f"statcast_batch_{label}.json"),
                       load(f"statcast_batch_{label}_verification.json")))
    seen_games, rows = {}, {}
    for dataset, audit in inputs:
        if not audit.get("all_passed"):
            raise ValueError("A source audit did not pass")
        validated = {int(r["game_pk"]): r for r in audit["games"]
                     if r.get("status") == "PASS"}
        imported = dataset["report"]
        pks = [int(g["game_pk"]) for g in imported]
        if len(set(pks)) != len(pks) or set(pks) != set(validated):
            raise ValueError("Mismatch between imported and independently audited games")
        for game in imported:
            pk = int(game["game_pk"])
            if pk not in eligible or pk in seen_games or game["status"] != "imported":
                raise ValueError(f"Unexpected, duplicate or failed attendance game: {pk}")
            if int(game["events"]) != int(validated[pk]["source_rows"]):
                raise ValueError(f"Event count not equal to source CSV: {pk}")
            seen_games[pk] = {**game, "source_verified": True}
        for event in dataset["events"]:
            event_id = event["event_id"]
            pk = int(event["game_pk"])
            if pk not in validated or event_id in rows:
                raise ValueError(f"Duplicate or unverified event: {event_id}")
            expected_id = f"{pk}:{int(event['at_bat_number'])}:{int(event['pitch_number'])}"
            if event_id != expected_id:
                raise ValueError(f"Corrupt event key: {event_id}")
            rows[event_id] = event
    if set(seen_games) != set(eligible):
        missing = sorted(set(eligible) - set(seen_games))
        unexpected = sorted(set(seen_games) - set(eligible))
        raise ValueError(f"Game coverage mismatch: missing={missing}, unexpected={unexpected}")
    total_expected = sum(int(g["events"]) for g in seen_games.values())
    if len(rows) != total_expected:
        raise ValueError(f"Pitch rows: actual={len(rows)}, expected={total_expected}")
    # Each pitch stays distinct. Do not collapse repeated achievements by player.
    records = sorted(rows.values(), key=lambda x: (x["game_date"], int(x["game_pk"]),
                     int(x["at_bat_number"]), int(x["pitch_number"])))
    biggest = lambda field, pred=lambda x: True: sorted(
        (x for x in records if pred(x) and number(x, field) is not None),
        key=lambda x: number(x, field), reverse=True)
    leaders = {
        "fastest_pitches": biggest("release_speed")[:100],
        "hardest_hit_balls": biggest("launch_speed")[:100],
        "longest_home_runs": biggest("hit_distance_sc", lambda x: x.get("events") == "home_run")[:100]
    }
    seasons = Counter(g["date"][:4] for g in seen_games.values())
    manifest = {
        "status": "PASS", "scope": "attended 2015+ MLB games only",
        "games_source_verified": len(seen_games),
        "total_attended_games_in_log": len(attendance),
        "imported_pitch_events": len(records),
        "years": dict(sorted(seasons.items())),
        "unique_pitch_events": True,
        "source_checks": "Savant CSV game/at-bat/pitch identities and 11 event fields",
        "excluded_older_years": "Before 2015, modern Statcast is not available",
        "production_published": False
    }
    out = {"metadata": manifest, "games": sorted(seen_games.values(),
           key=lambda g: (g["date"], g["game_pk"])), "events": records,
           "leaders": leaders}
    (DIR / "statcast_attendance_2015plus.json").write_text(
        json.dumps(out, separators=(",", ":"), allow_nan=False) + "\n")
    (DIR / "statcast_attendance_manifest.json").write_text(
        json.dumps(manifest, indent=2, allow_nan=False) + "\n")
    print(json.dumps(manifest, indent=2), flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
