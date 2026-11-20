#!/usr/bin/env python3
"""Candidate-only witnessed MLB pitching milestones. Never publishes milestones."""
import argparse, collections, concurrent.futures, json, pathlib, time, urllib.parse, urllib.request

DATA = pathlib.Path(__file__).resolve().parents[1] / "data"
BASE = "https://statsapi.mlb.com/api/v1/people/"
METRICS = {"wins": ("wins", 50), "saves": ("saves", 50), "strikeouts": ("strikeOuts", 500)}

def fetch(url):
    for attempt in range(5):
        try:
            request = urllib.request.Request(url, headers={"User-Agent": "CourtsideArchivePitcherMilestoneAudit/1.0"})
            with urllib.request.urlopen(request, timeout=40) as response:
                return json.load(response)
        except Exception:
            if attempt == 4:
                raise
            time.sleep(2 * (attempt + 1))

def stats(pid, kind, season=None):
    params = {"stats": kind, "group": "pitching", "sportIds": 1}
    if season is not None:
        params["season"] = season
    payload = fetch(BASE + str(pid) + "/stats?" + urllib.parse.urlencode(params))
    if "stats" not in payload:
        raise ValueError("Missing stats for player " + str(pid) + " (" + kind + ")")
    return [s for block in payload["stats"] for s in block.get("splits", [])]

def value(row, key):
    raw = (row.get("stat") or {}).get(key, 0)
    return int(raw or 0)

def analyze(item):
    pid, attended = item
    years = sorted({int(g["date"][:4]) for g in attended.values()})
    yearly = stats(pid, "yearByYear")
    # Aggregate per season across teams; ignore non-MLB splits and avoid double counting.
    totals = collections.defaultdict(lambda: collections.defaultdict(int))
    grouped = collections.defaultdict(list)
    for split in yearly:
        season = split.get("season")
        if season and str(season).isdigit():
            grouped[int(season)].append(split)
    for year, entries in grouped.items():
        # MLB returns a season total alongside team-level splits for traded players.
        # Prefer the aggregate row; summing all rows doubles career totals.
        aggregates = [entry for entry in entries if not (entry.get("team") or {}).get("id")]
        selected = aggregates[:1] if aggregates else entries
        for split in selected:
            for metric, (key, _) in METRICS.items():
                totals[year][metric] += value(split, key)
    candidates = []
    for year in years:
        logs = stats(pid, "gameLog", year)
        logs = [s for s in logs if (s.get("game") or {}).get("gamePk") and s.get("date")]
        logs.sort(key=lambda s: (s["date"], int((s["game"])["gamePk"])))
        # Same-day doubleheaders: gamePk ordering is not reliable; flag for verification.
        same_day_counts = collections.Counter(s["date"] for s in logs)
        seen_pks = set()
        running = {m: sum(totals[y][m] for y in totals if y < year) for m in METRICS}
        season_log_totals = {m: 0 for m in METRICS}
        for split in logs:
            pk = int(split["game"]["gamePk"])
            if pk in seen_pks:
                raise ValueError("Duplicate gamePk in pitching game log: " + str(pk))
            seen_pks.add(pk)
            before = dict(running)
            for metric, (key, step) in METRICS.items():
                delta = value(split, key)
                if delta < 0:
                    raise ValueError("Negative game statistic for " + metric)
                running[metric] += delta
                season_log_totals[metric] += delta
                if str(pk) not in attended:
                    continue
                thresholds = [1] + list(range(step, running[metric] + 1, step))
                for target in thresholds:
                    if before[metric] < target <= running[metric]:
                        game = attended[str(pk)]
                        candidates.append({
                            "type": metric, "milestone": target, "player_id": str(pid),
                            "date": split["date"], "game_pk": pk,
                            "attendance_id": game.get("attendance_id"),
                            "team": (split.get("team") or {}).get("name"),
                            "game_stat": delta, "career_before_game": before[metric],
                            "career_after_game": running[metric],
                            "same_day_doubleheader": same_day_counts[split["date"]] > 1,
                            "source_url": BASE + str(pid) + "/stats?stats=gameLog&group=pitching&season=" + str(year),
                            "status": "candidate_needs_independent_verification"
                        })
        # Never accept a season where the logs and season totals disagree.
        for metric in METRICS:
            expected = totals[year][metric]
            if season_log_totals[metric] != expected:
                raise ValueError(f"{year} {metric}: game logs sum {season_log_totals[metric]}, yearByYear sum {expected}")
    return candidates

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--batch-size", type=int, default=100)
    args = parser.parse_args()
    if args.batch_size != 100:
        parser.error("Exactly 100 players per batch required")
    games = json.loads((DATA / "games.json").read_text())
    rows = json.loads((DATA / "player_stats.json").read_text())
    by_game = {str(g["game_pk"]): g for g in games if g.get("game_pk")}
    players = collections.defaultdict(dict)
    for row in rows:
        pid, pk = row.get("player_id"), row.get("game_pk")
        if pid and str(pk) in by_game:
            players[str(pid)][str(pk)] = by_game[str(pk)]
    # All witnessed players are screened; non-pitchers simply have no pitching splits. 
    ids = sorted(players, key=lambda pid: (-len(players[pid]), int(pid)))
    total = (len(ids) + 99) // 100
    print(f"Auditing {len(ids)} MLB pitching participants in {total} batches", flush=True)
    for index in range(total):
        chunk = ids[index * 100:(index + 1) * 100]
        candidates, errors = [], []
        with concurrent.futures.ThreadPoolExecutor(max_workers=6) as pool:
            futures = {pool.submit(analyze, (pid, players[pid])): pid for pid in chunk}
            for future in concurrent.futures.as_completed(futures):
                try:
                    candidates.extend(future.result())
                except Exception as exc:
                    errors.append({"player_id": futures[future], "error": str(exc)})
        candidates.sort(key=lambda c: (c["date"], c["game_pk"], c["player_id"], c["type"], c["milestone"]))
        output = {"audit_scope": "MLB career pitching milestones witnessed", "batch_number": index + 1,
                  "batch_size": 100, "total_players": len(ids), "players_in_batch": len(chunk),
                  "candidate_count": len(candidates), "candidates": candidates, "errors": errors,
                  "complete": not errors, "publication_status": "candidate_only"}
        path = DATA / f"witnessed_pitcher_milestone_audit_batch_{index+1:03d}.json"
        path.write_text(json.dumps(output, indent=2) + "\n")
        print(f"Batch {index+1}/{total}: {len(chunk)} players, {len(candidates)} candidates, {len(errors)} errors", flush=True)
        if errors:
            raise RuntimeError(f"Batch {index+1} incomplete: {len(errors)} player errors; no silent skips")
    print("All pitcher milestone candidate batches completed", flush=True)

if __name__ == "__main__":
    main()
