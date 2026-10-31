#!/usr/bin/env python3
"""Source-scoped identity crosswalk, college baseball attendance players.

Do not rewrite original official-scorebook player/team IDs or game stats.
Merge only when archive owner's exact named player matches one identified
person at EACH of two explicitly listed schools. Fail closed on name/ID
ambiguity, record collision, and source game identity errors.
"""
import argparse
import json
import re
import unicodedata
from collections import Counter,defaultdict
from pathlib import Path

DATA=Path(__file__).resolve().parents[1]/"data"
RULES=DATA/"player_identity_merges.json"
SOURCE=DATA/"player_stats.json"
GAMES=DATA/"games.json"
AUDIT=DATA/"player_identity_reconciliation_audit.json"
OUTPUT=DATA/"player_identity_crosswalk.json"

ALIASES={
    "nc state":"north carolina state","n c state":"north carolina state",
    "north carolina st":"north carolina state",
    "north carolina state university":"north carolina state",
    "byu":"brigham young","brigham young university":"brigham young",
    "uncw":"unc wilmington","u n c wilmington":"unc wilmington",
    "unc greensboro":"unc greensboro","uncg":"unc greensboro",
    "middle tennessee":"middle tennessee state","mtsu":"middle tennessee state",
    "middle tennessee st":"middle tennessee state",
    "southern mississippi":"southern miss","southern miss":"southern miss",
    "st marys":"saint marys","saint marys college":"saint marys",
    "st bonaventure":"saint bonaventure",
    "st johns":"saint johns","st louis":"saint louis",
    "saint louis university":"saint louis",
    "uc san diego":"uc san diego","ucsd":"uc san diego",
    "university of san diego":"san diego",
    "cal state northridge":"cal state northridge","csun":"cal state northridge",
    "csu northridge":"cal state northridge",
    "cal state bakersfield":"csu bakersfield","csu bakersfield":"csu bakersfield",
    "california state bakersfield":"csu bakersfield",
    "california baptist":"california baptist","cal baptist":"california baptist",
    "southern california":"usc",
    "old dominion university":"old dominion",
    "unc asheville":"unc asheville","north carolina asheville":"unc asheville",
    "virginia commonwealth":"vcu",
    "louisiana state":"lsu",
    "southeastern louisiana university":"southeastern louisiana",
    "point loma nazarene":"point loma",
    "point loma nazarene university":"point loma",
    "miami fl":"miami","miami florida":"miami",
    "west virginia university":"west virginia",
    "garden webb":"gardner webb",
}

def basic(s):
    s=unicodedata.normalize("NFKD",str(s or ""))
    s="".join(c for c in s if not unicodedata.combining(c)).lower()
    s=s.replace("&"," and ")
    return " ".join(re.sub(r"[^a-z0-9 ]"," ",s).split())

def school(s):
    value=basic(s)
    return ALIASES.get(value,value)

def name(s):
    s=str(s or "")
    if "," in s:
        pieces=s.split(",",1)
        if len(pieces)==2 and pieces[0].strip() and pieces[1].strip():
            s=pieces[1].strip()+" "+pieces[0].strip()
    # Remove punctuation so A.J. matches AJ, preserve full names.
    s=unicodedata.normalize("NFKD",s)
    s="".join(c for c in s if not unicodedata.combining(c)).lower()
    s=s.replace("jr.","jr").replace("ii.","ii")
    return "".join(c for c in s if c.isalnum())

