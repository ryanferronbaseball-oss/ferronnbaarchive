#!/usr/bin/env python3
"""Build year-by-year NBA career-honor details for witnessed players.

Season-specific MVP and All-NBA selections come from NBA.com; All-Star
selection years from the same referenced source as our verified totals; and
championship years are checked against reviewed per-player title counts.
Only exact, count-reconciled history is exported.
"""

import json
import re
import time
import unicodedata
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from urllib.parse import quote
from urllib.request import Request, urlopen

from lxml import html

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "data/nba_award_years.json"
NBA_MVP = "https://www.nba.com/news/history-mvp-award-winners"
NBA_ALL = "https://www.nba.com/news/history-all-nba-teams"
ALL_STAR = "https://en.wikipedia.org/wiki/List_of_NBA_All-Stars"
PLAYER_WIKI = "https://en.wikipedia.org/wiki/"
WIKI_PAGE_TITLES = {
    "Derek Anderson": "Derek Anderson (basketball)",
    "Mark Madsen": "Mark Madsen (basketball)",
    "Ben Wallace": "Ben Wallace (basketball)",
    "James Jones": "James Jones (basketball, born 1980)",
    "David West": "David West (basketball)",
    "Tony Allen": "Tony Allen (basketball)",
    "David Lee": "David Lee (basketball)",
    "Glen Davis": "Glen Davis (basketball)",
    "Justin Jackson": "Justin Jackson (basketball, born 1995)",
}


def normalize(value):
    value = unicodedata.normalize("NFKD", value.replace("’", "'")).encode("ascii", "ignore").decode().lower()
    return re.sub(r"[^a-z0-9]+", " ", value).strip()


def fetch(url):
    issue = None
    for attempt in range(3):
        try:
            req = Request(url, headers={"User-Agent": "Mozilla/5.0 (compatible; CourtsideArchive/1.0)"})
            with urlopen(req, timeout=28) as response:
                return html.fromstring(response.read())
        except Exception as error:
            issue = error
            time.sleep(1 + attempt)
    raise RuntimeError(f"Unable to fetch {url}") from issue


def clean(text):
    return " ".join(text.split())


def all_nba_seasons(document):
    season = None
    for line in (clean(p.text_content()) for p in document.xpath("//article//p")):
        found = re.match(r"^>\s*(\d{4}-\d{2})$", line)
        if found:
            season = found.group(1)
            continue
        selection = next((label for prefix, label in [("FIRST TEAM", "First Team"), ("SECOND TEAM", "Second Team"), ("THIRD TEAM", "Third Team")] if line.startswith(prefix)), None)
        if not season or not selection:
            continue
        for part in line.split("•")[1:]:
            # Before 2024, most records prefix the player's position ("F: ").
            name = clean(part.split(",", 1)[0])
            name = re.sub(r"^[FCG][:-]\s*", "", name)
            if name:
                yield name, {"season": season, "selection": selection}


def mvp_seasons(document):
    for line in (clean(p.text_content()) for p in document.xpath("//article//p")):
        found = re.match(r"^(\d{4}-\d{2})\s*[—–-]\s*([^,]+),", line)
        if found:
            season, name = found.groups()
            yield clean(name), {"season": season}


def expand_years(value):
    """Expand e.g. '1998; 2000–2016' into explicit selection years."""
    result = []
    for part in re.split(r"\s*[;,]\s*", value):
        found = re.fullmatch(r"(\d{4})\s*[–—-]\s*(\d{4})", part)
        if found:
            start, end = map(int, found.groups())
            if not 1951 <= start <= end <= 2026:
                raise ValueError(f"Invalid selection year range {part}")
            result.extend(range(start, end + 1))
        else:
            result.extend(int(year) for year in re.findall(r"\b\d{4}\b", part))
    return sorted(set(result))


def all_star_seasons(document):
    table = document.xpath("//table")[1]
    for row in table.xpath(".//tr")[1:]:
        cells = [clean(cell.text_content()) for cell in row.xpath("./th|./td")]
        if len(cells) < 3 or not cells[1].isdigit():
            continue
        name = re.sub(r"\[.*?\]", "", re.sub(r"[\^*†§].*", "", cells[0]))
        years = expand_years(cells[2])
        if years:
            yield name, years, int(cells[1])


