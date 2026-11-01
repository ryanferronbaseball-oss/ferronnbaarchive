#!/usr/bin/env python3
"""Import six additional MLB honors and team-retired uniform numbers.

All recipients come from official MLB StatsAPI award histories, matched by
MLB person ID to players in the archive's attended game box scores. The
existing career_awards.json is intentionally left unchanged.
"""
import concurrent.futures
import datetime
import json
from pathlib import Path
import re
import time
import urllib.request


ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
STATS = json.loads((DATA / "player_stats.json").read_text(encoding="utf-8"))
PLAYERS = {str(row["player_id"]): row.get("name", "") for row in STATS if row.get("player_id") is not None}
AWARDS_URL = "https://statsapi.mlb.com/api/v1/awards"

# Only major-league honors; exclude club, Minor League and Players Choice awards.
CATEGORIES = {
    "ALROY": ("rookie_of_year", "AL", None),
    "NLROY": ("rookie_of_year", "NL", None),
    "MLBROY": ("rookie_of_year", "MLB", None),  # Combined pre-league award.
    "MLBAFIRST": ("all_mlb", None, "First Team"),
    "MLBSECOND": ("all_mlb", None, "Second Team"),
    "WSMVP": ("world_series_mvp", None, None),
    "ALCSMVP": ("lcs_mvp", "AL", None),
    "NLCSMVP": ("lcs_mvp", "NL", None),
    "ALHAA": ("hank_aaron", "AL", None),
    "NLHAA": ("hank_aaron", "NL", None),
    "ALPG": ("platinum_glove", "AL", None),
    "NLPG": ("platinum_glove", "NL", None),
}

TEAM_NAMES = {
    108: "Los Angeles Angels", 109: "Arizona Diamondbacks", 110: "Baltimore Orioles",
    111: "Boston Red Sox", 112: "Chicago Cubs", 113: "Cincinnati Reds",
    114: "Cleveland Guardians", 115: "Colorado Rockies", 116: "Detroit Tigers",
    117: "Houston Astros", 118: "Kansas City Royals", 119: "Los Angeles Dodgers",
    120: "Washington Nationals", 121: "New York Mets", 133: "Athletics",
    134: "Pittsburgh Pirates", 135: "San Diego Padres", 136: "Seattle Mariners",
    137: "San Francisco Giants", 138: "St. Louis Cardinals", 139: "Tampa Bay Rays",
    140: "Texas Rangers", 141: "Toronto Blue Jays", 142: "Minnesota Twins",
    143: "Philadelphia Phillies", 144: "Atlanta Braves", 145: "Chicago White Sox",
    146: "Miami Marlins", 147: "New York Yankees", 158: "Milwaukee Brewers",
}


def team_name(team_id, year):
    if team_id == 114 and year < 2022:
        return "Cleveland Indians"
    if team_id == 120 and year < 2005:
        return "Montreal Expos"
    if team_id == 133 and year <= 2024:
        return "Oakland Athletics"
    if team_id == 139 and year < 2008:
        return "Tampa Bay Devil Rays"
    if team_id == 146 and year < 2012:
        return "Florida Marlins"
    return TEAM_NAMES.get(team_id)


def get_json(url):
    for attempt in range(3):
        try:
            request = urllib.request.Request(url, headers={
                "Accept": "application/json",
                "User-Agent": "CourtsideArchive/1.0 (personal statistics archive)",
            })
            with urllib.request.urlopen(request, timeout=50) as response:
                return json.load(response)
        except Exception:
            if attempt == 2:
                raise
            time.sleep(attempt + 1)


def fetch_recipients(award_id):
    result = get_json(f"{AWARDS_URL}/{award_id}/recipients")
    if not isinstance(result.get("awards"), list):
        raise ValueError(f"Missing award records for {award_id}")
    return award_id, result["awards"]


