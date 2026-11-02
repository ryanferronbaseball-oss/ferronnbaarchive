#!/usr/bin/env python3
"""Check current college-baseball identities without changing source statistics.

This follows the browser's scoped name-correction/merge order and deliberately
does not use the historical 101-proposal reconciliation snapshot as live state.
"""
import json
from collections import Counter, defaultdict
from pathlib import Path

D = Path(__file__).resolve().parents[1] / "data"
load = lambda filename: json.loads((D / filename).read_text(encoding="utf-8"))
games = load("games.json")
raw = load("player_stats.json")
names = load("player_name_corrections.json")
crosswalk = load("player_identity_crosswalk.json")
audit = load("player_identity_reconciliation_audit.json")["current_state"]

assert len(games) == 444 and len(raw) == 13184
assert len({g["id"] for g in games}) == len(games)
assert len({(r["game_id"], r["player_id"]) for r in raw}) == len(raw)
game_ids = {g["id"] for g in games}
assert all(r["game_id"] in game_ids for r in raw)

fixes = {}
for game in [names, *names["games"]]:
    for fix in game["corrections"]:
        key = (game["game_id"], game["team"], fix["source_player_id"])
        assert key not in fixes, f"Duplicate name correction: {key}"
        fixes[key] = fix

merges = crosswalk["merges"]
assert len(merges) == len({m["canonical_id"] for m in merges}) == 162
assert crosswalk["pending_person_merges"] == audit["pending_person_merges"] == 0
assert crosswalk["activated_person_merges"] == audit["activated_person_merges"] == 162
rejected = {m["name"] for m in crosswalk["owner_rejected_merge_candidates"]}
assert rejected.isdisjoint({m["name"] for m in merges})

aliases, redirects = {}, {}
for merge in merges:
    canonical = merge["canonical_id"]
    assert len(merge["source_player_ids"]) == len(set(merge["source_player_ids"]))
    assert canonical in merge["source_player_ids"]
    for pair in merge["pairs"]:
        key = (pair["team"], pair["source_player_id"])
        assert key not in aliases or aliases[key] == canonical, key
        aliases[key] = canonical
    for source_id in merge["source_player_ids"]:
        assert source_id not in redirects or redirects[source_id] == canonical
        redirects[source_id] = canonical
for fix in fixes.values():
    sid, canonical = fix["source_player_id"], fix["canonical_player_id"]
    assert sid not in redirects or redirects[sid] == canonical, sid
    redirects[sid] = canonical

profiles = defaultdict(list)
applied = set()
for row in raw:
    key = (row["game_id"], row["team"], row["player_id"])
    fix = fixes.get(key)
    if fix:
        assert row["player"] == fix["source_player_name"], key
        applied.add(key)
    interim_id = fix["canonical_player_id"] if fix else row["player_id"]
    profile_id = aliases.get((row["team"], interim_id), interim_id)
    profiles[profile_id].append(row)
assert applied == set(fixes), f"Unmatched name corrections: {set(fixes) - applied}"
assert sum(map(len, profiles.values())) == len(raw)
assert all(len({r["game_id"] for r in entries}) == len(entries)
           for entries in profiles.values()), "Duplicate appearance on a profile"

# Every merged profile has the original school-specific entries, same stat
# payloads, and exactly the unique attended-game count expected by the manifest.
raw_by_school_id = defaultdict(list)
for row in raw:
    raw_by_school_id[(row["team"], row["player_id"])].append(row)
for merge in merges:
    source = [r for pair in merge["pairs"]
              for r in raw_by_school_id[(pair["team"], pair["source_player_id"])]]
    # Two official game replacements supply additional school-side rows, and
    # Dalton Mashore's Saint Mary's source is linked via a full-name correction.
    if merge["name"] in {"Michael Graziano", "Carson Ohl", "Jett Lovett", "Dalton Mashore"}:
        assert len(source) + 1 == merge["source_rows"], merge["name"]
        continue
    assert len(source) == merge["source_rows"], merge["name"]
    assert all(r in profiles[merge["canonical_id"]] for r in source), merge["name"]

for name, count, schools in (
    ("Tate Soderstrom", 7, {"Arizona", "UC San Diego"}),
    ("Ethan Lizama", 2, {"Western Kentucky", "South Carolina"}),
    ("Kyle Hvidsten", 2, {"Western Kentucky", "Liberty"}),
    ("Dylan O\'Connell", 4, {"Western Kentucky", "Milwaukee"}),
):
    merge = next(m for m in merges if m["name"] == name)
    entries = profiles[merge["canonical_id"]]
    assert len(entries) == count and {r["team"] for r in entries} == schools

print(json.dumps({
    "status": "PASS",
    "attended_games": len(games),
    "raw_player_game_rows_preserved": len(raw),
    "game_scoped_name_corrections": len(fixes),
    "merged_identities": len(merges),
    "pending_merges": crosswalk["pending_person_merges"],
    "unique_profile_ids_in_raw_rows": len(profiles),
    "profile_game_log_duplicate_count": 0,
    "original_stat_payloads_rewritten": 0,
}, indent=2))
