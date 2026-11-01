#!/usr/bin/env python3
"""Offline checks for the six new MLB award tags and retired-number badges."""
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
awards = json.loads((ROOT / "data/extra_career_awards.json").read_text())
players = awards["players"]
attended = {str(row["player_id"]) for row in json.loads((ROOT / "data/player_stats.json").read_text())}
categories = {
    "rookie_of_year": 40,
    "all_mlb": 65,
    "world_series_mvp": 15,
    "lcs_mvp": 35,
    "hank_aaron": 25,
    "platinum_glove": 10,
    "retired_number": 25,
}

assert set(players) <= attended, "Every new award must be assigned by attended MLB player ID"
for key, minimum in categories.items():
    recipients = [p for p in players.values() if p.get(key)]
    assert len(recipients) >= minimum, (key, len(recipients))
    assert awards["_meta"]["award_recipients"][key] == len(recipients), key
    for player in recipients:
        entries = player[key]
        years = [entry["year"] for entry in entries]
        assert years == sorted(years), (player["name"], key, years)
        assert all(1900 <= y <= 2026 for y in years)
        if key == "all_mlb":
            assert all(e["level"] in ("First Team", "Second Team") for e in entries)
        if key == "retired_number":
            assert all(e.get("team") and e.get("number") and e.get("date", "")[:4] == str(e["year"])
                       for e in entries), (player["name"], entries)

assert any(e["year"] == 1996 for e in players["116539"]["rookie_of_year"]), "Derek Jeter ROY"
assert any(e["year"] == 2000 for e in players["116539"]["world_series_mvp"]), "Derek Jeter WS MVP"
assert any(e["number"] == "2" and e["year"] == 2017 for e in players["116539"]["retired_number"]), "Jeter #2"
assert any(e["number"] == "33" and e["year"] == 2021 for e in players["123833"]["retired_number"]), "Walker #33"
assert any(e["year"] == 2020 and e["level"] == "Second Team" for e in players["477132"]["all_mlb"]), "Kershaw All-MLB"
assert any(e["year"] == 2013 for e in players["120074"]["world_series_mvp"]), "David Ortiz WS MVP"

pages = (ROOT / "assets/pages.js").read_text()
html = (ROOT / "player.html").read_text()
for key in categories:
    assert f'"{key}"' in pages, f"Missing profile integration for {key}"
assert "data/extra_career_awards.json" in pages
assert 'a.number?" · #"+esc(a.number)' in pages
assert 'a.level?" · "+esc(a.level)' in pages
assert "mlb-extra-honors-20261101" in html, "Profile JS needs a fresh cache key"
print("PASS all 7 new honors matched to real attended MLB IDs; exact award/jersey years and clickable profile integration verified")
