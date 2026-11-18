#!/usr/bin/env python3
"""Create a reproducible queue of *unreviewed* college baseball name-identity candidates.

Read-only for source box scores, player stats, and existing identity registries.
Any proposed matching is only a suggestion: no automatic identities are merged.
"""
import json, re, unicodedata
from collections import defaultdict
from pathlib import Path

D=Path(__file__).resolve().parents[1]/"data"
load=lambda p:json.loads((D/p).read_text(encoding="utf8"))
rows=load("player_stats.json")
cross=load("player_identity_crosswalk.json")
names=load("player_name_corrections.json")
batch2=load("identity_audit_batch_02_2026_11_17_approvals.json")
def norm(v):
 s=unicodedata.normalize("NFKD",str(v or ""))
 return " ".join(re.sub(r"[^a-z0-9 ]"," ", "".join(c for c in s if not unicodedata.combining(c)).lower()).split())
def tokens(v):return norm(v).split()
def longname(v):
 t=tokens(v)
 return len(t)>=2 and len(t[0])>1 and len(t[-1])>1 and all(x.isalpha() for x in t)
def short_matches(alias, full):
 a,b=tokens(alias),tokens(full)
 if not a or not b or a[-1]!=b[-1] or norm(alias)==norm(full):return False
 if len(a)==1:return True # surname-only
 if len(a)==2 and len(a[0])==1:return b[0].startswith(a[0])
 if len(a)==2 and len(a[0])==2 and len(b[0])>=2:return b[0].startswith(a[0])
 if len(a)==3 and len(a[0])==1 and len(a[1])==1:return b[0].startswith(a[0]+a[1])
 return False

approved_names={(norm(d["school"]),norm(d["source_name"])) for d in batch2["decisions"]}
approved_names|={(norm(d["school"]),norm(d["canonical_name"])) for d in batch2["decisions"]}
reviewed_ids={p["source_player_id"] for m in cross["merges"] for p in m.get("pairs",[])}
reviewed_ids|={sid for m in cross["merges"] for sid in m["source_player_ids"]}
reviewed_ids|={sid for m in cross["owner_rejected_merge_candidates"] for sid in m["source_player_ids"]}
fixed=set()
for group in [names,*names["games"]]:
 fixed.update(c["source_player_id"] for c in group["corrections"])
reviewed_ids|=fixed
by_school=defaultdict(lambda:defaultdict(list))
for r in rows:
 by_school[norm(r["team"])][r["player_id"]].append(r)
candidates=[]
for school,players in by_school.items():
 fulls=[]
 for pid,ls in players.items():
  labels=sorted(set(x["player"] for x in ls))
  if pid in reviewed_ids:continue
  if any((school,norm(label)) in approved_names for label in labels):continue
  if len(labels)!=1:continue
  name=labels[0]
  if longname(name):fulls.append((pid,name,ls))
 for pid,ls in players.items():
  labels=sorted(set(x["player"] for x in ls))
  if pid in reviewed_ids or len(labels)!=1:continue
  alias=labels[0]
  if (school,norm(alias)) in approved_names or longname(alias):continue
  matched=[(fid,fname,fls) for fid,fname,fls in fulls if fid!=pid and short_matches(alias,fname)]
  if not matched:continue
  collisions=[m for m in matched if set(x["game_id"] for x in ls)&set(x["game_id"] for x in m[2])]
  result={"school":ls[0]["team"],"source_name":alias,"source_id":pid,"source_games":sorted(set(x["game_id"] for x in ls)),"candidates":[{"full_name":nm,"source_id":fid,"games":len(set(x["game_id"] for x in fls)),"same_game_collision":bool(set(x["game_id"] for x in ls)&set(x["game_id"] for x in fls))} for fid,nm,fls in matched],"status":"needs_owner_review" if len(matched)==1 and not collisions else "ambiguous_or_collision","source_rows":len(ls)}
  candidates.append(result)
# Additional candidate class: matching full names across different schools.
# This is deliberately a *review* queue, never evidence of a transfer.
by_full_name=defaultdict(list)
for school, players in by_school.items():
 for pid,ls in players.items():
  labels=sorted(set(x["player"] for x in ls))
  if pid in reviewed_ids or len(labels)!=1:continue
  label=labels[0]
  if not longname(label) or (school,norm(label)) in approved_names:continue
  by_full_name[norm(label)].append((school,pid,label,ls))
for normalized, group in by_full_name.items():
 schools={g[0] for g in group}
 if len(schools)<2:continue
 source_game_ids=[set(r["game_id"] for r in g[3]) for g in group]
 collision=any(source_game_ids[i]&source_game_ids[j] for i in range(len(group)) for j in range(i+1,len(group)))
 candidates.append({
  "kind":"cross_school_same_full_name",
  "school":" ↔ ".join(sorted({g[3][0]["team"] for g in group})),
  "source_name":group[0][2],
  "source_id":group[0][1],
  "source_games":sorted(set().union(*source_game_ids)),
  "candidates":[{"full_name":g[2],"school":g[3][0]["team"],"source_id":g[1],"games":len(set(r["game_id"] for r in g[3])),"same_game_collision":collision} for g in group],
  "status":"needs_owner_review" if not collision and len(group)==2 else "ambiguous_or_collision",
  "source_rows":sum(len(g[3]) for g in group)
 })
candidates.sort(key=lambda x:(x["status"]!="needs_owner_review",x["school"].lower(),x["source_name"].lower()))

out={"version":1,"purpose":"Identity review candidates only; never apply automatically","source_rows_scanned":len(rows),"existing_merges_preserved":len(cross["merges"]),"existing_do_not_merge_preserved":len(cross["owner_rejected_merge_candidates"]),"batch2_approved_pending":len(batch2["decisions"]),"candidates_found":len(candidates),"candidates":candidates}
(D/"identity_audit_batch_03_candidates.json").write_text(json.dumps(out,indent=2,ensure_ascii=False)+"\n",encoding="utf8")
with (D/"identity_audit_batch_03_review.md").open("w",encoding="utf8") as f:
 f.write("# College Baseball identity audit — Batch 3\n\n")
 f.write("These are proposed matches from raw rows, not approved merges. Batch 2 retains its 24 previous COMBINE approvals. No original statistics were changed.\n\n")
 f.write(f"Source player-game rows scanned: {len(rows)}. Candidate alias IDs: {len(candidates)}.\n\n")
 f.write("| # | Printed name | Full-name candidate | School | Same-game collision? | Decision |\n|---|---|---|---|---|---|\n")
 for i,c in enumerate(candidates[:35],1):
  desc=", ".join(x["full_name"] for x in c["candidates"])
  coll="YES" if any(x["same_game_collision"] for x in c["candidates"]) else "No"
  f.write(f'| {i} | {c["source_name"]} | {desc} | {c["school"]} | {coll} | REVIEW |\n')
print(json.dumps({"source_rows":len(rows),"new_candidates":len(candidates),"clean_single_matches":sum(c["status"]=="needs_owner_review" for c in candidates),"review_md":"college-baseball/data/identity_audit_batch_03_review.md"}))

# Refresh trigger: produce review candidates from source rows after workflow installation.
