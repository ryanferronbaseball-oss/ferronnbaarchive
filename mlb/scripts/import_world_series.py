#!/usr/bin/env python3
"""Build player World Series titles from MLB's official schedules and season stats.

Attribution uses actual MLB regular-season appearances for a champion team.
It is intentionally broader than membership on the World Series game roster:
players who appeared earlier in the title season are included, even if traded.
"""

import json
import time
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import Request, urlopen


ROOT = Path(__file__).resolve().parents[1]
STATS = ROOT / "data" / "player_stats.json"
OUTPUT = ROOT / "data" / "world_series_championships.json"
FIRST_YEAR = 1980
LAST_YEAR = 2026
NO_WORLD_SERIES = {1994}
BASE = "https://statsapi.mlb.com/api/v1"


def get_json(path, params):
    url = f"{BASE}/{path}?{urlencode(params)}"
    last_error = None
    for attempt in range(4):
        try:
            with urlopen(Request(url, headers={"User-Agent": "CourtsideArchive/1.0"}), timeout=28) as response:
                return json.load(response)
        except Exception as error:
            last_error = error
            time.sleep((attempt + 1) * 1.5)
    raise RuntimeError(f"MLB StatsAPI failed after retries: {url}") from last_error


def champion_year(year):
    schedule = get_json("schedule", {"season": year, "gameTypes": "W", "sportId": 1})
    games = [game for day in schedule.get("dates", []) for game in day.get("games", [])]
    completed = [game for game in games if game.get("status", {}).get("detailedState") == "Final"
                 and any(side.get("isWinner") for side in game.get("teams", {}).values())]
    if not completed:
        raise ValueError(f"No completed World Series games returned for {year}")
    clincher = max(completed, key=lambda game: (game["officialDate"], game["gamePk"]))
    winners = [side["team"] for side in clincher["teams"].values() if side.get("isWinner")]
    if len(winners) != 1:
        raise ValueError(f"Cannot identify World Series clincher winner for {year}")
    champion = winners[0]

    stats = get_json("stats", {
        "stats": "season", "group": "hitting,pitching", "season": year,
        "teamId": champion["id"], "sportIds": 1,
        "playerPool": "all", "limit": 300,
    })
    if len(stats.get("stats", [])) < 2:
        raise ValueError(f"Incomplete batting/pitching statistics for {year} {champion['name']}")
    participants = {}
    for group in stats["stats"]:
        for split in group.get("splits", []):
            if split.get("stat", {}).get("gamesPlayed", 0) <= 0:
                continue
            player = split.get("player", {})
            if player.get("id"):
                participants[player["id"]] = player["fullName"]
    if len(participants) < 15:
        raise ValueError(f"Too few champion-season players for {year}: {len(participants)}")
    return year, champion, participants


def main():
    attended_players = {row["player_id"]: row["name"] for row in json.loads(STATS.read_text())}
    titles = defaultdict(list)
    years = [year for year in range(FIRST_YEAR, LAST_YEAR + 1) if year not in NO_WORLD_SERIES]
    results = []
    with ThreadPoolExecutor(max_workers=5) as pool:
        for task in as_completed([pool.submit(champion_year, year) for year in years]):
            result = task.result()
            results.append(result)
            print(f"{result[0]}: {result[1]['name']} ({len(result[2])} players)", flush=True)
    for year, team, players in sorted(results):
        for player_id in players:
            if player_id in attended_players:
                titles[str(player_id)].append({"year": year, "team": team["name"]})

    payload = {
        "_meta": {
            "source": "MLB StatsAPI official World Series schedules and champion-team season statistics",
            "champions_source": f"{BASE}/schedule?season=2026&gameTypes=W&sportId=1",
            "players_source": f"{BASE}/stats?stats=season&group=hitting,pitching&season=2026&teamId=158&sportIds=1&playerPool=all&limit=300",
            "definition": "Played at least one MLB regular-season game for the World Series-winning club in the championship year (including players not on the World Series roster)",
            "scope": "Full career titles, not limited to seasons or games attended",
            "years": [FIRST_YEAR, LAST_YEAR],
            "no_world_series": sorted(NO_WORLD_SERIES),
            "attended_players": len(attended_players),
            "champion_players_matched": len(titles),
        },
        "players": {
            player_id: {"name": attended_players[int(player_id)], "championships": titles[player_id]}
            for player_id in sorted(titles, key=int)
        },
    }
    OUTPUT.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n")
    print(f"Saved {len(titles)} player records to {OUTPUT}")


if __name__ == "__main__":
    main()
