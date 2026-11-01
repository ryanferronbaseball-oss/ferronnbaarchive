#!/usr/bin/env python3
"""Import official NBA award and retired-number histories for witnessed players.

The output is a reviewed, static career-honors snapshot; no NBA site traffic is
needed when a visitor opens a Courtside Archive player profile. Uses lxml.
"""

import json
import re
import time
import unicodedata
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from urllib.request import Request, urlopen

from lxml import html

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "data/player_boxscores_espn.json"
OUTPUT = ROOT / "data/nba_legacy_honors.json"

AWARD_URLS = {
    "finals_mvp": "https://www.nba.com/news/history-finals-mvp-winners",
    "dpoy": "https://www.nba.com/news/history-defensive-player-of-the-year-winners",
    "rookie": "https://www.nba.com/news/history-rookie-of-the-year-winners",
    "sixth": "https://www.nba.com/news/history-sixth-man-of-the-year-winners",
    "improved": "https://www.nba.com/news/history-most-improved-award-winners",
    "all_defensive": "https://www.nba.com/news/history-all-defensive-team",
}
NBA75_URL = "https://pr.nba.com/nba-75th-anniversary-team-announced/"

# Two official team pages have not incorporated these completed ceremonies in
# their retired-number tables. Both are confirmed in NBA franchise news.
RETIRED_NUMBER_SUPPLEMENTS = {
    "Shaquille O'Neal": [
        {"team": "Orlando Magic", "number": "32", "year": 2024},
    ],
    "Udonis Haslem": [
        {"team": "Miami Heat", "number": "40", "year": 2024},
    ],
}
RETIRED_NUMBER_SUPPLEMENT_SOURCES = [
    "https://www.nba.com/news/shaquille-oneal-first-jersey-retired-magic",
    "https://www.nba.com/news/heat-retire-udonis-haslem-40-jersey",
    "https://www.nba.com/news/vince-carter-nets-jersey-retire-15",
]

NBA_TEAMS = {
    1610612737: "Atlanta Hawks", 1610612738: "Boston Celtics",
    1610612751: "Brooklyn Nets", 1610612766: "Charlotte Hornets",
    1610612741: "Chicago Bulls", 1610612739: "Cleveland Cavaliers",
    1610612742: "Dallas Mavericks", 1610612743: "Denver Nuggets",
    1610612765: "Detroit Pistons", 1610612744: "Golden State Warriors",
    1610612745: "Houston Rockets", 1610612754: "Indiana Pacers",
    1610612746: "LA Clippers", 1610612747: "Los Angeles Lakers",
    1610612763: "Memphis Grizzlies", 1610612748: "Miami Heat",
    1610612749: "Milwaukee Bucks", 1610612750: "Minnesota Timberwolves",
    1610612740: "New Orleans Pelicans", 1610612752: "New York Knicks",
    1610612760: "Oklahoma City Thunder", 1610612753: "Orlando Magic",
    1610612755: "Philadelphia 76ers", 1610612756: "Phoenix Suns",
    1610612757: "Portland Trail Blazers", 1610612758: "Sacramento Kings",
    1610612759: "San Antonio Spurs", 1610612761: "Toronto Raptors",
    1610612762: "Utah Jazz", 1610612764: "Washington Wizards",
}


def normalize(name):
    ascii_name = unicodedata.normalize("NFKD", name.replace("’", "'")).encode("ascii", "ignore").decode().lower()
    return re.sub(r"[^a-z0-9]+", " ", ascii_name).strip()


def fetch(url):
    error = None
    for attempt in range(3):
        try:
            request = Request(url, headers={"User-Agent": "Mozilla/5.0 (compatible; CourtsideArchive/1.0)"})
            with urlopen(request, timeout=28) as response:
                return html.fromstring(response.read())
        except Exception as exc:
            error = exc
            time.sleep(1.5 * (attempt + 1))
    raise RuntimeError(f"Could not load official NBA source {url}") from error


def clean(value):
    return " ".join(value.split())


def award_rows(document):
    article = document.xpath("//article")[0]
    return [clean(p.text_content()) for p in article.xpath(".//p")]


def parse_awards(key, document):
    rows = award_rows(document)
    results = []
    if key == "all_defensive":
        season = None
        for row in rows:
            match = re.match(r"^>\s*(\d{4}-\d{2})$", row)
            if match:
                season = match.group(1)
                continue
            team = "First Team" if row.startswith("FIRST TEAM") else "Second Team" if row.startswith("SECOND TEAM") else None
            if not team or not season:
                continue
            for entry in row.split("•")[1:]:
                player = clean(entry.split(",", 1)[0])
                if player:
                    results.append((player, {"season": season, "selection": team}))
        return results

    for row in rows:
        match = re.match(r"^(\d{4}-\d{2})\s*[:—–-]\s*(.+)$", row)
        if not match:
            continue
        season, rest = match.groups()
        # The official winners table puts co-winners before their teams.
        # In 1994-95, for example: "Jason Kidd, Grant Hill, Dallas Mavericks, ...".
        rookie_ties = {
            "1970-71": ["Dave Cowens", "Geoff Petrie"],
            "1994-95": ["Jason Kidd", "Grant Hill"],
            "1999-00": ["Steve Francis", "Elton Brand"],
        }
        players = rookie_ties.get(season, [clean(rest.split(",", 1)[0])]) if key == "rookie" else [clean(rest.split(",", 1)[0])]
        for player in players:
            if player:
                results.append((player, {"season": season}))
    return results


