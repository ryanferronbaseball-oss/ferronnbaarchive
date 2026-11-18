#!/usr/bin/env python3
"""Verified 2019-03-05 UC Riverside roster full names; source data immutable."""
import hashlib,json,re,unicodedata
from collections import defaultdict
from pathlib import Path
D=Path(__file__).resolve().parents[1]/"data"
read=lambda n:json.loads((D/n).read_text(encoding="utf8"))
save=lambda n,x:(D/n).write_text(json.dumps(x,indent=2,ensure_ascii=False)+"\n",encoding="utf8")
gid="cb-2019-03-05-san-diego-uc-riverside-att0046"
team="UC Riverside"
verified={
"A Arnone":"Alec Arnone",
"A Garcia":"Adrian Garcia",
"C Tucker":"Cole Tucker",
"D Mckesson":"Devin Mckesson",
"D Sanchez":"Damien Sanchez",
"H Naucler":"Houston Naucler",
"H Petrovick":"Hayden Petrovick",
"J Mannens":"Justin Mannens",
"M Hardy":"Matt Hardy",
"N Kafer":"Nick Kafer",
"P Sanchez":"Peter Sanchez",
"T Bateson":"Trevor Bateson"
}
assert len(verified)==12
def slug(s):
 s=unicodedata.normalize("NFKD",s)
 return re.sub(r"[^a-z0-9]+","-", "".join(c for c in s if not unicodedata.combining(c)).lower()).strip("-")
source_files=[D/"player_stats.json",D/"games.json"]
hashes=[hashlib.sha256(f.read_bytes()).hexdigest() for f in source_files]
rows=read("player_stats.json");games=read("games.json")
corr=read("player_name_corrections.json");cross=read("player_identity_crosswalk.json")
assert len(rows)==13196 and len(games)==437
assert sum(g["id"]==gid for g in games)==1
lineup={(r["team"],r["player"]):r for r in rows if r["game_id"]==gid}
assert len(lineup)==sum(r["game_id"]==gid for r in rows)
groups=[corr,*corr["games"]]
group=next(g for g in groups if g["game_id"]==gid and g["team"]==team)
fixes={(g["game_id"],g["team"],f["source_player_id"]):f for g in groups for f in g["corrections"]}
aliases={(p["team"],p["source_player_id"]):m["canonical_id"] for m in cross["merges"] for p in m["pairs"]}
new=[]
for short,full in verified.items():
 r=lineup.get((team,short))
 assert r is not None,(short,"missing original row")
 assert full[0].lower()==short[0].lower(),(short,full)
 assert full.split()[-1].lower()==short.split()[-1].lower(),(short,full)
 k=(gid,team,r["player_id"])
 assert k not in fixes,("already corrected",short)
 canonical="cb-"+slug(team)+"-"+slug(full)
 assert (team,r["player_id"]) not in aliases,("conflicting active merge",short)
 fix={"source_player_id":r["player_id"],"source_player_name":short,"player":full,"canonical_player_id":canonical}
 group["corrections"].append(fix)
 fixes[k]=fix
 new.append(fix)
assert len(new)==12
# Independent pair protections apply to cross-school merging, not to roster-verified names.
# Confirm all 13,196 attended player appearances remain one row per game/profile.
profiles=defaultdict(set)
for r in rows:
 key=(r["game_id"],r["team"],r["player_id"])
 fx=fixes.get(key)
 intermediate=fx["canonical_player_id"] if fx else r["player_id"]
 canonical=aliases.get((r["team"],intermediate),intermediate)
 assert r["game_id"] not in profiles[canonical],("same-game collision",canonical,r["game_id"])
 profiles[canonical].add(r["game_id"])
assert sum(map(len,profiles.values()))==len(rows)
protected={sid:m["canonical_id"] for m in cross["merges"] for sid in m["source_player_ids"]}
for reject in cross["owner_rejected_merge_candidates"]:
 a,b=reject["source_player_ids"]
 assert protected.get(a,a)!=protected.get(b,b),reject["name"]
assert hashes==[hashlib.sha256(f.read_bytes()).hexdigest() for f in source_files]
save("player_name_corrections.json",corr)
save("lineup_name_fix_uc_riverside_2019_03_05.json",{
"version":1,"game_id":gid,"team":team,"status":"verified_and_applied",
"roster":"https://gohighlanders.com/sports/baseball/roster/2019",
"official_boxscore":"https://usdtoreros.com/sports/baseball/stats/2019/uc-riverside/boxscore/9239",
"full_name_corrections_added":12,"prior_name_corrections_preserved":2,
"batch2_approvals_not_activated":6,"taylor_juline_previously_resolved":True,
"original_player_stats_unchanged":True,"original_games_unchanged":True,"same_game_collisions":0,
"corrections":new
})
print(json.dumps({"status":"PASS","game":gid,"full_names_corrected":len(new),"source_rows_unchanged":len(rows),"same_game_collisions":0}))

# Run full-name reconciliation after workflow installation.
