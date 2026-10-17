#!/usr/bin/env python3
"""Export a minimal, deterministic MLB player-ID/name crosswalk for review UI."""
import json
from pathlib import Path

DATA=Path(__file__).resolve().parents[1] / "data"
rows=json.loads((DATA / "player_stats.json").read_text())
names={}
conflicts=[]
for r in rows:
    player_id=r.get("player_id")
    name=r.get("name")
    if player_id is None or not name: continue
    key=str(player_id)
    if key in names and names[key] != name:
        conflicts.append({"player_id":key, "first":names[key], "other":name})
    names.setdefault(key,name)
if conflicts: raise ValueError(f"Conflicting player names: {conflicts[:10]}")
if len(names) < 400: raise ValueError(f"Unexpectedly short player crosswalk: {len(names)}")
out=DATA / "statcast_player_names.json"
out.write_text(json.dumps(dict(sorted(names.items())),ensure_ascii=False,separators=(",",":"))+"\n")
print("Exported",len(names),"official box-score player name IDs to",out)
