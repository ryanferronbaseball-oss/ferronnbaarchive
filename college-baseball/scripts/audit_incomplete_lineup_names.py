#!/usr/bin/env python3
"""Read-only College Baseball lineup first-and-last-name audit."""
import json,re,unicodedata
from pathlib import Path
from collections import defaultdict,Counter
D=Path(__file__).resolve().parents[1]/"data"
load=lambda name:json.loads((D/name).read_text(encoding="utf8"))
rows=load("player_stats.json");games=load("games.json")
names=load("player_name_corrections.json");cross=load("player_identity_crosswalk.json")
batch2=load("identity_audit_batch_02_2026_11_17_approvals.json")
def normalized_name(s):return " ".join(re.sub(r"[^a-z0-9]+"," ",str(s).lower()).split())
prior_approved={(d["school"].lower(),normalized_name(d["source_name"])):d for d in batch2["decisions"] if d["decision"]=="COMBINE"}
assert len(games)==437 and len(rows)==13196
game_by_id={g["id"]:g for g in games}
fixes={}
for group in [names,*names["games"]]:
 for f in group["corrections"]:fixes[(group["game_id"],group["team"],f["source_player_id"])]=f
aliases={(p["team"],p["source_player_id"]):m for m in cross["merges"] for p in m["pairs"]}
def classify(name):
 s=str(name or "").strip()
 parts=s.split()
 if not parts:return "empty_name"
 low=unicodedata.normalize("NFKD",s).lower()
 if len(parts)>5 or re.search(r"\b(hbp|ibb|bf|fo|go|rbi|sac|avg|ab)\b",low):return "malformed_scorebook_text"
 core=[w for w in parts if w.strip(".,").lower() not in ("jr","sr","ii","iii","iv","v")]
 if len(core)<2:return "surname_only"
 head=core[0].strip(".,")
 if len(head)==1 and head.isalpha():return "first_initial_only"
 if re.match(r"(?i)^(jr|sr)\s*[,\.]",s):return "name_order_or_suffix_error"
 if len(head)==2 and head.isalpha() and (head.isupper() or head.lower() in {"ja","jd","jt","jp","jg","ej","rj","cj","aj","dj","jk","jb","tj","jw","mj"}):
  return "possible_abbreviated_first_name"
 return None
bygame=defaultdict(list)
for r in rows:
 if not r.get("batting") and not r.get("pitching"):continue
 issue=classify(r.get("player"))
 if not issue:continue
 k=(r["game_id"],r["team"],r["player_id"])
 fix=fixes.get(k)
 merge=aliases.get((r["team"],r["player_id"]))
 label=fix["player"] if fix else (merge["name"] if merge else None)
 approved=prior_approved.get((r["team"].lower(),normalized_name(r["player"])))
 status="resolved" if label and classify(label) is None else "approved_pending" if approved else "possible_short_first_name" if issue=="possible_abbreviated_first_name" else "needs_review"
 if approved and status=="approved_pending":label=approved["canonical_name"]
 bygame[r["game_id"]].append({"team":r["team"],"source_name":r["player"],"source_player_id":r["player_id"],"issue":issue,"role":"hitting + pitching" if r.get("batting") and r.get("pitching") else "hitting" if r.get("batting") else "pitching","status":status,"display_name":label,"resolution":"verified game correction" if fix else "approved identity merge" if merge else "owner-approved Batch 2 pending application" if approved else None})
output=[]
for gid,entries in bygame.items():
 g=game_by_id[gid]
 output.append({"game_id":gid,"date":g.get("date"),"away":g.get("away"),"home":g.get("home"),"source_url":g.get("source_url"),"needs_review":sum(e["status"]=="needs_review" for e in entries),"already_resolved":sum(e["status"]=="resolved" for e in entries),"approved_pending":sum(e["status"]=="approved_pending" for e in entries),"possible_short_first_names":sum(e["status"]=="possible_short_first_name" for e in entries),"entries":sorted(entries,key=lambda e:(e["status"]!="needs_review",e["team"],e["source_name"]))})