def champion_years(document, expected_count):
    tables = document.xpath('//table[contains(@class,"infobox")]')
    if not tables:
        return []
    groups = []
    for li in tables[0].xpath(".//li"):
        label = clean(li.text_content())
        if not re.search(r"\b(?:NBA|BAA) champion\b", label, re.I):
            continue
        # Only the regular NBA/BAA title counts; not Cup, NCAA, NBL,
        # conference championships, or coach/front-office honors.
        if "(" not in label or "retired" in label.lower():
            continue
        dates = label.split("(", 1)[1].split(")", 1)[0]
        years = expand_years(dates)
        groups.append(years)
    # Some retired players later earned rings as coaches or executives. A
    # separately listed player-era award must exactly match the reviewed
    # career championship total; never blend it with those later titles.
    return next((dates for dates in groups if len(dates) == expected_count), sorted(set(year for dates in groups for year in dates)))


def main():
    awards = json.loads((ROOT / "data/nba_career_awards.json").read_text())["players"]
    titles = json.loads((ROOT / "data/nba_championships.json").read_text())["players"]
    ids = {normalize(p["name"]): ident for ident, p in {**titles, **awards}.items()}
    aliases = {"ron artest": "25", "metta sandiford artest": "25", "j r smith": "2444", "jr smith": "2444"}
    matched = defaultdict(dict)

    def lookup(name):
        key = normalize(name)
        return aliases.get(key) or ids.get(key)

    pages = {"mvp": NBA_MVP, "all_nba": NBA_ALL, "all_star": ALL_STAR}
    with ThreadPoolExecutor(max_workers=3) as pool:
        documents = {key: future.result() for key, future in ((key, pool.submit(fetch, url)) for key, url in pages.items())}

    for key, parser in [("mvp", mvp_seasons), ("all_nba", all_nba_seasons)]:
        for name, record in parser(documents[key]):
            ident = lookup(name)
            if ident and awards.get(ident, {}).get(key):
                matched[ident].setdefault(key, []).append(record)

    for name, years, count in all_star_seasons(documents["all_star"]):
        ident = lookup(name)
        if ident and awards.get(ident, {}).get("all_star") and count == awards[ident]["all_star"] and len(years) == count:
            matched[ident]["all_star"] = years

    # Inspect one player at a time: official total is the independent guard.
    missing = []
    with ThreadPoolExecutor(max_workers=5) as pool:
        futures = {}
        for ident, player in titles.items():
            slug = quote(WIKI_PAGE_TITLES.get(player["name"], player["name"]).replace(" ", "_"))
            futures[pool.submit(fetch, PLAYER_WIKI + slug)] = (ident, player)
        for future in as_completed(futures):
            ident, player = futures[future]
            try:
                years = champion_years(future.result(), player["championships"])
            except Exception as exc:
                print(f"Championship source unavailable: {player['name']} ({exc})", flush=True)
                years = []
            if len(years) == player["championships"]:
                matched[ident]["championships"] = years
            else:
                missing.append((ident, player["name"], player["championships"], years))

    # Missing or ambiguous years are never silently inferred from totals.
    inconsistent = []
    for ident, player in awards.items():
        for key, count_key in [("mvp", "mvp_count"), ("all_nba", "all_nba_count")]:
            if player.get(count_key) and len(matched[ident].get(key, [])) != player[count_key]:
                inconsistent.append((ident, player["name"], key, player[count_key], len(matched[ident].get(key, []))))
                matched[ident].pop(key, None)

    result = {"_meta": {
        "meaning": "Exact career NBA title and award years, separate from attended-game statistics",
        "mvp_source": NBA_MVP,
        "all_nba_source": NBA_ALL,
        "all_star_source": ALL_STAR,
        "championship_source": "Individual player honor lists on Wikipedia, reconciled to reviewed NBA championship totals",
        "through_season": "2025-26",
        "counts": {key: sum(key in data for data in matched.values()) for key in ["championships", "mvp", "all_nba", "all_star"]},
        "unreconciled_championships": [item[1] for item in sorted(missing)],
        "unreconciled_awards": [f"{x[1]}: {x[2]}" for x in sorted(inconsistent)],
    }, "players": {ident: dict(sorted(data.items())) for ident, data in sorted(matched.items(), key=lambda x: int(x[0])) if data}}
    for item in result["players"].values():
        for key in ["mvp", "all_nba"]:
            if key in item:
                item[key].sort(key=lambda r: r["season"])
    OUTPUT.write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n")
    print("Saved", len(result["players"]), "players; counts", result["_meta"]["counts"])
    print("Unreconciled championship rows:", missing)
    print("Unreconciled awards:", inconsistent)


if __name__ == "__main__":
    main()