def main():
    available = get_json(AWARDS_URL)["awards"]
    retired_ids = sorted(a["id"] for a in available
                         if re.fullmatch(r"RETIREDUNI_\d+", a.get("id", ""))
                         and int(a["id"].split("_")[1]) in TEAM_NAMES)
    assert len(retired_ids) == 30, f"Expected 30 team retired-number histories, got {retired_ids}"

    keys = {item[0] for item in CATEGORIES.values()} | {"retired_number"}
    by_player = {pid: {"name": name, **{key: [] for key in keys}}
                 for pid, name in PLAYERS.items()}
    source_counts = {}
    max_year = datetime.date.today().year
    with concurrent.futures.ThreadPoolExecutor(max_workers=6) as executor:
        for award_id, recipients in executor.map(fetch_recipients, [*CATEGORIES, *retired_ids]):
            matched = 0
            for award in recipients:
                pid = str((award.get("player") or {}).get("id", ""))
                if pid not in by_player:
                    continue
                try:
                    year = int(award.get("season") or str(award.get("date", ""))[:4])
                except (ValueError, TypeError):
                    continue
                if award_id in retired_ids and re.match(r"^\d{4}-\d{2}-\d{2}$", str(award.get("date", ""))):
                    # Actual ceremony date takes precedence if an originally
                    # scheduled retirement was delayed (e.g. Walker in 2021).
                    year = int(award["date"][:4])
                if not 1900 <= year <= max_year:
                    continue

                team_id = (award.get("team") or {}).get("id")
                team = team_name(team_id, year)
                if award_id in CATEGORIES:
                    key, league, level = CATEGORIES[award_id]
                    entry = {"year": year}
                    if league:
                        entry["league"] = league
                    if level:
                        entry["level"] = level
                    if team:
                        entry["team"] = team
                    if award.get("notes"):
                        entry["notes"] = str(award["notes"])
                else:
                    key = "retired_number"
                    # Uniform number is the ceremony's official notes field.
                    number = str(award.get("notes") or "").strip()
                    if not number or not team:
                        continue
                    entry = {"year": year, "team": team, "number": number}
                    if award.get("date"):
                        entry["date"] = award["date"]

                if entry not in by_player[pid][key]:
                    by_player[pid][key].append(entry)
                matched += 1
            source_counts[award_id] = {"recipient_records": len(recipients), "matched_records": matched}

    retained = {}
    for pid, row in by_player.items():
        for key in keys:
            row[key].sort(key=lambda x: (x["year"], x.get("team", ""), x.get("level", "")))
        if any(row[key] for key in keys):
            retained[pid] = row

    counts = {key: sum(bool(row[key]) for row in retained.values()) for key in sorted(keys)}
    assert len(PLAYERS) >= 1000
    assert counts["rookie_of_year"] >= 25, counts
    assert counts["all_mlb"] >= 25, counts
    assert counts["world_series_mvp"] >= 5, counts
    assert counts["retired_number"] >= 10, counts
    output = {
        "_meta": {
            "source": "Official MLB StatsAPI award recipients and team uniform retirements",
            "source_url": AWARDS_URL,
            "career_scope": "Official honors earned at any career point, not limited to witnessed games",
            "all_mlb_definition": "All-MLB First and Second Team honors, first awarded in 2019",
            "retired_number_definition": "Official team-specific uniform number retirement ceremony; excludes informal numbers out of circulation",
            "player_pool": len(PLAYERS), "honored_players": len(retained),
            "award_recipients": counts, "sources": source_counts,
            "imported_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        },
        "players": retained,
    }
    target = DATA / "extra_career_awards.json"
    target.write_text(json.dumps(output, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print("ADDITIONAL MLB HONORS", json.dumps({"players": len(retained), "counts": counts}))
    print("RETIRED NUMBER EXAMPLES", [(row["name"], row["retired_number"])
                                    for row in retained.values() if row["retired_number"]][:12])


if __name__ == "__main__":
    main()