def dump(path,object):
    path.write_text(json.dumps(object,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--apply",action="store_true",help="Create crosswalk after matching; leave original game and stats files unchanged")
    args=p.parse_args()
    proposals=json.loads(RULES.read_text(encoding="utf-8"))
    rows=json.loads(SOURCE.read_text(encoding="utf-8"))
    games=json.loads(GAMES.read_text(encoding="utf-8"))
    by_game={g["id"]:g for g in games}
    expected_count=proposals["expected_proposals"]
    if len(games)!=444 or len(rows)!=13184 or len(by_game)!=444 or len(proposals["rules"])!=expected_count:
        raise ValueError("Attended game, player line, or proposed transfer manifest count changed; review before reconciliation")
    if len({(r["game_id"],r["player_id"]) for r in rows})!=len(rows):
        raise ValueError("Duplicate original official player-game record")
    index=defaultdict(list)
    by_id=defaultdict(list)
    for r in rows:
        if r["game_id"] not in by_game or r["team"] not in (by_game[r["game_id"]]["away"],by_game[r["game_id"]]["home"]):
            raise ValueError("Original source player not aligned to attended game/team")
        k=(name(r["player"]),school(r["team"]))
        index[k].append(r)
        by_id[r["player_id"]].append(r)
    state=[]
    changes=[]
    used=set()
    rules_seen=set()
    for rule in proposals["rules"]:
        n=rule["name"]
        nkey=name(n)
        if not nkey or nkey in rules_seen:
            raise ValueError("Empty or duplicate full person in user transfer manifest")
        rules_seen.add(nkey)
        expected=[school(t) for t in rule["schools"]]
        if len(expected)!=2 or expected[0]==expected[1]:
            raise ValueError("Transfer needs two distinct approved schools: "+n)
        # Abbreviated official box-score names are admitted only by explicit
        # owner-approved source ID, school, game, and exact printed name.
        aliases={}
        for alias in rule.get("source_aliases",[]):
            aid=alias["source_player_id"]
            found=by_id.get(aid,[])
            if (aid in aliases or school(alias["team"]) not in expected or not found or
                any(r["team"]!=alias["team"] or
                    r["game_id"]!=alias["game_id"] or
                    r["player"]!=alias["source_player_name"] for r in found)):
                raise ValueError("Invalid source-scoped player-name alias: "+aid)
            aliases[aid]=alias
        side=[]
        for t in expected:
            matches=index.get((nkey,t),[])
            ids=sorted({r["player_id"] for r in matches})
            appearances=sorted({(r["game_id"],r["team"]) for r in matches})
            side.append({"normalized_school":t,"observed_teams":sorted({r["team"] for r in matches}),
                         "source_player_ids":ids,"source_player_rows":len(matches),
                         "games":len(appearances),
                         "seasons":sorted({by_game[r["game_id"]]["season"] for r in matches})})
        issue=None
        if not all(s["source_player_ids"] for s in side):
            issue="one_or_both_schools_not_in_attended_game_player_rows"
        elif any(len(s["source_player_ids"])!=1 for s in side):
            issue="ambiguous_multiple_source_player_ids_for_school"
        elif side[0]["source_player_ids"][0]==side[1]["source_player_ids"][0]:
            issue="already_same_source_player_id"
        else:
            ids=[s["source_player_ids"][0] for s in side]+list(aliases)
            if len(ids)!=len(set(ids)):
                raise ValueError("A source-name alias duplicates a full-name ID: "+n)
            if any(i in used for i in ids):
                issue="source_player_id_shared_with_another_proposal"
            elif any(school(r["team"]) not in expected or
                     (name(r["player"])!=nkey and i not in aliases)
                     for i in ids for r in by_id[i]):
                issue="source_id_also_used_for_other_name_or_unapproved_school"
            elif len({r["game_id"] for i in ids for r in by_id[i]})!=sum(len(by_id[i]) for i in ids):
                issue="duplicate_person_in_one_attended_game"
            else:
                used.update(ids)
                # Existing school-specific ID from the first owner-listed team
                # is the canonical ID; preserve old incoming URLs by redirect.
                canonical=ids[0]
                changes.append({
                    "name":n,"canonical_id":canonical,
                    **({"display_name":rule["display_name"]} if rule.get("display_name") else {}),
                    "source_player_ids":ids,
                    "schools":[s["observed_teams"][0] for s in side],
                    "pairs":[{"team":r["team"],"source_player_id":r["player_id"]}
                             for i in ids for r in by_id[i]],
                    "source_rows":sum(len(by_id[i]) for i in ids),
                })
        state.append({"sequence":rule["sequence"],"name":n,"approved_schools":rule["schools"],
                      "source_sides":side,
                      **({"verified_source_aliases":list(aliases.values())} if aliases else {}),
                      "status":"merge_ready" if issue is None else issue,
                      "note":rule.get("notes")})
    # De-duplicate aliases by (school,id) while preserving deterministic input.
    for m in changes:
        pairs=list({(a["team"],a["source_player_id"]) for a in m["pairs"]})
        m["pairs"]=[{"team":a,"source_player_id":b} for a,b in sorted(pairs)]
    originals=Counter(r["player_id"] for r in rows)
    audit={
        "status":"PASS","source_manifests":expected_count,"original_game_count":444,
        "original_player_game_rows":len(rows),
        "eligible_gamebooks":437,
        "ready_merges":len(changes),
        "not_ready":len(state)-len(changes),
        "pending_breakdown":dict(Counter(r["status"] for r in state if r["status"]!="merge_ready")),
        "preview":state,
        "source_id_unique_count_before":len(originals),
        "source_id_unique_count_after_simulated":len(originals)-sum(len(m["source_player_ids"])-1 for m in changes),
    }
    dump(AUDIT,audit)
    if args.apply:
        payload={
            "version":1,
            "kind":"college_baseball_source_scoped_person_identity_overrides",
            "source":"Original archive owner confirmed each multi-school person",
            "original_attendance_ids_preserved":444,
            "original_player_game_rows_preserved":len(rows),
            "requested_person_merges":expected_count,
            "activated_person_merges":len(changes),
            "pending_person_merges":len(state)-len(changes),
            "merge_policy":"Only listed pair of exact normalized person names and school-specific original source player IDs; all other IDs remain separate",
            "merges":changes,
        }
        dump(OUTPUT,payload)
    print(json.dumps({"audit":"PASS","requested":expected_count,"ready":len(changes),
        "pending":len(state)-len(changes),
        "reasons":audit["pending_breakdown"],"source_rows":len(rows)},indent=2))

if __name__=="__main__":
    main()
