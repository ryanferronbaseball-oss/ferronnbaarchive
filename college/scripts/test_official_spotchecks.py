#!/usr/bin/env python3
"""Exact source transcriptions of 240 college player box-score fields.

Official source row references, audited 2026-10-15:
#18 Colorado @ USD https://usdtoreros.com/sports/mens-basketball/stats/2018-19/colorado/boxscore/8128
#29 SDSU @ USD https://usdtoreros.com/sports/mens-basketball/stats/2019-20/san-diego-state/boxscore/9520
#59 Utah State @ USD https://usdtoreros.com/sports/mens-basketball/stats/2022-23/utah-state/boxscore/13877

This is a targeted stat-field audit, NOT a certification of every field in the full archive.
The source fixture must be changed only after reviewing a new official university box score.
"""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FIELDS = ["minutes","fgm","fga","fg3m","fg3a","ftm","fta","oreb","dreb","reb","pf","ast","tov","blk","stl","pts"]
EXPECTED = [
    (18, "McKinley Wright IV", [36,5,13,1,5,3,4,2,5,7,4,6,5,0,2,14]),
    (18, "Shane Gatling", [24,2,6,2,3,2,3,0,1,1,3,0,0,1,0,8]),
    (18, "Lucas Siewert", [23,3,9,1,3,0,0,1,2,3,4,2,3,0,1,7]),
    (18, "Tyler Bey", [22,3,4,0,1,0,0,2,6,8,5,0,1,5,1,6]),
    (18, "D'Shawn Schwartz", [25,0,2,0,1,0,0,1,1,2,5,3,0,1,0,0]),
    (18, "Evan Battey", [30,7,13,2,3,2,6,1,3,4,3,1,0,0,1,18]),
    (18, "Deleon Brown", [20,2,3,1,2,0,0,0,1,1,1,0,1,0,0,5]),
    (18, "Namon Wright", [14,1,4,0,0,2,2,0,1,1,0,0,1,0,1,4]),
    (18, "Daylen Kountz", [4,1,2,0,0,0,0,0,2,2,0,1,0,0,0,2]),
    (18, "Alexander Strating", [1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0]),
    (18, "Eli Parquet", [1,0,1,0,1,0,0,0,0,0,0,0,0,0,0,0]),
    (29, "Yanni Wetzell", [27,9,11,1,1,1,2,5,7,12,3,1,3,0,2,20]),
    (59, "Jase Townsend", [30,2,9,0,3,3,3,1,3,4,3,3,0,0,1,7]),
    (59, "Daniel Akin", [35,7,11,0,0,7,11,5,10,15,3,0,2,1,0,21]),
    (59, "Eric Williams Jr.", [42,13,20,7,8,10,13,6,7,13,5,1,2,0,2,43]),
]

def main():
    rows=json.loads((ROOT/"data/player_boxscores_espn.json").read_text(encoding="utf-8"))
    by_game_player={(str(p["game_id"]),p["player"]):p for p in rows}
    assert len(by_game_player)==len(rows), "Duplicate person names in a game must be reviewed; never silently merge IDs"
    seen=set()
    for gid,name,stats in EXPECTED:
        key=(str(gid),name)
        assert key not in seen, f"Duplicate source fixture {key}"
        seen.add(key)
        assert len(stats)==len(FIELDS), f"Incorrect source stat row length: {key}"
        assert key in by_game_player, f"Missing official audited athlete: {key}"
        p=by_game_player[key]
        for field,value in zip(FIELDS,stats):
            assert float(p[field])==value, f"Source mismatch {gid} {name} {field}: actual={p[field]}, official={value}"
    assert len(EXPECTED)==15 and len(EXPECTED)*len(FIELDS)==240
    print(f"PASS {len(EXPECTED)} official player rows / {len(EXPECTED)*len(FIELDS)} independently reviewed stat fields")

if __name__=="__main__": main()
