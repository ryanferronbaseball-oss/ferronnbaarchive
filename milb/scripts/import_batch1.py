#!/usr/bin/env python3
"""Verify and import Batch 1 MiLB games from MLB StatsAPI.

Match historical games by date, level, BOTH teams and final score. Do not
publish unverified player totals. MiLB outputs remain strictly under milb/data.
"""
import collections
import datetime
import json
import pathlib
import re
import time
import urllib.parse
import urllib.request

ROOT = pathlib.Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
API = "https://statsapi.mlb.com/api/v1"
HEADERS = {"User-Agent": "CourtsideArchive-MiLB/1.0", "Accept": "application/json"}
LEVEL = {"Triple-A": 11, "Double-A": 12, "High-A": 13, "Single-A": 14}
BATCH_DATES = {
    "2014-05-24", "2015-08-02", "2021-05-18", "2021-05-19",
    "2021-05-20", "2021-05-21", "2021-05-22", "2021-05-23",
    "2022-07-02", "2024-05-10",
}

def fetch(url):
    for attempt in range(4):
        try:
            req = urllib.request.Request(url, headers=HEADERS)
            with urllib.request.urlopen(req, timeout=35) as res:
                return json.load(res)
        except Exception:
            if attempt == 3:
                raise
            time.sleep(2 * (attempt + 1))

def normalized(name):
    return re.sub(r"[^a-z0-9]", "", str(name or "").lower())

def same_team(expected, actual):
    x, y = normalized(expected), normalized(actual)
    return x == y or (len(x) > 8 and len(y) > 8 and (x.endswith(y) or y.endswith(x)))

def schedule(date, sport_id):
    params = urllib.parse.urlencode({"date": date, "sportId": sport_id})
    url = API + "/schedule?" + params
    data = fetch(url)
    return [g for d in data.get("dates", []) for g in d.get("games", [])]

def pick(entry, candidates, used):
    matches = []
    for g in candidates:
        if g.get("gamePk") in used:
            continue
        if g.get("status", {}).get("abstractGameState") != "Final":
            continue
        teams = g.get("teams", {})
        home, away = teams.get("home", {}), teams.get("away", {})
        if not same_team(entry["home_team"], home.get("team", {}).get("name")):
            continue
        if not same_team(entry["away_team"], away.get("team", {}).get("name")):
            continue
        if home.get("score") != entry["home_score"] or away.get("score") != entry["away_score"]:
            continue
        matches.append(g)
    if len(matches) == 1:
        return matches[0], None
    if len(matches) > 1:
        return None, "ambiguous: multiple official schedule matches"
    return None, "no official schedule match for both teams and final score"

def get_number(source, key):
    value = source.get(key)
    return int(value) if value is not None and str(value).strip() != "" else None

def batting(source):
    if not source:
        return None
    mapping = {
        "ab": "atBats", "pa": "plateAppearances", "r": "runs", "h": "hits",
        "doubles": "doubles", "triples": "triples", "hr": "homeRuns",
        "rbi": "rbi", "bb": "baseOnBalls", "so": "strikeOuts",
        "hbp": "hitByPitch", "sb": "stolenBases", "cs": "caughtStealing",
        "sf": "sacFlies", "sh": "sacBunts",
    }
    return {dest: get_number(source, src) for dest, src in mapping.items()}

def pitching(source):
    if not source:
        return None
    mapping = {
        "h": "hits", "r": "runs", "er": "earnedRuns", "bb": "baseOnBalls",
        "so": "strikeOuts", "hr": "homeRuns", "bf": "battersFaced",
        "pitches": "numberOfPitches", "hbp": "hitBatsmen",
    }
    result = {dest: get_number(source, src) for dest, src in mapping.items()}
    value = source.get("inningsPitched")
    result["ip"] = str(value) if value is not None else None
    return result

