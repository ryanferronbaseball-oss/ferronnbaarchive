#!/usr/bin/env python3
"""Apply 2024-02-19 Marshall @ Charleston official-roster verified names.

Preserve raw source stats, original gamebox rows and unrelated games. Not an
identity merge: only game-scoped original player IDs / display names.
"""
import json,hashlib,re,unicodedata
from collections import defaultdict
from pathlib import Path
D=Path(__file__).resolve().parents[1]/"data"
read=lambda p:json.loads((D/p).read_text(encoding="utf8"))
save=lambda p,v:(D/p).write_text(json.dumps(v,indent=2,ensure_ascii=False)+"\n",encoding="utf8")
gid="cb-2024-02-19-marshall-college-of-charleston-att0231"
rosters={
 "College of Charleston":{
  "A. Duval":"Andrew Duval",
  "A. Neaves":"Avery Neaves",
  "D. Johnson":"Dylan Johnson",
  "D. Pendergra":"Dariyan Pendergrass",
  "H. Garner":"Hogan Garner",
  "J. Bradford":"Jeb Bradford",
  "K. Madden":"Kevin Madden",
  "L. Wood":"Luke Wood",
  "T. Harlan":"Trotter Harlan",
  "T. Sorrentin":"Tyler Sorrentino",
  "W. Baumhofer":"Will Baumhofer",
 },
 "Marshall":{
  "B. Blevins":"Bryce Blevins",
  "C. Heiner":"Chad Heiner",
  "C. Kaiser":"Caden Kaiser",
  "C. Smith":"Calin Smith",
  "E. Leon":"Eddie Leon",
  "E. Vogelsong":"Elijah Vogelsong",
  "G. Cabrera":"Gabriel Cabrera",
  "G. Ferraro":"Gio Ferraro",
  "J. Firestone":"Jack Firestone",
  "K. Peralta":"Kebler Peralta",
  "N. Jodway":"Nick Jodway",
  "T. Hondras":"Tre Hondras",
 }
}
assert sum(map(len,rosters.values()))==23
rowsfile=D/"player_stats.json";gamesfile=D/"games.json"
before=[hashlib.sha256(f.read_bytes()).hexdigest() for f in [rowsfile,gamesfile]]
rows=read("player_stats.json");games=read("games.json")
names=read("player_name_corrections.json");cross=read("player_identity_crosswalk.json")
assert len(games)==437 and len(rows)==13196
assert len([g for g in games if g["id"]==gid])==1
current={(r["team"],r["player"]):r for r in rows if r["game_id"]==gid}
assert len(current)==len([r for r in rows if r["game_id"]==gid]),"Duplicate source names in game"
fixes={(g["game_id"],g["team"],f["source_player_id"]):f for g in [names,*names["games"]] for f in g["corrections"]}
redirect={sid:m["canonical_id"] for m in cross["merges"] for sid in m["source_player_ids"]}
protected={sid for m in cross["owner_rejected_merge_candidates"] for sid in m["source_player_ids"]}
def slug(s):
 s=unicodedata.normalize("NFKD",s)
 s="".join(ch for ch in s if not unicodedata.combining(ch))
 return re.sub(r"[^a-z0-9]+","-",s.lower()).strip("-")
added=[]
for team,dict_names in rosters.items():
 group=next((g for g in names["games"] if g["game_id"]==gid and g["team"]==team),None)
 assert group,"Existing correction group not found for "+team
 for source,full in dict_names.items():
  row=current.get((team,source))
  assert row and row["player_id"] not in protected,(team,source)
  key=(gid,team,row["player_id"])
  assert key not in fixes,key
  canonical="cb-"+slug(team)+"-"+slug(full)
  assert not (row["player_id"] in redirect and redirect[row["player_id"]]!=canonical),(team,source)
  assert (full.split()[0][0].lower()==source[0].lower()),(source,full)
  assert (full.split()[-1].lower().startswith(source.split()[-1].lower().rstrip(".")) or source=="D. Pendergra"),(source,full)
  group["corrections"].append({"source_player_id":row["player_id"],"source_player_name":source,"player":full,"canonical_player_id":canonical})
  added.append({"team":team,"source_player_name":source,"full_name":full,"source_player_id":row["player_id"],"canonical_player_id":canonical,"role":"hitting" if row.get("batting") else "pitching"})
assert len(added)==23
# Verify no existing correction/merge maps 2 source rows into one appearance.
correction_ids={(g["game_id"],g["team"],f["source_player_id"]):f["canonical_player_id"] for g in [names,*names["games"]] for f in g["corrections"]}
assert len(correction_ids)==sum(len(g["corrections"]) for g in [names,*names["games"]])
aliases={(p["team"],p["source_player_id"]):m["canonical_id"] for m in cross["merges"] for p in m["pairs"]}
ids_by_game=defaultdict(set)
for r in rows:
 key=(r["game_id"],r["team"],r["player_id"])
 interim=correction_ids.get(key,r["player_id"])
 actual=aliases.get((r["team"],interim),interim)
 assert actual not in ids_by_game[r["game_id"]],("Duplicate identity in same game",r["game_id"],actual)
 ids_by_game[r["game_id"]].add(actual)
assert sum(map(len,ids_by_game.values()))==len(rows)
assert [hashlib.sha256(f.read_bytes()).hexdigest() for f in [rowsfile,gamesfile]]==before
save("player_name_corrections.json",names)
save("lineup_name_fix_marshall_charleston_2024_02_19.json",{
 "version":1,"game_id":gid,"date":"2024-02-19","applied_verified_full_names":len(added),
 "status":"verified_and_applied","sources":{
  "marshall_roster":"https://herdzone.com/sports/baseball/roster/2024",
  "charleston_roster":"https://cofcsports.com/sports/baseball/roster/2024",
  "official_game_box_score":"https://cofcsports.com/sports/baseball/stats/2024/marshall/boxscore/11657"
 },
 "already_resolved":["Cole Mathis","Owen Ayers"],
 "approved_batch2_pending":["AJ Havrilla"],
 "source_stats_rewritten":False,"same_game_collisions":0,"corrections":added
})
print(json.dumps({"status":"PASS","corrections":len(added),"raw_source_rows_unchanged":len(rows),"same_game_collisions":0,"already_resolved":2,"preapproved_pending":1}))
