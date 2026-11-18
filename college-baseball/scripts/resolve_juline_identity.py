#!/usr/bin/env python3
"""Owner-confirmed T Juline -> Taylor Juline, never Tucker Juline.
Source game and statistics remain immutable. Fail on any source collision.
"""
import json,hashlib
from pathlib import Path
from collections import defaultdict
D=Path(__file__).resolve().parents[1]/"data"
read=lambda name:json.loads((D/name).read_text(encoding="utf-8"))
save=lambda name,obj:(D/name).write_text(json.dumps(obj,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
source=D/"player_stats.json";gamefile=D/"games.json"
before=[hashlib.sha256(p.read_bytes()).hexdigest() for p in [source,gamefile]]
rows=read("player_stats.json");games=read("games.json")
cross=read("player_identity_crosswalk.json")
audit=read("player_identity_reconciliation_audit.json")
batch=read("identity_audit_batch_03_decisions.json")
candidates=read("identity_audit_batch_03_candidates.json")
assert len(rows)==13196 and len(games)==437
a="cb-uc-riverside-t-juline";t="cb-uc-riverside-taylor-juline";other="cb-uc-riverside-tucker-juline"
gid="cb-2019-03-05-san-diego-uc-riverside-att0046"
assert batch["owner_decisions"]["UNSURE"]==["T Juline (UC Riverside)"]
candidate=next(c for c in candidates["candidates"] if c["source_id"]==a)
assert candidate["source_name"]=="T Juline" and candidate["source_games"]==[gid]
assert {c["source_id"] for c in candidate["candidates"]}=={t,other}
by_id=defaultdict(list)
for row in rows:by_id[row["player_id"]].append(row)
assert len(by_id[a])==1 and by_id[a][0]["game_id"]==gid and by_id[a][0]["team"]=="UC Riverside" and by_id[a][0]["player"]=="T Juline"
assert len(by_id[t])==3 and all(r["team"]=="UC Riverside" and r["player"]=="Taylor Juline" for r in by_id[t])
assert len(by_id[other])==1 and all(r["team"]=="UC Riverside" and r["player"]=="Tucker Juline" for r in by_id[other])
assert len({r["game_id"] for r in by_id[a]+by_id[t]})==4
existing={sid:m["canonical_id"] for m in cross["merges"] for sid in m["source_player_ids"]}
rejected={sid for m in cross["owner_rejected_merge_candidates"] for sid in m["source_player_ids"]}
assert not ({a,t,other}&(set(existing)|rejected))
cross["merges"].append({
 "name":"Taylor Juline","canonical_id":t,"source_player_ids":[t,a],
 "schools":["UC Riverside"],
 "pairs":[{"team":"UC Riverside","source_player_id":t},{"team":"UC Riverside","source_player_id":a}],
 "source_rows":4,"approval_batch":3,
 "note":"Attendee confirmed 2019-03-05 T Juline is Taylor, not Tucker. Single-game initial-only alias; historical box score unchanged."
})
cross["requested_person_merges"]+=1
cross["activated_person_merges"]+=1
assert cross["activated_person_merges"]==len(cross["merges"])==185
assert cross["pending_person_merges"]==0
# Restore single-source identity mapping, preserve Tucker and all protected separate pairs.
redirect={sid:m["canonical_id"] for m in cross["merges"] for sid in m["source_player_ids"]}
assert redirect[a]==t and redirect.get(other,other)==other
assert all(redirect.get(x["source_player_ids"][0],x["source_player_ids"][0])!=redirect.get(x["source_player_ids"][1],x["source_player_ids"][1]) for x in cross["owner_rejected_merge_candidates"])
assert len({r["game_id"] for r in by_id[a]+by_id[t]})==4
batch["owner_decisions"]["UNSURE"]=[]
batch["owner_decisions"]["COMBINE"].append("T Juline → Taylor Juline (UC Riverside, 2019-03-05)")
batch["applied"]=8
batch["source_rows_affected"]+=4
batch["resolved_followup"]={"name":"T Juline","canonical_name":"Taylor Juline","kept_separate":"Tucker Juline","source_game":gid,"identity_collision_count":0,"owner_confirmed":True,"source_game_modified":False}
audit["current_state"]["requested_person_merges"]=185
audit["current_state"]["activated_person_merges"]=185
audit["current_state"]["most_recent_merge"]={"name":"Taylor Juline","schools":["UC Riverside"],"combined_game_log_rows":4,"source_game":gid}
audit["current_state"]["latest_review_batch"].update({"approved_combinations":8,"new_merge_entries":8,"unresolved":None,"resolved_t_juline":"Taylor Juline","original_box_scores_modified":False})
assert before==[hashlib.sha256(p.read_bytes()).hexdigest() for p in [source,gamefile]]
save("player_identity_crosswalk.json",cross)
save("player_identity_reconciliation_audit.json",audit)
save("identity_audit_batch_03_decisions.json",batch)
print(json.dumps({"result":"PASS","canonical_profile":t,"merged_attendance_games":4,"tucker_separate":True,"protected_rejected":len(cross["owner_rejected_merge_candidates"]),"total_merges":185,"source_files_unchanged":True}))
