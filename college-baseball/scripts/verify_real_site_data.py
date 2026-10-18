#!/usr/bin/env python3
"""Validate committed genuine college-baseball data without creating synthetic games."""
import json
from collections import Counter,defaultdict
from pathlib import Path

D=Path(__file__).resolve().parents[1]/"data"
games=json.loads((D/"games.json").read_text(encoding="utf-8"))
rows=json.loads((D/"player_stats.json").read_text(encoding="utf-8"))
report=json.loads((D/"import_report.json").read_text(encoding="utf-8"))
assert len(games)==444==len({g["id"] for g in games}), "Original attendance identities changed"
assert len(rows)==len({(r["game_id"],r["player_id"]) for r in rows}), "Duplicate player-game row"
assert len(rows)==report["player_stat_rows"], "Data and report player-row counts differ"
game_by_id={g["id"]:g for g in games}
players_by_game=defaultdict(list)
for p in rows:
    assert p["game_id"] in game_by_id, "Player stat row lacks attended game"
    assert p["team"] in (game_by_id[p["game_id"]]["away"],game_by_id[p["game_id"]]["home"])
    players_by_game[p["game_id"]].append(p)
verified=[g for g in games if g["verification"]=="official_boxscore_verified"]
assert len(verified)==report["official_player_boxscores_imported"]
by_season=Counter(g["season"] for g in verified)
assert len(verified)>=396, "Previously committed historical verified boxscores disappeared"
assert by_season[2021]==32, "Full verified 2021 season lost"
assert (by_season[2024],by_season[2025],by_season[2026])==(71,74,68), "Protected 2024-26 changed"
assert all(g["id"] not in players_by_game for g in games if g.get("boxscore_backfill_excluded")), "JUCO rows must be excluded"
for g in verified:
    observed=players_by_game[g["id"]]
    assert len(observed)>=18, f"Verified game has fewer than 18 player rows: {g['id']}"
    assert g.get("source_url","").startswith("https://"), f"Verified game lacks official source {g['id']}"
    assert g.get("innings"), f"Verified game has no full inning scoreboard {g['id']}"
    if g.get("official_draw"):
        assert g["id"] == "cb-2023-02-20-nebraska-san-diego-att0181"
        assert (g["away_score"], g["home_score"], len(g["innings"])) == (16, 16, 7)
        assert g.get("pitching_decisions") == {"win":None,"loss":None,"save":None}
        assert all(r["pitching"].get("wins")==0 and r["pitching"].get("losses")==0
                   for r in observed if "pitching" in r), "Official draw cannot credit pitcher decisions"
    else:
        assert g.get("pitching_decisions",{}).get("win"), f"Verified game has no official winner {g['id']}"
        assert g.get("pitching_decisions",{}).get("loss"), f"Verified game has no official loser {g['id']}"
    assert g.get("away_score") is not None and g.get("home_score") is not None
    for team,score in ((g["away"],g["away_score"]),(g["home"],g["home_score"])):
        batters=[p for p in observed if p["team"]==team and "batting" in p]
        pitchers=[p for p in observed if p["team"]==team and "pitching" in p]
        assert len(batters)>=9 and pitchers, f"Missing player batting/pitching {g['id']} {team}"
        assert sum(p["batting"]["runs"] for p in batters)==score, f"R runs differ from hitters {g['id']} {team}"
        assert len({p["batting_slot"] for p in batters})==9, f"MLB-style batting order not nine slots {g['id']} {team}"
print(json.dumps({"status":"PASS","original_attendance_games":len(games),
                  "verified_games":len(verified),"player_game_rows":len(rows),
                  "verified_by_year":dict(sorted(by_season.items()))},indent=2))
