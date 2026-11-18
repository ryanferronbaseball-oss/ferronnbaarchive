#!/usr/bin/env python3
"""Batch 4: new potential identities, NEVER auto-merge. Conservative surname/initial and spelling review."""
import json,re,unicodedata
from collections import defaultdict
from difflib import SequenceMatcher
from pathlib import Path
D=Path(__file__).resolve().parents[1]/"data"
read=lambda s:json.loads((D/s).read_text(encoding="utf8"))
rows=read("player_stats.json")
cross=read("player_identity_crosswalk.json")
corrections=read("player_name_corrections.json")
b2=read("identity_audit_batch_02_2026_11_17_approvals.json")
def norm(s):
 s=unicodedata.normalize("NFKD",str(s or "")).lower()
 return " ".join(re.sub(r"[^a-z0-9 ]"," ","".join(c for c in s if not unicodedata.combining(c))).split())
def parts(s):return norm(s).split()
def match(x,y):
 a,b=parts(x),parts(y)
 if len(a)<2 or len(b)<2 or norm(x)==norm(y):return False
 if a[-1]!=b[-1]:return False
 if a[0]==b[0]:return True
 if a[0][0]==b[0][0] and (min(len(a[0]),len(b[0]))<=2):return True
 if a[0][0]==b[0][0] and SequenceMatcher(None,a[0],b[0]).ratio()>=0.75:return True
 # Nicknames sometimes have distinct initials; DO NOT assume match unless nickname is established.
 return False
skip={sid for m in cross["merges"] for sid in m["source_player_ids"]}
skip|={sid for m in cross["owner_rejected_merge_candidates"] for sid in m["source_player_ids"]}
for g in [corrections,*corrections["games"]]:
 skip|={f["source_player_id"] for f in g["corrections"]}
batch2ids={norm(d["source_name"]) for d in b2["decisions"]}|{norm(d["canonical_name"]) for d in b2["decisions"]}
groups=defaultdict(list)
for r in rows:
 if r["player_id"] in skip:continue
 groups[(r["team"],r["player_id"])].append(r)
entries=[]
for (school,pid),rr in groups.items():
 labels={r["player"] for r in rr}
 if len(labels)!=1:continue
 name=next(iter(labels))
 if norm(name) in batch2ids:continue
 if len(parts(name))<2:continue
 entries.append({"name":name,"school":school,"id":pid,"games":{r["game_id"] for r in rr}})
# group by surname, then compare distinct IDs with first-name abbreviation/similarity
by_last=defaultdict(list)
for entry in entries:by_last[parts(entry["name"])[-1]].append(entry)
results=[]
for last,subset in by_last.items():
 if len(subset)>24:continue
 for i,a in enumerate(subset):
  for b in subset[i+1:]:
   if not match(a["name"],b["name"]):continue
   # skip same spelling with separate school; these were covered in batch3
   if norm(a["name"])==norm(b["name"]) and norm(a["school"])!=norm(b["school"]):continue
   coll=bool(a["games"]&b["games"])
   score=2 if norm(a["school"])==norm(b["school"]) else 1
   # Names with a single-letter abbreviation remain candidates requiring owner verification
   results.append({"source_name":a["name"],"candidate_name":b["name"],"source_id":a["id"],"candidate_id":b["id"],"school_a":a["school"],"school_b":b["school"],"game_count_a":len(a["games"]),"game_count_b":len(b["games"]),"same_game_collision":coll,"priority":score,"status":"OWNER_REVIEW_ONLY"})
results.sort(key=lambda r:(-r["priority"],r["same_game_collision"],r["school_a"],r["source_name"],r["candidate_name"]))
out={"version":1,"batch":4,"source_rows_scanned":len(rows),"total_candidates":len(results),"status":"review_only_no_merges_applied","exclusions":"Prior approved/rejected identity IDs and Batch 2 named approvals excluded","candidates":results}
(D/"identity_audit_batch_04_candidates.json").write_text(json.dumps(out,indent=2)+"\n",encoding="utf8")
with (D/"identity_audit_batch_04_review.md").open("w",encoding="utf8") as f:
 f.write("# College Baseball Batch 4 — fresh candidates\n\nSource-only possible matches, NOT verified identities. Do not combine without approval and source collision validation.\n\n")
 f.write(f"Scanned {len(rows)} player-game rows, found {len(results)} candidate pairs.\n\n")
 f.write("| # | First source name | Second source name | Schools | Collision | Decision |\n|---|---|---|---|---|---|\n")
 for i,r in enumerate(results[:40],1):
  f.write(f'| {i} | {r["source_name"]} | {r["candidate_name"]} | {r["school_a"]} / {r["school_b"]} | {"YES" if r["same_game_collision"] else "No"} | REVIEW |\n')
print(json.dumps({"candidates":len(results),"sample":results[:4]}))
