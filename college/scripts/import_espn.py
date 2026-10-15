#!/usr/bin/env python3
"""Courtside College — conservative ESPN historical importer.

Only attended-game rows from college/data/attendance.csv are searched.
No game is marked matched unless date and BOTH school identities agree.
Usage: python college/scripts/import_espn.py --limit 10
       python college/scripts/import_espn.py --limit 94 --fetch-boxscores
Output: college/output/matches.csv, player_boxscores.json, summary.json
No third-party dependencies. Does not modify the NBA archive.
"""
import argparse
import csv
import json
import re
import time
from collections import Counter
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[1]
BASE = "https://site.api.espn.com/apis/site/v2/sports/basketball/mens-college-basketball"
ALIASES = {
    "byu": "brigham young", "brigham young university": "brigham young",
    "unc": "north carolina", "north carolina tar heels": "north carolina",
    "nc state": "north carolina state", "n c state": "north carolina state",
    "north carolina st": "north carolina state",
    "san diego st": "san diego state", "sdsu": "san diego state",
    "ucsd": "uc san diego", "uc irvine anteaters": "uc irvine",
    "st marys": "saint marys", "saint marys": "saint marys",
    "unc wilmington": "unc wilmington", "uncw": "unc wilmington",
    "college of charleston": "charleston", "charleston cougars": "charleston",
    "cal state northridge": "cal state northridge", "csun": "cal state northridge",
    "cs northridge": "cal state northridge", "cal st northridge": "cal state northridge",
    "cal state fullerton": "cal state fullerton", "cs fullerton": "cal state fullerton",
    "cal st fullerton": "cal state fullerton",
    "ut arlington": "texas arlington", "texas arlington": "texas arlington",
    "little rock": "little rock", "arkansas little rock": "little rock",
    "florida gulf coast": "florida gulf coast", "fgcu": "florida gulf coast",
    "miami fl": "miami", "miami hurricanes": "miami",
    "california golden bears": "california", "cal": "california",
    "grambling state": "grambling", "unc asheville": "unc asheville",
    "saint marys gaels": "saint marys",
}
def canonical(name):
    x = re.sub(r"[^a-z0-9]+", " ", (name or "").lower()).strip()
    x = re.sub(r"\b(university|college)\b", "", x).strip() if x not in ("college of charleston", "san diego christian", "college of charleston") else x
    return ALIASES.get(x, x)

def get_json(path, params):
    url = BASE + path + "?" + urlencode(params)
    for attempt in range(3):
        try:
            req = Request(url, headers={"User-Agent": "CourtsideCollegeArchive/0.1 (historical personal archive)", "Accept": "application/json"})
            with urlopen(req, timeout=25) as response:
                return json.loads(response.read().decode("utf-8"))
        except (HTTPError, URLError, TimeoutError, json.JSONDecodeError):
            if attempt == 2:
                raise
            time.sleep(1.5 * (attempt + 1))

def team_labels(comp):
    t = comp.get("team", {})
    return {canonical(x) for x in (t.get("displayName"), t.get("shortDisplayName"), t.get("name"), t.get("abbreviation")) if x}

def match_event(event, row):
    comps = ((event.get("competitions") or [{}])[0]).get("competitors") or []
    if len(comps) != 2:
        return False
    left, right = canonical(row["away"]), canonical(row["home"])
    # Both schools must match a distinct competitor. Home/away designation
    # may be arbitrary for neutral-site games, so do not depend on ordering.
    return (left in team_labels(comps[0]) and right in team_labels(comps[1])) or (left in team_labels(comps[1]) and right in team_labels(comps[0]))

def parse_scoreboard(data, date):
    # ESPN dates use UTC kickoff timestamps: west-coast late games may land
    # on the following UTC day. Trust the requested scoreboard date window.
    return data.get("events", [])

