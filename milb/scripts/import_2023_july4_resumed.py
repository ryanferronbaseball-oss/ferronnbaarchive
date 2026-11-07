#!/usr/bin/env python3
"""Add the July 4 ACL Royals-Rangers game completed July 7, once only."""
import datetime
import json
from pathlib import Path

import import_batch1 as core
import enrich_game_details as details
import import_pitching_decisions as credits

ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / "milb/data"
VENUES = ROOT / "venues/data/venues.json"
PK = 743312
GID = "milb-2023-07-04-acl-royals-rangers"

def read(path):
    return json.loads(path.read_text())

def write(path, value):
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n")

def main():
    games = read(DATA / "games.json")
    players = read(DATA / "player_stats.json")
    decisions = read(DATA / "pitching_decisions.json")
    innings = read(DATA / "inning_scores.json")
    plays = read(DATA / "scoring_plays.json")
    report = read(DATA / "game_detail_report.json")
    audit = read(DATA / "pitching_decisions_audit.json")
    venues = read(VENUES)
    if not (len(games) == len(decisions) == len(innings) == len(plays) == report["games_checked"] == audit["games_checked"] == 118):
        raise ValueError("Unexpected MiLB baseline")
    if PK in {g["source_game_id"] for g in games} or GID in {g["id"] for g in games}:
        raise ValueError("This July 4 game is already recorded")
    schedule = [g for g in core.schedule("2023-07-04", 16) if g["gamePk"] == PK]
    if len(schedule) != 1:
        raise ValueError("Official July 4 schedule did not uniquely identify game")
    entry = schedule[0]
    assert entry["officialDate"] == "2023-07-04"
    assert entry["status"]["abstractGameState"] == "Final"
    assert core.same_team("ACL Royals", entry["teams"]["away"]["team"]["name"])
    assert core.same_team("ACL Rangers", entry["teams"]["home"]["team"]["name"])
    assert (entry["teams"]["away"]["score"], entry["teams"]["home"]["score"]) == (5, 8)
    g = {"id": GID, "date": "2023-07-04", "away_team": "ACL Royals",
         "home_team": "ACL Rangers", "away_score": 5, "home_score": 8,
         "level": "Rookie", "venue": "Surprise Stadium", "city": "Surprise, AZ",
         "source_game_id": PK, "source_url": f"https://www.milb.com/gameday/{PK}",
         "box_score_status": "verified", "attendance_confirmed": True,
         "official_home_team_id": entry["teams"]["home"]["team"]["id"],
         "official_away_team_id": entry["teams"]["away"]["team"]["id"],
         "venue_id": "venue-0139", "completed_date": "2023-07-07",
         "date_note": "Suspended July 4; completed July 7; full game counted once per attendee confirmation."}
    box = core.fetch(f"{core.API}/game/{PK}/boxscore")
    rows = core.make_player_rows(g, entry, box)
    assert len(rows) >= 18
    for side in ("home", "away"):
        assert sum((r.get("batting") or {}).get("r") or 0 for r in rows if r["side"] == side) == g[side + "_score"]
    summary = details.enrich(g)
    assert all(summary[field + "_status"] == "verified" for field in ("score", "play", "order"))
    decision = credits.official_decisions(g)
    for role, side in (("winner", "home"), ("loser", "away"), ("save", "home")):
        person = decision.get(role)
        if person:
            assert any(r["player_id"] == person["id"] and r["side"] == side and r.get("pitching") is not None for r in rows)
    for r in rows:
        patch = summary["order"].get((r["side"], str(r["player_id"])))
        assert patch is not None
        r.update(patch)
        if r.get("pitching") is not None:
            for role, flag in (("winner", "w"), ("loser", "l"), ("save", "sv")):
                r["pitching"][flag] = int(bool(decision.get(role) and decision[role]["id"] == r["player_id"]))
    assert sum(r["pitching"]["w"] for r in rows if r.get("pitching")) == 1
    assert sum(r["pitching"]["l"] for r in rows if r.get("pitching")) == 1
    stadium = next(v for v in venues["venues"] if v["id"] == "venue-0139")
    assert stadium["name"] == "Surprise Stadium"
    stadium["games"].append({"id": GID, "date": g["date"], "away": g["away_team"], "home": g["home_team"],
                             "awayScore": 5, "homeScore": 8, "url": "../milb/game.html?id=" + GID})
    stadium["games"].sort(key=lambda x: (x["date"], x["id"]))
    stadium["visits"] = len(stadium["games"])
    stadium["firstVisit"] = "2023-07-04"
    stadium["factNote"] = "First attended July 4, 2023, ACL Royals at ACL Rangers (suspended and completed July 7). Also attended July 7, ACL Rangers at ACL Royals."
    stadium["history"] = stadium["history"].replace("the official July 7, 2023 ACL schedule lists", "the official July 7, 2023 ACL schedule lists")
    venues["mappedGames"] += 1
    venues["updated"] = datetime.datetime.now(datetime.timezone.utc).date().isoformat()
    innings[str(PK)] = summary["scores"]
    plays[str(PK)] = summary["plays"]
    decisions[str(PK)] = decision
    summary.update(status="verified", decision_status="verified")
    summary.pop("decision_error", None)
    clean = {k: v for k, v in summary.items() if k not in ("order", "scores", "plays", "decisions")}
    report["games"].append(clean)
    report["games_checked"] += 1
    for k in ("innings_verified", "scoring_plays_verified", "pitcher_order_verified", "pitching_decisions_verified"):
        report[k] += 1
    stamp = datetime.datetime.now(datetime.timezone.utc).isoformat()
    report["timestamp"] = stamp
    audit["games"].append({"game_id": GID, "game_pk": PK,
                            "winner": decision["winner"]["id"], "loser": decision["loser"]["id"],
                            "save": (decision.get("save") or {}).get("id")})
    audit["games"].sort(key=lambda r: r["game_id"])
    audit["games_checked"] += 1
    audit["games_with_verified_win"] += 1
    audit["games_with_verified_loss"] += 1
    if decision.get("save"):
        audit["games_with_verified_save"] += 1
    else:
        audit["games_without_save"] += 1
    audit["player_game_pitching_rows"] += sum(r.get("pitching") is not None for r in rows)
    audit["verified_at"] = stamp
    games.append(g)
    games.sort(key=lambda x: (x["date"], x["id"]))
    players.extend(rows)
    players.sort(key=lambda r: (r["date"], r["game_id"], r["side"], r["player_id"]))
    assert len(games) == 119 and len({x["source_game_id"] for x in games}) == 119
    assert venues["mappedGames"] == 825 and stadium["visits"] == 2
    for path, value in ((DATA / "games.json", games), (DATA / "player_stats.json", players),
                        (DATA / "pitching_decisions.json", decisions), (DATA / "inning_scores.json", innings),
                        (DATA / "scoring_plays.json", plays), (DATA / "game_detail_report.json", report),
                        (DATA / "pitching_decisions_audit.json", audit), (VENUES, venues)):
        write(path, value)
    print("IMPORTED", GID, "players", len(rows), "pitching", decision)

if __name__ == "__main__":
    main()
