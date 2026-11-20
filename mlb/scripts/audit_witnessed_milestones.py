#!/usr/bin/env python3
"""Audit attended MLB games for debut and team-debut candidates using MLB StatsAPI.
Outputs candidates for manual verification; does not automatically publish them.
"""
import json, urllib.request, time, pathlib, collections, argparse
ROOT=pathlib.Path(__file__).resolve().parents[1]
DATA=ROOT/"data"
def load(name):
    return json.loads((DATA/name).read_text())
def api(url):
    for attempt in range(3):
        try:
            with urllib.request.urlopen(urllib.request.Request(url,headers={"User-Agent":"CourtsideArchiveMilestoneAudit/1.0"}),timeout=25) as r:
                return json.load(r)
        except Exception:
            if attempt==2:return {}
            time.sleep(1+attempt)
def main():
    games=load("games.json")
    rows=load("player_stats.json")
    attended={str(g.get("game_pk")):g for g in games if g.get("game_pk")}
    player_games=collections.defaultdict(list)
    for row in rows:
        game=attended.get(str(row.get("game_pk")))
        if not game or not row.get("player_id"):continue
        player_games[str(row["player_id"])].append((game,row))
    candidates=[]
    parser=argparse.ArgumentParser(description='Audit 100 MLB players per batch')
    parser.add_argument('--batch',type=int,default=1,help='1-based batch number')
    args=parser.parse_args()
    if args.batch<1:parser.error('--batch must be >= 1')
    all_ids=sorted(player_games,key=lambda pid:(-len({str(g['game_pk']) for g,_ in player_games[pid]}),int(pid)))
    ids=all_ids[(args.batch-1)*100:args.batch*100]
    for start in range(0,len(ids),50):
        batch=ids[start:start+50]
        people=api("https://statsapi.mlb.com/api/v1/people?personIds="+",".join(batch)).get("people",[])
        byid={str(p["id"]):p for p in people}
        for pid in batch:
            person=byid.get(pid,{})
            debut=person.get("mlbDebutDate")
            for game,row in player_games[pid]:
                if debut==game["date"]:
                    candidates.append({"type":"mlb_debut","player_id":pid,"player":person.get("fullName",row.get("name")),"date":debut,"attendance_id":game["attendance_id"],"game_pk":game["game_pk"],"team":row.get("team"),"evidence":"MLB StatsAPI person.mlbDebutDate equals attended game date","source_url":"https://statsapi.mlb.com/api/v1/people/"+pid,"status":"candidate_needs_game_participation_check"})
        time.sleep(.2)
    # A player appearing for the first time in THIS archive is not necessarily a team debut.
    # Do not infer team debuts, first hits, HRs or career landmarks from partial attendance logs.
    output={"audit_scope":"MLB games attended","batch_number":args.batch,"batch_size":100,"total_players":len(all_ids),"games_total":len(games),"matched_game_pks":len(attended),"player_ids_in_boxscores":len(ids),"debut_candidates":candidates,"limitations":["Debut date matches require individual boxscore verification when multiple games occur that day.","Team debuts require complete career team game logs.","First hits/home runs and numeric career milestones require historical career cumulative logs.","This output is not the published verified milestone list."]}
    dest=DATA/f"witnessed_milestone_audit_batch_{args.batch:03d}.json"
    dest.write_text(json.dumps(output,indent=2)+"\n")
    print(f"Checked {len(ids)} players, {len(attended)} matched games, {len(candidates)} MLB debut candidates. Output: {dest}")
if __name__=="__main__":main()
