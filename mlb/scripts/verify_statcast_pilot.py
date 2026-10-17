#!/usr/bin/env python3
"""Compare archive's imported Statcast events against Baseball Savant's raw CSV.

Verifies Savant-to-archive integrity, not physical sensor accuracy.
"""
import csv
import io
import json
import math
import sys
from pathlib import Path

import requests

DATA_DIR = Path(__file__).resolve().parents[1] / "data"
SAMPLE_YEARS = (2015, 2018, 2022, 2024, 2026)
CHECK_FIELDS = ("game_pk", "at_bat_number", "pitch_number", "pitcher", "batter",
                "release_speed", "launch_speed", "launch_angle",
                "hit_distance_sc", "events", "description")
NUMERIC_FIELDS = {"release_speed", "launch_speed", "launch_angle", "hit_distance_sc"}
ID_FIELDS = {"game_pk", "at_bat_number", "pitch_number", "pitcher", "batter"}


def normalize(value, field):
    if value is None or str(value).strip().lower() in ("", "nan", "none", "<na>"):
        return None
    if field in ID_FIELDS:
        return int(float(value))
    if field in NUMERIC_FIELDS:
        return float(value)
    return str(value)


def key(row):
    return ":".join(str(normalize(row.get(c), c)) for c in
                    ("game_pk", "at_bat_number", "pitch_number"))


def keyed(rows):
    out, duplicates, skipped = {}, [], 0
    for row in rows:
        if any(normalize(row.get(c), c) is None for c in
               ("game_pk", "at_bat_number", "pitch_number")):
            skipped += 1
            continue
        k = key(row)
        if k in out:
            duplicates.append(k)
        out[k] = row
    return out, duplicates, skipped


def get_savant(pk):
    url = "https://baseballsavant.mlb.com/statcast_search/csv"
    r = requests.get(url, params={"all": "true", "type": "details", "game_pk": pk},
                     headers={"User-Agent": "CourtsideArchiveStatcastVerifier/1.0"},
                     timeout=90)
    r.raise_for_status()
    if "game_pk" not in r.text[:1500]:
        raise ValueError("Savant did not return a recognizable CSV header")
    rows = list(csv.DictReader(io.StringIO(r.text)))
    if not rows or "game_pk" not in rows[0]:
        raise ValueError("Savant returned an empty/non-Statcast CSV")
    return rows


def verify_game(game, pilot):
    pk = int(game["game_pk"])
    report = {"game_pk": pk, "date": game["date"],
              "game": game["away"] + " at " + game["home"],
              "status": "BLOCKED", "mismatches": []}
    source_rows = get_savant(pk)
    imported = [r for r in pilot["events"] if int(r.get("game_pk") or 0) == pk]
    source, source_dupes, source_skipped = keyed(source_rows)
    ours, ours_dupes, ours_skipped = keyed(imported)
    report.update({"source_rows": len(source_rows), "source_usable": len(source),
                   "imported_rows": len(imported),
                   "source_rows_missing_ids": source_skipped,
                   "imported_rows_missing_ids": ours_skipped,
                   "source_duplicates": len(source_dupes),
                   "import_duplicates": len(ours_dupes),
                   "missing_from_import": len(source.keys() - ours.keys()),
                   "not_in_savant": len(ours.keys() - source.keys())})
    bad = []
    for k in source.keys() & ours.keys():
        for field in CHECK_FIELDS:
            a, b = normalize(source[k].get(field), field), normalize(ours[k].get(field), field)
            if field in NUMERIC_FIELDS and a is not None and b is not None:
                equal = math.isclose(a, b, rel_tol=0, abs_tol=0.051)
            else:
                equal = a == b
            if not equal:
                bad.append({"event_id": k, "field": field, "savant": a, "import": b})
    report["field_mismatch_count"] = len(bad)
    report["mismatches"] = bad[:25]
    status = next((r.get("status") for r in pilot["report"]
                   if int(r["game_pk"]) == pk), None)
    report["import_status"] = status
    report["status"] = ("PASS" if not (source_dupes or ours_dupes or
                        source.keys() != ours.keys() or bad or status != "imported")
                        else "FAIL")
    return report


def main():
    pilot = json.loads((DATA_DIR / "statcast_pilot.json").read_text())
    if "events" not in pilot:
        raise ValueError("Pilot JSON lacks pitch events; run updated importer first")
    games = json.loads((DATA_DIR / "games.json").read_text())
    report = []
    for year in SAMPLE_YEARS:
        game = next(g for g in games if g["date"].startswith(str(year)) and g.get("game_pk"))
        try:
            report.append(verify_game(game, pilot))
        except Exception as exc:
            report.append({"game_pk": int(game["game_pk"]), "date": game["date"],
                           "status": "BLOCKED", "error": str(exc)[:300]})
    outcome = {"definition": "Pitch-event identity and field comparison to Savant raw CSV",
               "sample_years": list(SAMPLE_YEARS), "games": report,
               "all_passed": len(report) == len(SAMPLE_YEARS) and
                             all(x["status"] == "PASS" for x in report)}
    out_path = DATA_DIR / "statcast_verification.json"
    out_path.write_text(json.dumps(outcome, indent=2, allow_nan=False) + "\n")
    print(json.dumps(outcome, indent=2, allow_nan=False))
    return 0 if outcome["all_passed"] else 1


if __name__ == "__main__":
    sys.exit(main())
