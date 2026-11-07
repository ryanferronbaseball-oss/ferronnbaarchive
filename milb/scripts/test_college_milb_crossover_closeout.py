#!/usr/bin/env python3
"""Validate audited College Baseball/MiLB/MLB links and reciprocal badge gates."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
M = ROOT / "milb/data"
C = ROOT / "college-baseball/data"

def read(path):
    return json.loads(path.read_text(encoding="utf8"))

games = read(M / "games.json")
players = read(M / "player_stats.json")
college_rows = read(C / "player_stats.json")
identity = read(C / "player_identity_crosswalk.json")
links = read(M / "college_links.json")
mlb_links = read(M / "player_links.json")
college_mlb = read(C / "mlb_crosswalk.json")
audit = read(M / "college_crossover_closeout_2026-11-07.json")

canonical = {source: merge["canonical_id"] for merge in identity["merges"]
             for source in merge["source_player_ids"]}
college_ids = {canonical.get(row["player_id"], row["player_id"])
               for row in college_rows if row.get("player_id")}
mi_ids = {row["player_id"] for row in players if isinstance(row.get("player_id"), int)}
assert len(games) == 119 and len({g["source_game_id"] for g in games}) == 119
assert len(links) == audit["total_verified_links"] == 22
assert len({link["milb_id"] for link in links}) == len(links)
assert all(link["verified"] and link["milb_id"] in mi_ids
           and link["college_player_id"] in college_ids for link in links)

milb_mlb_seen = {link["milb_id"] for link in mlb_links
                 if link.get("verified") and link.get("mlb_seen") and link.get("mlb_debut")}
college_mlb_seen = {(link["college_player_id"], link["mlb_player_id"])
                    for link in college_mlb if link.get("verified")}
triple = {link["milb_id"] for link in links
          if link["milb_id"] in milb_mlb_seen
          and (link["college_player_id"], link["milb_id"]) in college_mlb_seen}
assert triple == {668970, 669477}, triple
assert triple == {x["milb_id"] for x in audit["verified_three_level_attendees"]}
assert 523260 not in {x["milb_id"] for x in links}

mi_profile = (ROOT / "milb/assets/profile.js").read_text(encoding="utf8")
college_profile = (ROOT / "college-baseball/assets/archive.js").read_text(encoding="utf8")
mlb_profile = (ROOT / "mlb/assets/pages.js").read_text(encoding="utf8")
for source in (mi_profile, college_profile, mlb_profile):
    assert "SEEN IN COLLEGE + MiLB + MLB" in source
    assert "SEEN IN COLLEGE + MiLB" in source
assert "linked.mlb_seen===true&&collegeLink" in mi_profile
assert "String(cross.mlb_player_id)===String(matchedMiLB.milb_id)" in college_profile
assert '"milb-triple-level"' in mi_profile
assert 'class="mlb-profile-badge cb-triple-level"' in college_profile
assert "#171717" in (ROOT / "milb/assets/profile.css").read_text(encoding="utf8")
assert "#F4CC70" in (ROOT / "college-baseball/assets/archive.css").read_text(encoding="utf8")
assert "verifiedCollegeMiLB.has(String(collegeId)+\"|\"+String(milbId))" in mlb_profile
assert "#F4CC70" in (ROOT / "mlb/assets/archive.css").read_text(encoding="utf8")
print("PASS: 119 games, 22 reciprocal college/MiLB links, 2 three-level badges, no false Joe Kelly merge")
