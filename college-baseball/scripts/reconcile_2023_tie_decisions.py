#!/usr/bin/env python3
"""Reconcile exact university 2023 seven-inning draw with zero pitcher W/L/S.

Safe idempotent data migration; no other game or pitcher row may change.
"""
import json
from pathlib import Path

DATA=Path(__file__).resolve().parents[1]/"data"
TARGET="cb-2023-02-20-nebraska-san-diego-att0181"
def read(name):
    return json.loads((DATA/name).read_text(encoding="utf-8"))
games=read("games.json")
game=next((g for g in games if g["id"]==TARGET),None)
if (not game or game.get("verification")!="official_boxscore_verified"
    or game.get("official_draw") is not True
    or [game["away"],game["home"],game["away_score"],game["home_score"],len(game["innings"])]
        != ["Nebraska","San Diego",16,16,7]
    or game.get("pitching_decisions") != {"win":None,"loss":None,"save":None}):
    raise ValueError("Refusing historical draw migration: exact official seven-inning game identity mismatch")
rows=read("player_stats.json")
affected=[r for r in rows if r["game_id"]==TARGET and "pitching" in r]
if len(affected)<4 or {r["team"] for r in affected}!={"Nebraska","San Diego"}:
    raise ValueError("Incomplete official tie pitching evidence")
changed=0
for r in affected:
    for fld in ("wins","losses","saves"):
        v=r["pitching"].get(fld)
        if v not in (None,0):
            raise ValueError("Official tie unexpectedly credits "+fld+" to "+r["player"])
        if v is None:
            r["pitching"][fld]=0
            changed+=1
if changed:
    (DATA/"player_stats.json").write_text(json.dumps(rows,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
print(f"PASS: strictly sourced historical Nebraska-USD draw; {len(affected)} pitchers, {changed} nullable W/L/S indicators reconciled to zero")
