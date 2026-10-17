#!/usr/bin/env python3
"""Second isolated Statcast batch: 15 additional attended games across seasons.

The original five-game pilot and production site remain unchanged.
Every imported pitch is compared against Savant's official search CSV.
"""
import json
import sys
from collections import defaultdict

from pybaseball import statcast_single_game

from statcast_pilot import DATA, PILOT_YEARS, FIELDS, clean, metric
from verify_statcast_pilot import verify_game

BATCH_SIZE = 15
MIN_YEAR = 2015


def choose_games(games, offset=0, count=BATCH_SIZE):
    # Retain original pilot identities even if the attendance list is reordered.
    pilot_pks = {
        int(next(g for g in games if g["date"].startswith(str(year))
                 and g.get("game_pk"))["game_pk"])
        for year in PILOT_YEARS
    }
    seasons = defaultdict(list)
    for game in games:
        year = int(game["date"][:4])
        pk = game.get("game_pk")
        if year >= MIN_YEAR and pk and int(pk) not in pilot_pks:
            seasons[year].append(game)
    for group in seasons.values():
        group.sort(key=lambda x: (x["date"], x["attendance_id"]))
    selected = []
    season_years = sorted(seasons)
    # Round-robin coverage of early and modern Statcast seasons.
    for i in range(max(map(len, seasons.values()), default=0)):
        for year in season_years:
            if i < len(seasons[year]):
                selected.append(seasons[year][i])
    return selected[offset:offset + count]


def run(offset=0, count=BATCH_SIZE, label="02"):
    games = json.loads((DATA / "games.json").read_text())
    chosen = choose_games(games, offset=offset, count=count)
    if len(chosen) != count:
        raise RuntimeError(f"Expected {count} games, found {len(chosen)}")
    unique_pk = {int(g["game_pk"]) for g in chosen}
    if len(unique_pk) != len(chosen):
        raise RuntimeError("Duplicate game_pks in selected batch")
    records, imports, audits = [], [], []
    for game in chosen:
        pk = int(game["game_pk"])
        report = {"game_pk": pk, "date": game["date"],
                  "game": game["away"] + " at " + game["home"]}
        try:
            frame = statcast_single_game(pk)
            if frame is None or frame.empty:
                raise ValueError("pybaseball returned no pitch data")
            entries = []
            for r in frame.to_dict("records"):
                if int(clean(r.get("game_pk")) or 0) != pk:
                    continue
                at_bat = clean(r.get("at_bat_number"))
                pitch = clean(r.get("pitch_number"))
                if at_bat is None or pitch is None:
                    raise ValueError("Pitch record is missing at-bat or pitch number")
                entry = {k: clean(r.get(k)) for k in FIELDS}
                entry["event_id"] = f"{pk}:{int(at_bat)}:{int(pitch)}"
                entry["attendance_id"] = game["attendance_id"]
                entries.append(entry)
            keys = [e["event_id"] for e in entries]
            if not entries or len(keys) != len(set(keys)):
                raise ValueError("Empty events or duplicate event IDs")
            records.extend(entries)
            report.update({"status": "imported", "events": len(entries),
                           "exit_velocities": sum(metric(p, "launch_speed") is not None for p in entries),
                           "pitch_velocities": sum(metric(p, "release_speed") is not None for p in entries),
                           "measured_home_runs": sum(p.get("events") == "home_run" and metric(p, "hit_distance_sc") is not None for p in entries)})
        except Exception as exc:
            report.update({"status": "fetch_error", "error": str(exc)[:300]})
        imports.append(report)
        print(f"IMPORT {game['date']} {pk}: {report['status']} ({report.get('events', 0)} events)", flush=True)

    batch = {
        "metadata": {"scope": "second pilot batch", "not_production_ready": True,
                     "batch_size": count,
                     "not_complete_attendance_leaderboards": True},
        "report": imports, "events": records
    }
    (DATA / f"statcast_batch_{label}.json").write_text(json.dumps(batch, indent=2, allow_nan=False) + "\n")

    for game in chosen:
        try:
            result = verify_game(game, batch)
        except Exception as exc:
            result = {"game_pk": int(game["game_pk"]), "date": game["date"],
                      "status": "BLOCKED", "error": str(exc)[:300]}
        audits.append(result)
        print(f"AUDIT {game['date']} {game['game_pk']}: {result['status']}", flush=True)
    all_passed = len(audits) == count and all(x["status"] == "PASS" for x in audits)
    verification = {"batch": label, "all_passed": all_passed,
                    "imported_event_count": len(records), "games": audits}
    (DATA / f"statcast_batch_{label}_verification.json").write_text(
        json.dumps(verification, indent=2, allow_nan=False) + "\n")
    print("Summary: ", json.dumps({"all_passed": all_passed,
          "imported_events": len(records),
          "passed_games": sum(x["status"] == "PASS" for x in audits),
          "failed_games": [x for x in audits if x["status"] != "PASS"]}, indent=2), flush=True)
    return 0 if all_passed else 1


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--offset", type=int, default=0)
    parser.add_argument("--count", type=int, default=BATCH_SIZE)
    parser.add_argument("--label", default="02")
    args = parser.parse_args()
    if args.offset < 0 or not 1 <= args.count <= BATCH_SIZE or not args.label.isdigit():
        parser.error("Require nonnegative offset, count 1-15, and numeric label")
    sys.exit(run(offset=args.offset, count=args.count, label=args.label))
