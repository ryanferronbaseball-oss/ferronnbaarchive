#!/usr/bin/env python3
"""Investigate ambiguous UNLV Ja Sharman ID using actual gamebook role, not name guesses."""
import json
from pathlib import Path
d=Path(__file__).resolve().parents[1]/"data"
rows=json.loads((d/"player_stats.json").read_text())
games={g["id"]:g for g in json.loads((d/"games.json").read_text())}
ids=["cb-unlv-ja-sharman","cb-unlv-jason-sharman","cb-unlv-josh-sharman",
"cb-liberty-nathan-keeter","cb-lenoir-rhyne-nathaneal-keeter"]
out={}
for pid in ids:
 selected=[r for r in rows if r["player_id"]==pid]
 out[pid]=[{"game_id":r["game_id"],"date":games.get(r["game_id"],{}).get("date"),
 "name":r["player"],"team":r["team"],"position":r.get("position"),
 "batting":r.get("batting"),"pitching":r.get("pitching")} for r in selected]
(d/"identity_audit_batch_04_source_evidence.json").write_text(json.dumps(out,indent=2)+"\n")
print(json.dumps({k:len(v) for k,v in out.items()}))