output.sort(key=lambda g:(-g["needs_review"],g["date"] or "",g["game_id"]))
allissues=Counter(e["issue"] for g in output for e in g["entries"])
unresolved=Counter(e["issue"] for g in output for e in g["entries"] if e["status"]=="needs_review")
report={"version":1,"method":"heuristic full-name audit of original gamebook source entries; both batting and pitching","source_game_count":len(games),"source_player_game_rows":len(rows),"games_with_source_short_names":len(output),"games_needing_review":sum(g["needs_review"]>0 for g in output),"source_name_issues":sum(allissues.values()),"unresolved_player_game_names":sum(unresolved.values()),"already_resolved_display_names":sum(g["already_resolved"] for g in output),"approved_pending_batch2_source_rows":sum(g["approved_pending"] for g in output),"optional_possible_short_first_names":sum(g["possible_short_first_names"] for g in output),"issue_counts":dict(allissues),"unresolved_issue_counts":dict(unresolved),"important":"Flags are NOT verified corrections. Original stats and games remain unmodified.","games":output}
(D/"lineup_full_name_audit_2026_11_17.json").write_text(json.dumps(report,indent=2,ensure_ascii=False)+"\n",encoding="utf8")
with (D/"lineup_full_name_audit_2026_11_17.md").open("w",encoding="utf8") as f:
 f.write("# College Baseball: Incomplete lineup first-and-last names\n\n")
 f.write("Read-only audit of 437 games and 13,196 player-game records. Hitting and pitching names. No changes to source box scores.\n\n")
 for key,label in [("games_with_source_short_names","Games containing abbreviated source names"),("games_needing_review","Games needing review"),("source_name_issues","Flagged player-game source names"),("unresolved_player_game_names","Names needing review"),("already_resolved_display_names","Names already resolved for display"),("approved_pending_batch2_source_rows","Previously approved Batch 2 names, pending activation"),("optional_possible_short_first_names","Two-letter first names, optional review only")]:
  f.write("- **"+label+":** "+str(report[key])+"\n")
 f.write("\n## Games with unresolved incomplete lineup names\n\n")
 for g in output:
  if not g["needs_review"]:continue
  f.write("### "+str(g["date"])+" — "+str(g["away"])+" at "+str(g["home"])+" ("+str(g["needs_review"])+" names)\n\n")
  f.write("Game ID: "+g["game_id"]+"\n\n")
  f.write("| Team | Source name | Issue | Role |\n|---|---|---|---|\n")
  for e in g["entries"]:
   if e["status"]!="needs_review":continue
   f.write("| "+e["team"]+" | "+e["source_name"]+" | "+e["issue"].replace("_"," ")+" | "+e["role"]+" |\n")
  f.write("\n")
 f.write("## Previously approved Batch 2 names, pending source mapping\n\n")
 for g in output:
  pending=[e for e in g["entries"] if e["status"]=="approved_pending"]
  if not pending:continue
  f.write("### "+str(g["date"])+" — "+str(g["away"])+" at "+str(g["home"])+"\n\n")
  for e in pending:f.write("- "+e["team"]+": "+e["source_name"]+" => "+e["display_name"]+" (APPROVED, not activated)\n")
  f.write("\n")
 f.write("## Two-letter first names (optional verification; may already be full names)\n\n")
 for g in output:
  maybe=[e for e in g["entries"] if e["status"]=="possible_short_first_name"]
  if not maybe:continue
  f.write("### "+str(g["date"])+" — "+str(g["away"])+" at "+str(g["home"])+"\n\n")
  for e in maybe:f.write("- "+e["team"]+": "+e["source_name"]+" ("+e["role"]+")\n")
  f.write("\n")
 f.write("## Already resolved source abbreviations\n\n")
 for g in output:
  done=[e for e in g["entries"] if e["status"]=="resolved"]
  if not done:continue
  f.write("### "+str(g["date"])+" — "+str(g["away"])+" at "+str(g["home"])+"\n\n")
  for e in done:f.write("- "+e["team"]+": "+e["source_name"]+" => "+e["display_name"]+" ("+str(e["resolution"])+")\n")
  f.write("\n")
print(json.dumps({k:report[k] for k in ("games_with_source_short_names","games_needing_review","source_name_issues","unresolved_player_game_names","already_resolved_display_names","approved_pending_batch2_source_rows","optional_possible_short_first_names","unresolved_issue_counts")}))

# Run current source lineup coverage scan.
