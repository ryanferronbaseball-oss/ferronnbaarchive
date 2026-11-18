#!/usr/bin/env python3
"""Apply safe owner-approved Batch 4 identities and protect separately identified players.

#1 Ja Sharman (RF) -> Jason Sharman (outfielder).
#2 Ja Sharman -> Josh Sharman: BLOCKED as a player-role mismatch; Jason & Josh are brothers.
#15 Nathan Keeter -> Nathaneal Keeter: confirmed Liberty -> Lenoir-Rhyne.
Other 17 proposals: owner instructed only selected pairs COMBINE, therefore SEPARATE.
All original source rows and games remain untouched. Validate source rows and collisions.
"""
import hashlib,json
from pathlib import Path
from collections import defaultdict
D=Path(__file__).resolve().parents[1]/"data"
load=lambda n:json.loads((D/n).read_text(encoding="utf-8"))
save=lambda n,d:(D/n).write_text(json.dumps(d,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
orig=D/"player_stats.json";gamepath=D/"games.json"
checks={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in (orig,gamepath)}
rows=load("player_stats.json"); games=load("games.json")
cross=load("player_identity_crosswalk.json")
audit=load("player_identity_reconciliation_audit.json")
decisions=load("identity_audit_batch_04_decisions.json")
evidence=load("identity_audit_batch_04_source_evidence.json")
assert len(rows)==13196 and len(games)==437
assert cross["activated_person_merges"]==len(cross["merges"])==185
assert decisions["reviewed_pairs"]==20
byid=defaultdict(list)
for r in rows:byid[r["player_id"]].append(r)
existing={sid:m["canonical_id"] for m in cross["merges"] for sid in m["source_player_ids"]}
protected={sid for m in cross["owner_rejected_merge_candidates"] for sid in m["source_player_ids"]}
assert len(cross["owner_rejected_merge_candidates"])==29
j="cb-unlv-jason-sharman";ja="cb-unlv-ja-sharman";jo="cb-unlv-josh-sharman"
l="cb-liberty-nathan-keeter";lr="cb-lenoir-rhyne-nathaneal-keeter"
assert not ({j,ja,jo,l,lr}&(set(existing)|protected))
for id in (j,ja,jo,l,lr):
 assert evidence[id] and len(evidence[id])==len(byid[id]),id
 assert {r["game_id"] for r in evidence[id]}=={r["game_id"] for r in byid[id]}
assert len(byid[ja])==1 and byid[ja][0]["game_id"]=="cb-2022-02-25-unlv-san-diego-att0120"
assert byid[ja][0]["position"].lower()=="rf" and byid[ja][0]["pitching"] is None
assert len(byid[jo])==2 and all(r["pitching"] and not r["batting"] for r in byid[jo])
assert len(byid[j])==1 and byid[j][0]["batting"] and not byid[j][0]["pitching"]
assert len(byid[l])==1 and len(byid[lr])==1
assert {r["team"] for r in byid[l]}=={"Liberty"} and {r["team"] for r in byid[lr]}=={"Lenoir-Rhyne"}
def merge(name,canonical,ids,schools):
 rs=[r for pid in ids for r in byid[pid]]
 assert len(rs)==len({r["game_id"] for r in rs}),f"same game collision {name}"
 assert all(pid not in existing and pid not in protected for pid in ids),name
 return {"name":name,"canonical_id":canonical,"source_player_ids":ids,"schools":schools,
  "pairs":[{"team":team,"source_player_id":pid} for team,pid in sorted({(r["team"],r["player_id"]) for r in rs})],
  "source_rows":len(rs),"approval_batch":4}
m1=merge("Jason Sharman",j,[j,ja],["UNLV"])
m1["note"]="Source gamebook recorded Ja Sharman as right fielder; official UNLV roster identifies Jason as OF and Josh as LHP. Josh is a distinct person."
m15=merge("Nathaneal Keeter",lr,[lr,l],["Lenoir-Rhyne","Liberty"])
m15["note"]="Owner-approved Liberty Nathan Keeter / Lenoir-Rhyne Nathaneal Keeter transfer identity. Name variant preserved from original box scores."
assert decisions["results"][0]["source_id"]==ja and decisions["results"][0]["candidate_id"]==j
assert decisions["results"][1]["source_id"]==ja and decisions["results"][1]["candidate_id"]==jo
assert decisions["results"][14]["source_id"]==l and decisions["results"][14]["candidate_id"]==lr
for n in range(3,21):
 if n==15:continue
 pair=decisions["results"][n-1]
 assert pair["decision"]=="SEPARATE",n
 cross["owner_rejected_merge_candidates"].append({
  "name":pair["source_name"]+" / "+pair["candidate_name"],"schools":pair["schools"],
  "source_player_ids":[pair["source_id"],pair["candidate_id"]],
  "decision":"do_not_merge","confirmed_on":"2026-11-17","approval_batch":4,
  "note":"Owner instructed COMBINE only 1, 2, and 15; all other displayed Batch 4 pairs SEPARATE."
 })
decisions["results"][1]["decision"]="BLOCKED_SOURCE_VERIFIED_DIFFERENT_BROTHERS"
decisions["results"][1]["reason"]="Ja Sharman is a right fielder; Josh Sharman is a pitcher, and Jason and Josh are roster-listed brothers, not the same player."
cross["owner_rejected_merge_candidates"].append({
 "name":"Ja Sharman / Josh Sharman","schools":["UNLV","UNLV"],
 "source_player_ids":[ja,jo],"decision":"do_not_merge_source_verified","confirmed_on":"2026-11-17","approval_batch":4,
 "note":"Source right-field player is Jason Sharman, not Josh Sharman; two separate UNLV rostered brothers. User initially marked both candidates COMBINE, but source verification proved #2 unsafe."
})
cross["merges"] += [m1,m15]
cross["requested_person_merges"]+=2
cross["activated_person_merges"]+=2
assert cross["activated_person_merges"]==len(cross["merges"])==187
redirect={sid:m["canonical_id"] for m in cross["merges"] for sid in m["source_player_ids"]}
assert redirect[ja]==j and redirect.get(jo,jo)==jo
assert redirect[l]==lr
for blocked in cross["owner_rejected_merge_candidates"]:
 a,b=blocked["source_player_ids"]
 assert redirect.get(a,a)!=redirect.get(b,b),f"Protected separate pair merged: {blocked}"
# Browser merges scoped pairs. Prevent source duplicates on all seven million? 13k rows.
cor=load("player_name_corrections.json");fixes={}
for group in [cor,*cor["games"]]:
 for f in group["corrections"]:
  k=(group["game_id"],group["team"],f["source_player_id"])
  assert k not in fixes
  fixes[k]=f
aliases={(pair["team"],pair["source_player_id"]):m["canonical_id"] for m in cross["merges"] for pair in m["pairs"]}
byprofile=defaultdict(set)
for r in rows:
 fix=fixes.get((r["game_id"],r["team"],r["player_id"]))
 id=fix["canonical_player_id"] if fix else r["player_id"]
 profile=aliases.get((r["team"],id),id)
 assert r["game_id"] not in byprofile[profile],(profile,r["game_id"])
 byprofile[profile].add(r["game_id"])
assert sum(map(len,byprofile.values()))==13196
for num in (1,15):decisions["results"][num-1]["decision"]="COMBINE_APPLIED";decisions["results"][num-1]["applied"]=True
decisions["status"]="PASS_2_APPROVED_AND_17_SEPARATE_1_SOURCE_CONFLICT_BLOCKED"
decisions["applied_combinations"]=2
decisions["source_verified_conflict"]=1
decisions["protected_separate_decisions_added"]=18
audit["current_state"]["activated_person_merges"]=187
audit["current_state"]["requested_person_merges"]=187
audit["current_state"]["latest_review_batch"]={"batch":4,"approved_combinations_applied":2,"protected_separate_decisions_added":18,"blocked_source_conflict":"Ja Sharman (RF Jason) cannot be Josh Sharman (LHP)","source_game_rows_modified":0}
assert checks=={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in (orig,gamepath)}
save("player_identity_crosswalk.json",cross)
save("player_identity_reconciliation_audit.json",audit)
save("identity_audit_batch_04_decisions.json",decisions)
print(json.dumps({"status":"PASS","merges_added":2,"total_merges":187,"separate_protections":len(cross["owner_rejected_merge_candidates"]),"blocked_conflicting_approval":1,"source_stats_preserved":True}))

# Trigger authorized Batch 4 collision validation.
