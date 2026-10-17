#!/usr/bin/env python3
"""Normalize an attended college baseball game list without fabricating box scores.

Usage:
    python college-baseball/scripts/import_attendance.py
    python college-baseball/scripts/import_attendance.py --input my_log.csv --output /tmp/games.json
    python college-baseball/scripts/import_attendance.py --validate-only

Raw scores, if supplied, remain attributed to the user's log until checked against
an official university/NCAA scorebook. This script NEVER invents stats or players.
"""
from __future__ import annotations

import argparse
import csv
import json
import re
import unicodedata
from datetime import datetime
from pathlib import Path
from urllib.parse import urlparse

BASE = Path(__file__).resolve().parents[1]
REQUIRED = ("date", "away", "home")
FIELDS = (
    "attendance_id", "date", "away", "home", "ballpark", "city", "state",
    "neutral_site", "game_number", "game_type", "postseason_round",
    "away_score", "home_score", "source_url", "notes"
)


def parse_date(value: str) -> str:
    for fmt in ("%Y-%m-%d", "%m/%d/%Y", "%m/%d/%y", "%Y/%m/%d", "%b %d, %Y", "%B %d, %Y"):
        try:
            return datetime.strptime(value.strip(), fmt).date().isoformat()
        except ValueError:
            pass
    raise ValueError(f"Invalid game date {value!r}; use YYYY-MM-DD or US MM/DD/YYYY")


def slug(s: str) -> str:
    a = unicodedata.normalize("NFKD", s)
    a = a.encode("ascii", "ignore").decode("ascii").lower()
    return re.sub(r"(^-|-$)", "", re.sub(r"-+", "-", re.sub(r"[^a-z0-9]+", "-", a)))


def optional_int(s: str, name: str) -> int | None:
    if not s.strip():
        return None
    if not re.fullmatch(r"\d+", s.strip()):
        raise ValueError(f"Invalid {name} {s!r}; provide a nonnegative integer or leave blank")
    return int(s)


def optional_bool(s: str) -> bool | None:
    k = s.strip().lower()
    if k in ("", "unknown", "unsure", "?", "n/a"):
        return None
    if k in ("true", "yes", "y", "1", "neutral"):
        return True
    if k in ("false", "no", "n", "0", "home", "away"):
        return False
    raise ValueError(f"Invalid neutral_site value {s!r}; use yes, no or leave blank")


def source_link(s: str) -> str | None:
    if not s:
        return None
    p = urlparse(s)
    if p.scheme not in ("https", "http") or not p.netloc:
        raise ValueError(f"Source URL is not http(s): {s!r}")
    return s


def load_csv(path: Path) -> list[dict]:
    if not path.exists():
        raise FileNotFoundError(f"Attendance CSV not found: {path}")
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        if not reader.fieldnames:
            raise ValueError("File must have a header with date, away, home")
        fields = set(reader.fieldnames)
        missing = set(REQUIRED) - fields
        if missing:
            raise ValueError("Missing required CSV columns: " + ", ".join(sorted(missing)))
        unknown = fields - set(FIELDS)
        if unknown:
            raise ValueError("Unexpected CSV columns: " + ", ".join(sorted(unknown)))
        entries = []
        seen: set[str] = set()
        attendance_ids: set[str] = set()
        for line, data in enumerate(reader, 2):
            if None in data:
                raise ValueError(f"Row {line}: too many cells; check that notes with commas are quoted")
            row = {name: str(data.get(name) or "").strip() for name in FIELDS}
            if not any(row.values()):
                continue
            absent = [key for key in REQUIRED if not row[key]]
            if absent:
                raise ValueError(f"Row {line}: missing {', '.join(absent)}")
            try:
                date = parse_date(row["date"])
                game_no = optional_int(row["game_number"], "game_number")
                if game_no is not None and game_no < 1:
                    raise ValueError("game_number must start at 1")
                away_score = optional_int(row["away_score"], "away_score")
                home_score = optional_int(row["home_score"], "home_score")
                if (away_score is None) != (home_score is None):
                    raise ValueError("away_score and home_score must both be present or both blank")
                neutral = optional_bool(row["neutral_site"])
                url = source_link(row["source_url"])
            except ValueError as exc:
                raise ValueError(f"Row {line}: {exc}") from exc
            away_slug, home_slug = slug(row["away"]), slug(row["home"])
            if not away_slug or not home_slug or away_slug == home_slug:
                raise ValueError(f"Row {line}: teams must be distinct, nonempty names")
            game_id = f"cb-{date}-{away_slug}-{home_slug}" + (f"-g{game_no}" if game_no else "")
            if game_id in seen:
                raise ValueError(f"Row {line}: duplicate game {game_id}. Distinguish doubleheaders using game_number.")
            if row["attendance_id"]:
                if row["attendance_id"] in attendance_ids:
                    raise ValueError(f"Row {line}: duplicate attendance_id {row['attendance_id']}")
                attendance_ids.add(row["attendance_id"])
            seen.add(game_id)
            entries.append({
                "id": game_id,
                "attendance_id": row["attendance_id"] or game_id,
                "date": date,
                "season": int(date[:4]),
                "away": row["away"],
                "home": row["home"],
                "ballpark": row["ballpark"] or None,
                "city": row["city"] or None,
                "state": row["state"] or None,
                "neutral_site": neutral,
                "game_number": game_no,
                "game_type": row["game_type"].lower() or None,
                "postseason_round": row["postseason_round"] or None,
                "away_score": away_score,
                "home_score": home_score,
                "score_provenance": "user_attendance_log" if away_score is not None else None,
                "source_url": url,
                "verification": "attendance_only",
                "official_boxscore_status": "not_imported",
                "notes": row["notes"] or None,
            })
    entries.sort(key=lambda g: (g["date"], g["id"]))
    return entries


def make_report(items: list[dict]) -> dict:
    return {
        "status": "awaiting_attendance_log" if not items else "attendance_imported_official_boxscores_pending",
        "scope": "college baseball only; not MLB, MiLB or other college sports",
        "attendance_games": len(items),
        "official_boxscores_imported": 0,
        "player_stat_rows": 0,
        "scores_supplied_by_user": sum(g["score_provenance"] is not None for g in items),
        "linked_unverified_sources": sum(g["source_url"] is not None for g in items),
        "seasons": sorted(set(g["season"] for g in items)),
        "warning": "Scores from the attendance list are not official verification. Do not infer missing box scores, players, inning totals, or pitch-tracking measurements.",
    }


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--input", type=Path, default=BASE / "data" / "attendance.csv")
    ap.add_argument("--output", type=Path, default=BASE / "data" / "games.json")
    ap.add_argument("--report", type=Path, default=BASE / "data" / "import_report.json")
    ap.add_argument("--validate-only", action="store_true")
    args = ap.parse_args()
    games = load_csv(args.input)
    report = make_report(games)
    print(json.dumps(report, indent=2))
    if not args.validate_only:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(games, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        args.report.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
