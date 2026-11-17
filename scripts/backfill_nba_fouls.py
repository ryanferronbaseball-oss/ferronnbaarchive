#!/usr/bin/env python3
"""Backfill NBA personal fouls (PF) from ESPN without changing other statistics.

Only records matched by ESPN event ID, ESPN athlete ID, team ID, and
pre-existing point/shooting/rebound/assist totals receive a verified PF value.
A missing or conflicting source entry remains unavailable and is audited.
"""
import json
import pathlib
import re
import time
from collections import Counter, defaultdict
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

ROOT = pathlib.Path(__file__).resolve().parents[1]
PLAYERS = ROOT / "data" / "player_boxscores_espn.json"
REPORT = ROOT / "data" / "nba_pf_backfill_report.json"
ESPN = "https://site.api.espn.com/apis/site/v2/sports/basketball/nba/summary?event="

def request_summary(event_id):
    url = ESPN + event_id
    last_error = None
    for attempt in range(3):
        try:
            req = Request(url, headers={
                "User-Agent": "Mozilla/5.0 (compatible; CourtsideArchive/1.0)",
                "Accept": "application/json"
            })
            with urlopen(req, timeout=30) as response:
                return json.load(response)
        except (HTTPError, URLError, TimeoutError, ValueError) as exc:
            last_error = exc
            if attempt < 2:
                time.sleep(2 * (attempt + 1))
    raise RuntimeError(f"ESPN summary not available: {last_error}")

def candidate_athletes(doc):
    for team in (doc.get("boxscore") or {}).get("players") or []:
        team_id = str((team.get("team") or {}).get("id") or "")
        for group in team.get("statistics") or []:
            labels = [str(s).strip().upper() for s in group.get("labels") or []]
            for entry in group.get("athletes") or []:
                athlete = entry.get("athlete") or {}
                ident = athlete.get("id")
                values = entry.get("stats") or []
                if not ident or len(labels) != len(values) or not labels:
                    continue
                yield "espn:" + str(ident), team_id, dict(zip(labels, values))

def parse_pair(text):
    if not re.fullmatch(r"\d+-\d+", str(text).strip()):
        return None
    return tuple(map(int, str(text).strip().split("-")))

def verified_personal_fouls(old, team_id, stats):
    if str(old.get("team_id")) != team_id:
        return None, "team_id_mismatch"
    for key, espn_key in (("pts", "PTS"), ("reb", "REB"), ("ast", "AST")):
        try:
            if int(old[key]) != int(stats[espn_key]):
                return None, key + "_mismatch"
        except (KeyError, TypeError, ValueError):
            return None, key + "_missing"
    for makes, attempts, espn_key in (
        ("fgm", "fga", "FG"), ("fg3m", "fg3a", "3PT"), ("ftm", "fta", "FT")
    ):
        pair = parse_pair(stats.get(espn_key))
        if pair is None or pair != (old.get(makes), old.get(attempts)):
            return None, espn_key + "_mismatch"
    raw = stats.get("PF")
    if raw is None:
        return None, "pf_missing"
    if not re.fullmatch(r"\d+", str(raw).strip()):
        return None, "pf_not_numeric"
    pf = int(raw)
    if not 0 <= pf <= 6:
        return None, "pf_out_of_range"
    if old.get("pf") is not None and old["pf"] != pf:
        return None, "existing_pf_conflict"
    return pf, None

def main():
    original = json.loads(PLAYERS.read_text(encoding="utf-8"))
    if not isinstance(original, list) or not original:
        raise RuntimeError("NBA player archive is empty or invalid")
    by_event = defaultdict(list)
    unique_keys = set()
    for row in original:
        event = str(row.get("espn_event_id") or "")
        athlete = str(row.get("player_id") or "")
        if not event.isdigit() or not athlete.startswith("espn:"):
            raise RuntimeError("Player has no stable ESPN event/athlete ID")
        key = (event, athlete)
        if key in unique_keys:
            raise RuntimeError("Duplicate athlete in one NBA game: " + str(key))
        unique_keys.add(key)
        by_event[event].append(row)

    report = {
        "source": "ESPN NBA summary API; personal-foul (PF) field",
        "records": len(original),
        "events": len(by_event),
        "verified_pf": 0,
        "unavailable_pf": 0,
        "event_results": {}
    }
    for event, rows in sorted(by_event.items()):
        verified = 0
        errors = Counter()
        try:
            doc = request_summary(event)
            matches = {}
            duplicates = set()
            for athlete_id, team_id, stats in candidate_athletes(doc):
                if athlete_id in matches:
                    duplicates.add(athlete_id)
                matches[athlete_id] = (team_id, stats)
            for row in rows:
                athlete_id = str(row["player_id"])
                if athlete_id in duplicates:
                    errors["duplicate_espn_athlete_id"] += 1
                    continue
                candidate = matches.get(athlete_id)
                if candidate is None:
                    errors["athlete_not_in_source"] += 1
                    continue
                pf, problem = verified_personal_fouls(row, *candidate)
                if problem:
                    errors[problem] += 1
                else:
                    row["pf"] = pf
                    verified += 1
        except Exception as exc:
            errors["source_request_failed"] += len(rows)
            errors["source_error: " + str(exc)[:160]] += 1
        report["verified_pf"] += verified
        report["unavailable_pf"] += len(rows) - verified
        report["event_results"][event] = {
            "date": rows[0]["date"],
            "players": len(rows),
            "verified_pf": verified,
            "remaining": len(rows) - verified,
            "issues": dict(errors),
            "source_url": ESPN + event
        }
        print(f"{event} {rows[0]['date']}: {verified}/{len(rows)} PF verified; issues={dict(errors)}")
        time.sleep(0.7)

    if report["verified_pf"] + report["unavailable_pf"] != len(original):
        raise RuntimeError("NBA foul backfill record-count reconciliation failed")
    REPORT.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    if not report["verified_pf"]:
        raise RuntimeError("No verified ESPN fouls retrieved; refusing to modify player data")
    PLAYERS.write_text(json.dumps(original, indent=2) + "\n", encoding="utf-8")
    print(f"VALIDATED {report['verified_pf']}/{len(original)} individual fouls. "
          f"Remaining missing: {report['unavailable_pf']}. Other stat values unchanged.")

if __name__ == "__main__":
    main()