def parse_nba75(document):
    table = document.xpath("//table")[0]
    names = [clean(td.text_content()) for row in table.xpath(".//tr")[1:] for td in row.xpath("./td")]
    if len(names) != 76:
        raise ValueError(f"NBA 75 official roster should contain 76 players (tie); got {len(names)}")
    return names


def parse_retired(team, document):
    candidates = []
    for table in document.xpath("//table"):
        headers = [clean(x.text_content()).lower() for x in table.xpath(".//th")]
        if not any(x == "#" for x in headers) or not any("year of induction" in x for x in headers):
            continue
        for row in table.xpath(".//tbody/tr"):
            cells = [clean(x.text_content()) for x in row.xpath("./td")]
            if len(cells) < 5:
                continue
            number, name, _position, _seasons, year = cells[:5]
            if not number or not name or not year.isdigit() or int(year) > 2026:
                continue
            # Nets table labels Carter with announcement year (2024); the
            # actual retirement ceremony was January 25, 2025.
            if team == "Brooklyn Nets" and name == "Vince Carter":
                year = "2025"
            candidates.append((name, {"team": team, "number": number, "year": int(year)}))
    return candidates


def main():
    attended = {row["player_id"].removeprefix("espn:"): row["player"] for row in json.loads(SOURCE.read_text())}
    by_name = {normalize(name): ident for ident, name in attended.items()}
    aliases = {
        "ron artest": "25",  # Metta World Peace, 2004 Defensive Player of the Year
        "j r smith": "2444", "jr smith": "2444",
    }
    def player_id(name):
        key = normalize(name)
        return aliases.get(key) or by_name.get(key)

    results = defaultdict(dict)
    unknown = defaultdict(set)

    def add(name, key, record):
        ident = player_id(name)
        if ident:
            if key == "nba75":
                results[ident][key] = True
            else:
                results[ident].setdefault(key, [])
                if record not in results[ident][key]:
                    results[ident][key].append(record)
        else:
            unknown[key].add(name)

    pages = {**AWARD_URLS, "nba75": NBA75_URL,
             **{f"retired_{ident}": f"https://www.nba.com/team/{ident}" for ident in NBA_TEAMS}}
    with ThreadPoolExecutor(max_workers=5) as pool:
        futures = {pool.submit(fetch, url): key for key, url in pages.items()}
        for future in as_completed(futures):
            key = futures[future]
            document = future.result()
            if key in AWARD_URLS:
                records = parse_awards(key, document)
                for name, record in records:
                    add(name, key, record)
            elif key == "nba75":
                records = parse_nba75(document)
                for name in records:
                    add(name, "nba75", None)
            else:
                team_id = int(key.removeprefix("retired_"))
                records = parse_retired(NBA_TEAMS[team_id], document)
                for name, record in records:
                    add(name, "retired_jersey", record)
            print(f"{key}: {len(records)} source records", flush=True)

    for name, records in RETIRED_NUMBER_SUPPLEMENTS.items():
        for record in records:
            add(name, "retired_jersey", record)

    output = {
        "_meta": {
            "scope": "Official career NBA honors through 2025-26, not limited to games witnessed",
            "award_sources": AWARD_URLS,
            "nba75_source": NBA75_URL,
            "retired_jersey_source": "Official NBA franchise /team/{teamId} RETIRED NUMBERS tables",
            "retired_jersey_supplement_sources": RETIRED_NUMBER_SUPPLEMENT_SOURCES,
            "retired_jersey_definition": "NBA franchise-retired jersey numbers as of 2026-11-01, excluding college, hall of fame, Ring of Honor-only and announced future ceremonies",
            "attended_player_count": len(attended),
            "matched_player_count": len(results),
            "category_counts": {key: sum(key in record for record in results.values()) for key in [*AWARD_URLS, "nba75", "retired_jersey"]},
        },
        "players": {
            ident: {"name": attended[ident], **record}
            for ident, record in sorted(results.items(), key=lambda item: int(item[0]))
        },
    }
    for record in output["players"].values():
        for key, value in record.items():
            if isinstance(value, list):
                value.sort(key=lambda entry: (entry.get("season", ""), entry.get("year", 0), entry.get("team", "")))
    OUTPUT.write_text(json.dumps(output, indent=2, ensure_ascii=False) + "\n")
    print(f"Saved {len(results)} player honors to {OUTPUT}")
    print("Unmatched source names close to archive names should be audited before publishing.")
    for key, names in unknown.items():
        print(f"Unmatched {key}: {len(names)} names")


if __name__ == "__main__":
    main()
