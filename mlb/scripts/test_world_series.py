"""Offline checks for MLB World Series career title tags and profile integration."""

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
dataset = json.loads((ROOT / "data/world_series_championships.json").read_text())
players = dataset["players"]
attended = {str(p["player_id"]) for p in json.loads((ROOT / "data/player_stats.json").read_text())}

assert len(players) == dataset["_meta"]["champion_players_matched"]
assert len(players) >= 350, f"Unexpectedly few champions matched: {len(players)}"
assert set(players) <= attended, "Champion IDs must match attended MLB player IDs"
for player_id, record in players.items():
    titles = record["championships"]
    years = [title["year"] for title in titles]
    assert years == sorted(set(years)), (player_id, years)
    assert all(1980 <= year <= 2026 and year != 1994 for year in years)
    assert all(title.get("team") for title in titles)

examples = {
    "116539": [1996, 1998, 1999, 2000, 2009],  # Derek Jeter
    "605141": [2018, 2020, 2024, 2025],  # Mookie Betts
    "477132": [2020, 2024, 2025],  # Clayton Kershaw
    "660271": [2024, 2025],  # Shohei Ohtani
    "120074": [2004, 2007, 2013],  # David Ortiz
    "425877": [2006, 2011],  # Yadier Molina
    "661388": [2021, 2026],  # William Contreras
    "592885": [2026],  # Christian Yelich
}
for player_id, expected in examples.items():
    actual = [title["year"] for title in players[player_id]["championships"]]
    assert actual == expected, (player_id, actual, expected)

pages = (ROOT / "assets/pages.js").read_text()
css = (ROOT / "assets/archive.css").read_text()
html = (ROOT / "player.html").read_text()
assert 'data/world_series_championships.json' in pages
assert '["world_series","World Series Champion","ws","🏆"]' in pages
assert 'a.team?" · "+esc(a.team)' in pages
assert '.mlb-profile-badge.ws' in css and '.mlb-award-tab.ws' in css
assert 'mlb-world-series-20261101' in html

print(f"World Series title checks passed for {len(players)} player profiles; {len(examples)} exact-title examples verified.")