def make_player_rows(entry, match, box):
    teams = box.get("teams", {})
    output = []
    for side in ("away", "home"):
        team_box = teams.get(side) or {}
        official_id = (match.get("teams", {}).get(side) or {}).get("team", {}).get("id")
        box_id = (team_box.get("team") or {}).get("id")
        if official_id != box_id:
            raise ValueError("boxscore team ID mismatch on " + side)
        club = entry[side + "_team"]
        team_players = team_box.get("players", {})
        team_batters = {str(p) for p in team_box.get("batters", [])}
        team_pitchers = {str(p) for p in team_box.get("pitchers", [])}
        side_rows = []
        for item in team_players.values():
            person = item.get("person") or {}
            player_id = person.get("id")
            if not player_id:
                continue
            stats = item.get("stats") or {}
            bat, pit = stats.get("batting") or None, stats.get("pitching") or None
            field = stats.get("fielding") or None
            appeared = bool(bat or pit or field or item.get("battingOrder") is not None or
                            str(player_id) in team_batters or str(player_id) in team_pitchers)
            if not appeared:
                continue
            side_rows.append({
                "game_id": entry["id"], "game_pk": match["gamePk"],
                "date": entry["date"], "side": side, "team_id": box_id,
                "team": club, "player_id": player_id, "name": person.get("fullName"),
                "position": (item.get("position") or {}).get("abbreviation"),
                "batting_order": item.get("battingOrder"),
                "batting": batting(bat), "pitching": pitching(pit),
                "fielding": field,
            })
        if len(side_rows) < 9:
            raise ValueError("incomplete boxscore: only " + str(len(side_rows)) + " players for " + side)
        output.extend(side_rows)
    keys = [(r["side"], r["player_id"]) for r in output]
    if len(keys) != len(set(keys)):
        raise ValueError("duplicate player side/game entries")
    return output

def main():
    games_path = DATA / "games.json"
    stats_path = DATA / "player_stats.json"
    games = json.loads(games_path.read_text(encoding="utf8"))
    previous = json.loads(stats_path.read_text(encoding="utf8"))
    batch = [g for g in games if g.get("date") in BATCH_DATES]
    if len(batch) != 10 or len({g["id"] for g in batch}) != 10:
        raise ValueError("Batch 1 must contain exactly ten unique games")
    if any(g.get("date", "").startswith("2021-05-") and g["date"] < "2021-05-18" for g in batch):
        raise ValueError("An excluded early-May 2021 game was selected")
    # Clear outdated rows for this batch ONLY if replacement succeeds below.
    updated_rows = list(previous)
    cache = {}
    used = set()
    results = []
    for e in sorted(batch, key=lambda x: x["date"]):
        record = {"id": e["id"], "date": e["date"], "status": None, "rows": 0}
        try:
            sport = LEVEL[e["level"]]
            key = (e["date"], sport)
            if key not in cache:
                cache[key] = schedule(*key)
            match, reason = pick(e, cache[key], used)
            if not match:
                record["status"] = "unmatched"
                record["reason"] = reason
                e["box_score_status"] = "official_match_pending"
            else:
                gamepk = match["gamePk"]
                box = fetch(API + "/game/" + str(gamepk) + "/boxscore")
                rows = make_player_rows(e, match, box)
                # Every loaded player belongs to the documented attended game.
                updated_rows = [r for r in updated_rows if r.get("game_id") != e["id"]]
                updated_rows.extend(rows)
                used.add(gamepk)
                e["source_game_id"] = gamepk
                e["source_url"] = "https://www.milb.com/gameday/" + str(gamepk)
                e["box_score_status"] = "verified"
                e["official_home_team_id"] = match["teams"]["home"]["team"]["id"]
                e["official_away_team_id"] = match["teams"]["away"]["team"]["id"]
                record.update(status="verified", game_pk=gamepk, rows=len(rows))
        except Exception as exc:
            record["status"] = "error"
            record["reason"] = str(exc)[:250]
            e["box_score_status"] = "import_error"
        results.append(record)
        print(json.dumps(record), flush=True)
    # Do not replace previously verified rows if a retry cannot fetch the API.
    game_set = {g["id"] for g in games}
    if any(r.get("game_id") not in game_set for r in updated_rows):
        raise ValueError("orphan player stat row")
    report = {
        "source": "MLB StatsAPI (MiLB sportIds 11-14)",
        "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "batch_target": 10,
        "games_verified": sum(r["status"] == "verified" for r in results),
        "player_rows_in_batch": sum(r["rows"] for r in results),
        "games": results,
    }
    for name, value in (
        ("games.json", games),
        ("player_stats.json", updated_rows),
        ("import_report.json", report),
    ):
        (DATA / name).write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n", encoding="utf8")
    print("FINAL_REPORT " + json.dumps(report), flush=True)

if __name__ == "__main__":
    main()
