#!/usr/bin/env python3
"""Replace the incorrectly matched 2017-09-02 opener with the attended nightcap.
Run in a clean checkout; publish only after all downstream checks pass.
"""
import collections, json, pathlib, concurrent.futures
import import_official as imp
import import_decisions as dec
import audit_witnessed_hitter_milestones as hit
import audit_witnessed_pitcher_milestones as pitch
D=imp.DATA
OLD, NEW, AID=490565,492125,72
DATE="2017-09-02"
def read(name): return json.loads((D/name).read_text())
def write(name,obj): imp.write_json(name,obj)
def old(x): return isinstance(x,dict) and (str(x.get("game_pk"))==str(OLD) or str(x.get("attendance_id"))==str(AID))
def main():
    attendance=read("attendance.json")
    games=read("games.json")
    a=next(x for x in attendance if x["attendance_id"]==AID)
    original=next(x for x in games if x["attendance_id"]==AID)
    assert original["game_pk"] in (OLD,NEW) and a["date"]==DATE
    matches=[g for g in imp.schedule(DATE) if g["gamePk"]==NEW]
    assert len(matches)==1
    g=matches[0]
    assert g["gameNumber"]==2 and g["teams"]["away"]["team"]["id"]==119 and g["teams"]["home"]["team"]["id"]==135
    assert g["teams"]["away"]["score"]==2 and g["teams"]["home"]["score"]==7
    a.update(game_pk=NEW,away_score=2,home_score=7,source_note="Attended game 2 of split doubleheader; confirmed by archive owner.")
    game,rows,plays=imp.enrich(imp.game_data(a,g))
    assert game["stat_status"]=="verified" and game["scoring_status"]=="verified" and rows and plays
    assert all(r["game_pk"]==NEW and r["attendance_id"]==AID for r in rows)
    assert sum(x["away"] or 0 for x in game["innings"])==2
    assert sum(x["home"] or 0 for x in game["innings"])==7
    for side in ("away","home"):
        assert set(r["batting_slot"] for r in rows if r["side"]==side and r["batting_slot"])==set(range(1,10))
    pk,decision=dec.decisions(game)
    assert pk==str(NEW) and decision["status"]=="verified"
    assert decision["winner"]["name"]=="Buddy Baumann" and decision["loser"]["name"]=="Yu Darvish" and not decision.get("save")
    allrows=read("player_stats.json")
    removed=[r for r in allrows if old(r)]
    assert removed
    allrows=[r for r in allrows if not old(r)]+rows
    allrows.sort(key=lambda r:r["attendance_id"])
    games=[game if x["attendance_id"]==AID else x for x in games]
    assert len(games)==len(attendance)==len({x["game_pk"] for x in games})==131
    assert not any(r["game_pk"]==OLD for r in allrows)
    scoring=read("scoring_plays.json");scoring.pop(str(OLD),None);scoring[str(NEW)]=plays
    decisions=read("decisions.json");decisions.pop(str(OLD),None);decisions[str(NEW)]=decision
    names={r["name"]:r["player_id"] for r in rows}
    def link(name): return "[["+str(names[name])+"|"+name+"]]"
    recap=read("game_recaps.json")
    recap[str(AID)]=[
        f"Los Angeles and San Diego traded runs in the first inning of the nightcap at Petco Park. {link('Justin Turner')} doubled home a run for the Dodgers before {link('Hector Sanchez')} tied it with a groundout. {link('Adrian Gonzalez')} put Los Angeles back ahead with a third-inning RBI single.",
        f"The Padres answered with four runs in the bottom of the third. {link('Carlos Asuaje')} homered, Sanchez singled in another run, and {link('Matt Szczur')} doubled home two more to make it 5–2. {link('Yu Darvish')} allowed five runs in three innings, and {link('Jordan Lyles')} gave up two runs in 4 1/3 innings in his Padres debut.",
        f"San Diego added two seventh-inning runs on singles by {link('Yangervis Solarte')} and {link('Jose Pirela') if 'Jose Pirela' in names else link('José Pirela')}. {link('Buddy Baumann')} earned the win with 1 2/3 scoreless innings. The Padres won 7–2 to complete the doubleheader sweep."
    ]
    registry=read("witnessed_milestones.json")
    removed_milestones=[m for m in registry["milestones"] if old(m)]
    registry["milestones"]=[m for m in registry["milestones"] if not old(m)]
    assert names["Jordan Lyles"]==543475
    registry["milestones"].append({"id":"mlb-2017-09-02-543475-padres-debut","player":"Jordan Lyles","player_id":543475,"team":"San Diego Padres","date":DATE,"type":"team_debut","title":"San Diego Padres debut","description":"Made his first MLB appearance for San Diego in Game 2 of the doubleheader, starting and allowing two runs in 4 1/3 innings.","opponent":"Los Angeles Dodgers","attendance_id":AID,"game_pk":NEW,"source_url":"https://www.mlb.com/player/jordan-lyles-543475","verified":True})
    registry["milestones"].sort(key=lambda m:m["date"])
    # Targeted screening using complete MLB career logs; keep new candidates separate
    # until doubleheader order and independent evidence are reviewed.
    candidates=[]; errors=[]
    def audit(r):
        found=[]
        for module,field in ((hit,"batting"),(pitch,"pitching")):
            if r.get(field):
                found.extend(module.analyze((str(r["player_id"]),{str(NEW):game})))
        return found
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
        jobs={pool.submit(audit,r):r for r in rows}
        for job in concurrent.futures.as_completed(jobs):
            try: candidates.extend(job.result())
            except Exception as exc: errors.append({"player":jobs[job]["name"],"error":str(exc)})
    # Remove only obsolete records from old audit outputs, retain other candidates.
    for path in sorted(D.glob("*milestone*audit_batch_*.json"))+sorted(D.glob("*team_debut*audit_batch_*.json"))+[D/"verified_hitter_milestone_candidates.json"]:
        if not path.exists(): continue
        obj=json.loads(path.read_text());changed=False
        for key in ("candidates","debut_candidates","verified_candidates"):
            if isinstance(obj.get(key),list):
                orig=obj[key];obj[key]=[x for x in orig if not old(x)]
                if len(orig)!=len(obj[key]):
                    changed=True
                    for count in ("candidate_count","verified_count"):
                        if count in obj: obj[count]=len(obj[key])
        if changed:
            obj["attendance_correction"]="Attendance 72 replaced with game 492125; see doubleheader_correction_20170902.json for targeted re-audit."
            write(path.name,obj)
    write("attendance.json",attendance);write("games.json",games);write("player_stats.json",allrows)
    write("scoring_plays.json",scoring);write("decisions.json",decisions);write("game_recaps.json",recap)
    write("witnessed_milestones.json",registry)
    report=read("import_report.json")
    report["player_rows"]=len(allrows)
    report["lineup_slot_rows"]=sum(r.get("batting_slot") is not None for r in allrows)
    report["attendance_correction_20170902"]={"attendance_id":AID,"game_pk":NEW,"previous_game_pk":OLD}
    write("import_report.json",report)
    write("doubleheader_correction_20170902.json",{"attendance_id":AID,"old_game_pk":OLD,"new_game_pk":NEW,"old_player_rows":len(removed),"new_player_rows":len(rows),"old_only_players":sorted(set(r["name"] for r in removed)-set(names)),"new_only_players":sorted(set(names)-set(r["name"] for r in removed)),"removed_milestones":[m["title"]+" — "+m["player"] for m in removed_milestones],"added_verified_milestone":"Jordan Lyles — Padres debut","new_career_candidates":candidates,"audit_errors":errors,"source":"https://www.mlb.com/gameday/492125","review_source":"https://www.baseball-reference.com/boxes/SDN/SDN201709022.shtml"})
    print("Core correction staged:",len(rows),"player rows;",len(plays),"scoring plays;",len(candidates),"career candidates;",len(errors),"audit errors")
if __name__=="__main__":main()
