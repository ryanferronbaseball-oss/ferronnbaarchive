#!/usr/bin/env python3
"""Apply owner-approved Batch 3 CSUN spelling-ID merges, fail closed on collisions.
Original player_stats.json and games.json are NEVER written.
"""
import json, hashlib
from collections import defaultdict
from pathlib import Path

D=Path(__file__).resolve().parents[1]/"data"
read=lambda f:json.loads((D/f).read_text(encoding="utf8"))
def save(f,o):(D/f).write_text(json.dumps(o,indent=2,ensure_ascii=False)+"\n",encoding="utf8")
source=D/"player_stats.json"
gamespath=D/"games.json"
source_hash=hashlib.sha256(source.read_bytes()).hexdigest()
games_hash=hashlib.sha256(gamespath.read_bytes()).hexdigest()
raw=read("player_stats.json")
games=read("games.json")
cross=read("player_identity_crosswalk.json")
audit=read("player_identity_reconciliation_audit.json")
candidates=read("identity_audit_batch_03_candidates.json")
names=read("player_name_corrections.json")
assert len(raw)==13196 and len(games)==437
assert len(cross["merges"])==cross["activated_person_merges"]==177
assert len(cross["owner_rejected_merge_candidates"])==28
assert candidates["source_rows_scanned"]==len(raw)
assert len(candidates["candidates"])==9
by_id=defaultdict(list)
for r in raw:by_id[r["player_id"]].append(r)
existing={sid:m["canonical_id"] for m in cross["merges"] for sid in m["source_player_ids"]}
prior_rejected={sid for m in cross["owner_rejected_merge_candidates"] for sid in m["source_player_ids"]}
first_seven=["Andrew Sojka","Emanuel Dean","Isaac Ontiveros","Jakob Simons","Joey Kramer","Kenji Pallares","Shunsuke Sakaino"]
lookup={r["source_name"]:r for r in candidates["candidates"]}
assert set(first_seven).issubset(lookup)
additions=[]
for n in first_seven:
 c=lookup[n]
 assert c["kind"]=="cross_school_same_full_name" and len(c["candidates"])==2
 by_team={a["school"]:a for a in c["candidates"]}
 assert set(by_team)=={"Cal State Northrdige","Cal State Northridge"}
 correct=by_team["Cal State Northridge"]["source_id"]
 typo=by_team["Cal State Northrdige"]["source_id"]
 assert correct.startswith("cb-cal-state-northridge-") and typo.startswith("cb-cal-state-northrdige-")
 assert correct!=typo and not ({correct,typo}&(set(existing)|prior_rejected))
 src=by_id[typo]+by_id[correct]
 assert len(src)==c["source_rows"]
 assert all(r["player"]==n for r in src)
 assert {r["team"] for r in src}==set(by_team)
 assert len({r["game_id"] for r in src})==len(src),f"Same-game collision: {n}"
 additions.append({"name":n,"canonical_id":correct,"source_player_ids":[correct,typo],
  "schools":["Cal State Northridge","Cal State Northrdige"],
  "pairs":[{"team":team,"source_player_id":pid} for team,pid in sorted({(r["team"],r["player_id"]) for r in src})],
  "source_rows":len(src),
  "approval_batch":3,
  "note":"One team typed Cal State Northrdige in the historical game source. Source rows unchanged."})
assert len(additions)==7
rejected=lookup["Tanner Smith"]
ids={x["source_id"] for x in rejected["candidates"]}
assert ids=={"cb-oregon-tanner-smith","cb-presbyterian-tanner-smith"}
assert all(by_id[i] for i in ids)
assert not (ids & set(existing))
cross["owner_rejected_merge_candidates"].append({
 "name":"Tanner Smith","schools":["Oregon","Presbyterian"],
 "source_player_ids":["cb-oregon-tanner-smith","cb-presbyterian-tanner-smith"],
 "decision":"do_not_merge","confirmed_on":"2026-11-17",
 "approval_batch":3,"note":"Owner explicitly decided SEPARATE; do not infer a transfer from an identical name."
})
jul=lookup["T Juline"]
assert jul["source_id"]=="cb-uc-riverside-t-juline"
assert {x["full_name"] for x in jul["candidates"]}=={"Taylor Juline","Tucker Juline"}
assert all(by_id[x["source_id"]] for x in jul["candidates"]+[{"source_id":jul["source_id"]}])
cross["merges"].extend(additions)
cross["requested_person_merges"]+=7
cross["activated_person_merges"]+=7
assert cross["pending_person_merges"]==0
# Resolve and verify all source rows as the browser does, including existing game-specific corrections.
fixes={}
for group in [names,*names["games"]]:
 for f in group["corrections"]:
  k=(group["game_id"],group["team"],f["source_player_id"])
  assert k not in fixes
  fixes[k]=f