def extract_boxscore(summary, row, event_id):
    box = summary.get("boxscore") or {}
    lines, warnings = [], []
    for team in box.get("players") or []:
        t = team.get("team") or {}
        team_id = t.get("id")
        team_name = t.get("displayName") or t.get("shortDisplayName")
        for group in team.get("statistics") or []:
            names = group.get("names") or []
            labels = group.get("labels") or []
            for athlete in group.get("athletes") or []:
                a = athlete.get("athlete") or {}
                values = athlete.get("stats") or []
                if not values or not a.get("id"):
                    continue
                stats = {}
                for i, value in enumerate(values):
                    key = str(names[i] if i < len(names) else labels[i] if i < len(labels) else i).lower()
                    stats[key] = value
                lines.append({
                    "attendance_id": int(row["attendance_id"]),
                    "event_id": str(event_id),
                    "date": row["date"],
                    "player_id": "espn:" + str(a["id"]),
                    "player": a.get("displayName") or a.get("fullName"),
                    "team_id": str(team_id) if team_id is not None else None,
                    "team": team_name,
                    "source": "ESPN",
                    "raw_stats": stats,
                    "raw_values": values,
                    "source_stat_labels": names or labels,
                })
    if not lines:
        warnings.append("ESPN summary contains no usable player lines")
    return lines, warnings

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", default=str(ROOT / "data" / "attendance.csv"))
    ap.add_argument("--output", default=str(ROOT / "output"))
    ap.add_argument("--limit", type=int, default=10)
    ap.add_argument("--fetch-boxscores", action="store_true")
    ap.add_argument("--ids", default="", help="Comma-separated attendance IDs to test")
    args = ap.parse_args()
    out = Path(args.output)
    out.mkdir(parents=True, exist_ok=True)
    with open(args.input, newline="", encoding="utf-8-sig") as handle:
        rows = list(csv.DictReader(handle))
    if args.ids:
        selected = {x.strip() for x in args.ids.split(",")}
        rows = [r for r in rows if r["attendance_id"] in selected]
    elif args.limit > 0:
        rows = rows[:args.limit]
    date_cache = {}
    report, player_lines = [], []
    for row in rows:
        date = row["date"]
        result = {
            "attendance_id": row["attendance_id"],
            "date": date, "away": row["away"], "home": row["home"],
            "match_status": "pending", "espn_event_id": "",
            "away_score": "", "home_score": "", "boxscore_status": "not_requested",
            "player_lines": 0, "review_notes": ""
        }
        try:
            if date not in date_cache:
                date_cache[date] = parse_scoreboard(
                    get_json("/scoreboard", {"dates": date.replace("-", ""), "limit": 500}), date)
            candidates = [e for e in date_cache[date] if match_event(e, row)]
            if len(candidates) != 1:
                result["match_status"] = "unmatched" if not candidates else "review"
                result["review_notes"] = f"{len(candidates)} exact team matches found among {len(date_cache[date])} ESPN events"
            else:
                event = candidates[0]
                result["match_status"] = "matched"
                result["espn_event_id"] = str(event["id"])
                competitors = (event["competitions"][0]).get("competitors") or []
                for comp in competitors:
                    label = "away" if canonical(row["away"]) in team_labels(comp) else "home"
                    result[label+"_score"] = comp.get("score") or ""
                if args.fetch_boxscores:
                    summary = get_json("/summary", {"event": event["id"]})
                    lines, warnings = extract_boxscore(summary, row, event["id"])
                    player_lines.extend(lines)
                    result["player_lines"] = len(lines)
                    result["boxscore_status"] = "raw_imported" if lines else "missing"
                    result["review_notes"] = "; ".join(warnings)
        except Exception as exc:
            result["match_status"] = "error"
            result["review_notes"] = type(exc).__name__ + ": " + str(exc)[:180]
        report.append(result)
        print(f"{row['attendance_id']:>3} {date} {row['away']} @ {row['home']}: {result['match_status']} {result['espn_event_id']} ({result['player_lines']} lines)", flush=True)
        time.sleep(0.15)
    with (out/"matches.csv").open("w", newline="", encoding="utf-8") as handle:
        w = csv.DictWriter(handle, fieldnames=list(report[0]) if report else [
            "attendance_id", "date", "away", "home", "match_status", "espn_event_id",
            "away_score", "home_score", "boxscore_status", "player_lines", "review_notes"])
        w.writeheader()
        w.writerows(report)
    (out/"player_boxscores_raw.json").write_text(json.dumps(player_lines, indent=2, ensure_ascii=False), encoding="utf-8")
    counts = dict(Counter(x["match_status"] for x in report))
    summary = {"games_checked": len(rows), "match_counts": counts, "player_lines_raw": len(player_lines),
               "method": "exact date + two distinct normalized schools; no fuzzy auto-accept",
               "warning": "raw boxscores not yet normalized or scoring-validated; do not publish on leaderboards"}
    (out/"summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(json.dumps(summary, indent=2))
if __name__ == "__main__":
    main()
