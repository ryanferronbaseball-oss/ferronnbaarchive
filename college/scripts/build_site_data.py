#!/usr/bin/env python3
"""Step 1 of the college website port: build and verify NBA-compatible NCAA data.

Run *after* import_espn.py and normalize_espn.py, not against the live NBA files.
The game_id on player rows is the unique COLLEGE attendance ID, while the
espn_event_id is the provider's actual NCAA event ID (never an NBA ID).
"""
import argparse
import csv
import json
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
GAME_FIELDS = ("id","date","away","home","arena","espn_event_id",
               "away_score","home_score","away_team_id","home_team_id","boxscore_status","site_type")
CORE = ("game_id","espn_event_id","date","player_id","player","team_id","minutes",
        "pts","reb","ast","fgm","fga","fg3m","fg3a","ftm","fta","oreb",
        "dreb","stl","blk","tov","pf")
STAT_FIELDS = ("pts","reb","ast","fgm","fga","fg3m","fg3a","ftm","fta",
               "oreb","dreb","stl","blk","tov","pf")

def check(ok, message):
    if not ok:
        raise ValueError(message)

def minutes(value):
    text = str(value)
    if ":" in text:
        a, b = text.split(":")
        check(a.isdigit() and b.isdigit() and int(b) < 60, "Invalid MM:SS minutes")
        return int(a) + int(b) / 60
    check(text not in ("", "None", "--", "DNP"), "Missing minutes for played athlete")
    return float(text)