aliases={}
redirects={}
for m in cross["merges"]:
 assert m["canonical_id"] in m["source_player_ids"]
 for sid in m["source_player_ids"]:
  assert sid not in redirects or redirects[sid]==m["canonical_id"]
  redirects[sid]=m["canonical_id"]
 for p in m["pairs"]:
  k=(p["team"],p["source_player_id"])
  assert k not in aliases or aliases[k]==m["canonical_id"]
  aliases[k]=m["canonical_id"]
for f in fixes.values():
 sid,canonical=f["source_player_id"],f["canonical_player_id"]
 assert sid not in redirects or redirects[sid]==canonical
 redirects[sid]=canonical
profiles=defaultdict(set)
applied=set()
for r in raw:
 key=(r["game_id"],r["team"],r["player_id"])
 fixed=fixes.get(key)
 if fixed:
  assert r["player"]==fixed["source_player_name"]
  applied.add(key)
 effective=fixed["canonical_player_id"] if fixed else r["player_id"]
 target=aliases.get((r["team"],effective),effective)
 assert r["game_id"] not in profiles[target],f"Duplicate profile game {target} / {r['game_id']}"
 profiles[target].add(r["game_id"])
assert applied==set(fixes)
assert sum(map(len,profiles.values()))==len(raw)
for rejected_entry in cross["owner_rejected_merge_candidates"]:
 a,b=rejected_entry["source_player_ids"]
 assert redirects.get(a,a)!=redirects.get(b,b),f"Protected SEPARATE breached: {rejected_entry['name']}"
assert jul["source_id"] not in redirects, "UNSURE T Juline mapped without approval"
audit["current_state"]["activated_person_merges"]=cross["activated_person_merges"]
audit["current_state"]["requested_person_merges"]=cross["requested_person_merges"]
audit["current_state"]["latest_review_batch"]={
 "batch":3,"approved_combinations":7,"new_merge_entries":7,
 "protected_separate":"Tanner Smith (Oregon / Presbyterian)",
 "unresolved":"T Juline (UC Riverside: Taylor or Tucker)",
 "owner_approved":True,"same_game_collisions":0,
 "original_box_scores_modified":False
}
audit["current_state"]["most_recent_merge"]={
 "name":"Shunsuke Sakaino",
 "schools":["Cal State Northrdige","Cal State Northridge"],
 "combined_game_log_rows":4
}
save("player_identity_crosswalk.json",cross)
save("player_identity_reconciliation_audit.json",audit)
save("identity_audit_batch_03_decisions.json",{
 "batch":3,"owner_decisions":{"COMBINE":first_seven,"SEPARATE":["Tanner Smith (Oregon / Presbyterian)"],"UNSURE":["T Juline (UC Riverside)"]},
 "applied":7,"source_rows_affected":sum(x["source_rows"] for x in additions),
 "collision_count":0,"crosswalk_conflicts":0,
 "original_source_hash_sha256":source_hash,"original_games_hash_sha256":games_hash,
 "separate_decisions_preserved":len(cross["owner_rejected_merge_candidates"]),
 "status":"PASS","note":"T Juline deliberately left unmapped; source boxes and player stats not modified."
})
assert hashlib.sha256(source.read_bytes()).hexdigest()==source_hash
assert hashlib.sha256(gamespath.read_bytes()).hexdigest()==games_hash
print(json.dumps({"status":"PASS","added_merges":7,"total_merges":len(cross["merges"]),
 "protected_separate":len(cross["owner_rejected_merge_candidates"]),"unresolved":"T Juline",
 "player_rows_unchanged":len(raw),"profile_collision_count":0}))

# Invoke approved Batch 3 validation workflow.

# Rerun after reconciling older validation row-count assertions.
