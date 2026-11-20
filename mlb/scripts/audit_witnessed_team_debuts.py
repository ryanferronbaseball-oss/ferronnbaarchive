#!/usr/bin/env python3
"""Discover MLB franchise debuts witnessed in attended games. Candidate-only, never publishes."""
import argparse, collections, concurrent.futures, json, pathlib, time, urllib.parse, urllib.request

DATA = pathlib.Path(__file__).resolve().parents[1] / "data"
BASE = "https://statsapi.mlb.com/api/v1/people/"
GROUPS = ("hitting", "pitching", "fielding")

def fetch(url):
    for attempt in range(4):
        try:
            req = urllib.request.Request(url, headers={"User-Agent":"CourtsideArchiveTeamDebutAudit/1.0"})
            with urllib.request.urlopen(req, timeout=35) as response:
                return json.load(response)
        except Exception:
            if attempt == 3:
                raise
            time.sleep(1.5 * (attempt + 1))

def splits(pid, kind, season=None):
    params = {"stats": kind, "group": ",".join(GROUPS), "sportIds": 1}
    if season is not None:
        params["season"] = season
    url = BASE + str(pid) + "/stats?" + urllib.parse.urlencode(params)
    result = fetch(url)
    if "stats" not in result:
        raise ValueError("Missing stats key for player " + str(pid))
    return [split for block in result["stats"] for split in block.get("splits", [])]

def analyze(item):
    pid, game_refs = item
    # Game logs provide both actual participation and the MLB franchise ID.
    years = sorted({int(g["date"][:4]) for g in game_refs})
    attended = {int(g["game_pk"]): g for g in game_refs}
    matching = []
    for year in years:
        for split in splits(pid, "gameLog", year):
            pk = (split.get("game") or {}).get("gamePk")
            team = split.get("team") or {}
            tid = team.get("id")
            if pk is not None and int(pk) in attended and tid:
                matching.append((split, attended[int(pk)]))
    if not matching:
        return []
    history = splits(pid, "yearByYear")
    # A franchise's first season must match the candidate season. A prior-season
    # team record excludes it even if the player first appears in this archive later.
    first_seasons = {}
    for split in history:
        team = split.get("team") or {}
        tid = team.get("id")
        year = split.get("season")
        if tid and year and str(year).isdigit():
            first_seasons[tid] = min(first_seasons.get(tid, 9999), int(year))
    results = []
    log_cache = {}
    for split, game in matching:
        team = split["team"]
        tid = team["id"]
        date = split.get("date")
        year = int(game["date"][:4])
        if first_seasons.get(tid, year) < year:
            continue
        if year not in log_cache:
            log_cache[year] = splits(pid, "gameLog", year)
        same_team = [x for x in log_cache[year] if (x.get("team") or {}).get("id") == tid and x.get("date")]
        if not same_team:
            continue
        first_date = min(x["date"] for x in same_team)
        if first_date != date:
            continue
        first_pks = {int(x["game"]["gamePk"]) for x in same_team if x["date"] == first_date and (x.get("game") or {}).get("gamePk")}
        # Same-day doubleheaders must be verified in phase 2.
        results.append({"type":"team_debut","player_id":str(pid),"date":date,"team_id":tid,"team":team.get("name"),"attendance_id":game.get("attendance_id"),"game_pk":game["game_pk"],"same_day_game_pks":sorted(first_pks),"source_url":BASE+str(pid)+"/stats?stats=gameLog&season="+str(year),"status":"candidate_needs_exact_first_game_verification"})
    unique = {(x["player_id"], x["team_id"], x["game_pk"]): x for x in results}
    return list(unique.values())

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--batch-size", type=int, default=100)
    args = parser.parse_args()
    if args.batch_size != 100:
        parser.error("This workflow requires batches of exactly 100 players")
    games = json.loads((DATA/"games.json").read_text())
    rows = json.loads((DATA/"player_stats.json").read_text())
    by_game = {str(g["game_pk"]):g for g in games if g.get("game_pk")}
    players = collections.defaultdict(dict)
    for row in rows:
        pid, pk = row.get("player_id"), row.get("game_pk")
        if pid and str(pk) in by_game:
            players[str(pid)][str(pk)] = by_game[str(pk)]
    ids = sorted(players, key=lambda pid:(-len(players[pid]), int(pid)))
    total = (len(ids)+99)//100
    print(f"Auditing {len(ids)} MLB players in {total} sequential batches", flush=True)
    for index in range(total):
        chunk = ids[index*100:(index+1)*100]
        candidates, errors = [], []
        with concurrent.futures.ThreadPoolExecutor(max_workers=6) as pool:
            tasks = {pool.submit(analyze, (pid, list(players[pid].values()))):pid for pid in chunk}
            for task in concurrent.futures.as_completed(tasks):
                pid = tasks[task]
                try:
                    candidates.extend(task.result())
                except Exception as exc:
                    errors.append({"player_id":pid,"error":str(exc)})
        candidates.sort(key=lambda x:(x["date"], x["player_id"], x["team_id"]))
        output = {"audit_scope":"MLB franchise/team debuts","batch_number":index+1,"batch_size":100,"total_players":len(ids),"players_in_batch":len(chunk),"candidate_count":len(candidates),"candidates":candidates,"errors":errors,"complete":not errors,"publication_status":"candidate_only"}
        path = DATA/f"witnessed_team_debut_audit_batch_{index+1:03d}.json"
        path.write_text(json.dumps(output, indent=2)+"\n")
        print(f"Batch {index+1}/{total}: {len(chunk)} players, {len(candidates)} candidates, {len(errors)} errors", flush=True)
        if errors:
            raise RuntimeError(f"Batch {index+1} incomplete: {len(errors)} player API errors; stopped rather than silently skipping players")
    print("All team debut candidate batches completed", flush=True)

if __name__ == "__main__":
    main()