def build(source, destination, expected_games=94, expected_players=1825):
    with (source / "site_games.csv").open(encoding="utf-8-sig",newline="") as stream:
        games = list(csv.DictReader(stream))
    players = json.loads((source / "site_players_certified.json").read_text(encoding="utf-8"))
    qa = json.loads((source / "qa_report.json").read_text(encoding="utf-8"))
    check(len(games) == qa.get("games_complete") == qa.get("games_points_reconciled") ==
          qa.get("games_minutes_reconciled") == expected_games, "Games failed QA or changed in count")
    check(qa.get("games_partial") == 0 and not qa.get("incomplete_attendance_ids"),
          "Unresolved games must not appear in all-time leaderboard data")
    check(len(players) == qa.get("certified_player_lines") == expected_players,
          "Player-game rows disagree with the certified source")
    # Source-cited event-level venue overrides; never infer an arena from listed home school.
    venue_path = ROOT / "data" / "verified_venues.csv"
    venue_rows = list(csv.DictReader(venue_path.open(encoding="utf-8", newline=""))) if venue_path.exists() else []
    by_id = {g["id"]:g for g in games}
    seen_venues = set()
    for v in venue_rows:
        gid = v["attendance_id"]
        check(gid not in seen_venues and gid in by_id, "Duplicate/unknown venue attendance ID " + gid)
        seen_venues.add(gid)
        g = by_id[gid]
        check(v["espn_event_id"] == g["espn_event_id"], "Venue event ID mismatch " + gid)
        check(bool(v["arena"]) and "," not in v["arena"], "Missing or CSV-unsafe arena " + gid)
        check(v["site_type"] in ("home", "neutral"), "Bad neutral-site classification " + gid)
        check(v["source_url"].startswith("https://") and bool(v["source_name"]), "Venue source missing " + gid)
        check(not g["arena"] or g["arena"] == v["arena"], "Conflicting venue name " + gid)
        g["arena"] = v["arena"]
        g["site_type"] = v["site_type"]
    for g in games:
        g.setdefault("site_type", "")
        check(bool(g["arena"]) == (g["id"] in seen_venues), "Unsourced venue not allowed " + g["id"])

    game_map, events, teams = {}, set(), {}
    for g in games:
        check(set(GAME_FIELDS).issubset(g), "Missing game CSV fields")
        gid, event = g["id"], g["espn_event_id"]
        check(gid.isdigit() and gid not in game_map, "Duplicate attendance game ID " + gid)
        check(event.isdigit() and event not in events, "Duplicate NCAA event ID " + event)
        check(g["boxscore_status"] == "complete" and g["away_team_id"] != g["home_team_id"],
              "Incomplete game or duplicate opposing school IDs")
        for side in ("away","home"):
            tid, name = g[side + "_team_id"], g[side]
            check(bool(tid and name), "Unknown college team")
            if tid in teams:
                check(teams[tid] == name, "Inconsistent school identity for team ID " + tid)
            teams[tid] = name
        game_map[gid] = g
        events.add(event)

    seen, school_ids_by_player, by_game_team = set(), defaultdict(set), defaultdict(list)
    name_by_id = {}
    for p in players:
        check(set(CORE).issubset(p), "Missing player schema field")
        gid, pid, tid = str(p["game_id"]), str(p["player_id"]), str(p["team_id"])
        check(gid in game_map, "Unmatched player game ID " + gid)
        game = game_map[gid]
        check(str(p["espn_event_id"]) == game["espn_event_id"] and p["date"] == game["date"],
              "Player date or event mismatch in game " + gid)
        check(tid in (game["away_team_id"], game["home_team_id"]),
              "Player school not in game " + gid)
        check(pid.startswith(("espn:", "official:")) and bool(p["player"]),
              "Missing qualified athlete identity")
        check(p.get("boxscore_complete") is True, "Non-certified player line")
        check((gid,pid) not in seen, "Duplicate player attendance " + gid + " / " + pid)
        seen.add((gid,pid))
        check(pid not in name_by_id or name_by_id[pid] == p["player"],
              "Athlete ID changed names; review before publishing")
        name_by_id[pid] = p["player"]
        m = minutes(p["minutes"])
        check(0 <= m <= 65, "Invalid athlete minutes")
        for stat in STAT_FIELDS:
            check(type(p[stat]) is int and p[stat] >= 0,
                  "Bad or missing box-score field: " + stat + " for " + pid)
        check(p["fgm"] <= p["fga"] and p["fg3m"] <= p["fg3a"] and p["ftm"] <= p["fta"],
              "Shooting makes exceed attempts")
        check(p["fg3m"] <= p["fgm"] and p["fg3a"] <= p["fga"], "3-point shots exceed field goals")
        check(2*p["fgm"]+p["fg3m"]+p["ftm"] == p["pts"], "Player scoring does not match shooting")
        check(p["oreb"]+p["dreb"] == p["reb"], "Player rebounds do not add up")
        school_ids_by_player[pid].add(tid)
        by_game_team[(gid,tid)].append(p)

    for g in games:
        totals = []
        for side in ("away","home"):
            lines = by_game_team[(g["id"],g[side+"_team_id"])]
            check(bool(lines), "Missing team lineup " + g["id"])
            check(sum(p["pts"] for p in lines) == int(g[side+"_score"]),
                  "Game scoring mismatch " + g["id"] + " " + side)
            totals.append(sum(minutes(p["minutes"]) for p in lines))
        check(any(all(abs(total-(200+25*n)) <= .1 for total in totals) for n in range(8)),
              "Team-minute discrepancy in game " + g["id"])

    schools_by_player = {
        pid: sorted(teams[tid] for tid in school_ids)
        for pid,school_ids in school_ids_by_player.items() if len(school_ids)>1
    }
    check(len(schools_by_player) == qa["multi_school_players"], "Multi-school identities changed")
    fixtures = {
        "official:san-diego:jase-townsend": (14,170),
        "official:utah-state:daniel-akin": (2,36),
        "official:cal-state-fullerton:tory-san-antonio": (2,10),
        "espn:4433281": (4,63),  # Hunter Sallis, Gonzaga + Wake Forest
    }
    for pid,(gp,points) in fixtures.items():
        rows = [p for p in players if p["player_id"] == pid]
        check(len(rows) == gp and sum(p["pts"] for p in rows) == points,
              "Unified player profile regression: " + pid)
    check(schools_by_player.get("espn:4433281") == ["Gonzaga","Wake Forest"],
          "Hunter Sallis school-transfer profile not unified")

    # Exact source records, names, shooting stats, and provenance retained.
    # The NBA HTML must be explicitly adapted to NCAA links/team maps in step 2.
    payload = [
        {k:p.get(k) for k in (
            *CORE,"team","opponent","source","source_url",
            "supplemental_official_source","official_override_source"
        )} for p in players
    ]
    payload.sort(key=lambda p: (p["date"],int(p["game_id"]),p["team_id"],p["player_id"]))
    destination.mkdir(parents=True,exist_ok=True)
    with (destination/"games.csv").open("w",encoding="utf-8",newline="") as output:
        writer = csv.DictWriter(output,GAME_FIELDS,extrasaction="ignore")
        writer.writeheader()
        writer.writerows(games)
    (destination/"player_boxscores_espn.json").write_text(
        json.dumps(payload,ensure_ascii=False,separators=(",",":"))+"\n",encoding="utf-8")
    (destination/"team_names.json").write_text(
        json.dumps(teams,ensure_ascii=False,sort_keys=True,indent=2)+"\n",encoding="utf-8")
    report = {
        "status":"PASS","stage":"college_data_adapter_only",
        "games":len(games),"player_game_rows":len(players),"unique_player_ids":len(name_by_id),
        "school_ids":len(teams),"cross_school_players":len(schools_by_player),
        "score_and_minute_reconciled_games":len(games),
        "jase_townsend_games":14,"jase_townsend_attended_points":170,
        "hunter_sallis_unified_games":4,
        "arenas_unverified":sum(not g["arena"] for g in games),
        "arenas_verified_games":len(venue_rows),
        "unique_verified_arenas":len({v["arena"] for v in venue_rows}),
        "neutral_site_games_verified":sum(v["site_type"]=="neutral" for v in venue_rows),
        "provisional_official_player_ids":sum(pid.startswith("official:") for pid in name_by_id),
        "release_note":"This certifies player-stat joins and sourced arenas; unverified venues and release checks remain."
    }
    (destination/"validation.json").write_text(json.dumps(report,indent=2)+"\n",encoding="utf-8")
    print(json.dumps(report,indent=2))
    return report

if __name__=="__main__":
    parser=argparse.ArgumentParser()
    parser.add_argument("--source",type=Path,default=ROOT/"output")
    parser.add_argument("--destination",type=Path,default=ROOT/"data")
    parser.add_argument("--expected-games",type=int,default=94)
    parser.add_argument("--expected-players",type=int,default=1825)
    a=parser.parse_args()
    build(a.source,a.destination,a.expected_games,a.expected_players)
