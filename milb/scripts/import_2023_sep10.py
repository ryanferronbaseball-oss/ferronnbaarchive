#!/usr/bin/env python3
"""Import two attended California League games on September 10, 2023.

Use official MLBAM game, team and player IDs; retain all earlier MiLB records.
Keep college/MiLB identity matching deferred. Venue identities are physical
ballparks, so San Manuel Stadium is reused and LoanMart Field is created once.
"""
import collections
import datetime
import json
import pathlib

import enrich_game_details as details
import import_batch1 as core
import import_pitching_decisions as credits

ROOT = pathlib.Path(__file__).resolve().parents[2]
DATA = ROOT / "milb" / "data"
VENUES = ROOT / "venues" / "data" / "venues.json"
DATE = "2023-09-10"
NEW = [
    {"id": "milb-2023-09-10-rawhide-quakes", "source_game_id": 724665,
     "away_team": "Visalia Rawhide", "home_team": "Rancho Cucamonga Quakes",
     "away_score": 6, "home_score": 8, "venue": "LoanMart Field",
     "city": "Rancho Cucamonga, CA", "venue_id": "venue-0137"},
    {"id": "milb-2023-09-10-storm-66ers", "source_game_id": 724862,
     "away_team": "Lake Elsinore Storm", "home_team": "Inland Empire 66ers",
     "away_score": 6, "home_score": 5, "venue": "San Manuel Stadium",
     "city": "San Bernardino, CA", "venue_id": "venue-0135"},
]


def load(path):
    return json.loads(path.read_text(encoding="utf8"))


def save(path, value):
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n", encoding="utf8")


def stadium_link(game):
    return {"id": game["id"], "date": game["date"],
            "away": game["away_team"], "home": game["home_team"],
            "awayScore": game["away_score"], "homeScore": game["home_score"],
            "url": "../milb/game.html?id=" + game["id"]}


def new_venue(game):
    return {
        "id": "venue-0137", "name": "LoanMart Field", "sport": "MiLB",
        "city": "Rancho Cucamonga, CA",
        "address": "8408 Rochester Avenue, Rancho Cucamonga, CA 91730",
        "lat": 34.102765, "lon": -117.54797,
        "coordinateConfidence": "High", "opened": "1993",
        "capacity": "Approximately 6,000 (official Rancho Cucamonga Quakes ballpark guide)",
        "occupants": "Rancho Cucamonga Quakes minor-league baseball",
        "history": "Opened April 8, 1993 at the Epicenter in Rancho Cucamonga. The Quakes have played in this same ballpark since 1993. It became LoanMart Field for the 2013 season and carried that name at the September 10, 2023 game. Later naming rights changed; the physical stadium remains the same.",
        "sources": ["https://www.milb.com/rancho-cucamonga/ballpark",
                    "https://www.milb.com/rancho-cucamonga/ballpark/frontoffice",
                    "https://www.milb.com/news/gcs-43824950"],
        "factNote": "First attended September 10, 2023, Visalia Rawhide at Rancho Cucamonga Quakes.",
        "games": [stadium_link(game)], "visits": 1,
        "firstVisit": DATE, "lastVisit": DATE,
    }


def update_counter(path, old, new):
    text = path.read_text(encoding="utf8")
    if text.count(old) != 1:
        raise ValueError(f"Expected one marker in {path}: {old}")
    return text.replace(old, new)


def main():
    games = load(DATA / "games.json")
    rows = load(DATA / "player_stats.json")
    venues = load(VENUES)
    prev_report = load(DATA / "game_detail_report.json")
    prior_credits = load(DATA / "pitching_decisions.json")
    prior_audit = load(DATA / "pitching_decisions_audit.json")
    before_college = (DATA / "college_links.json").read_bytes()
    assert len(games) == 112 and prev_report["games_checked"] == 112
    assert len(prior_credits) == 112 and prior_audit["games_checked"] == 112
    assert venues["venueCount"] == 136 and venues["mappedGames"] == 818
    assert len({g["source_game_id"] for g in games}) == len(games)
    existing_ids = {g["id"] for g in games}
    existing_pks = {g["source_game_id"] for g in games}
    if any(e["id"] in existing_ids or e["source_game_id"] in existing_pks for e in NEW):
        raise ValueError("A September 10 game already exists; refusing duplicate")
    if any(v["name"] == "LoanMart Field" for v in venues["venues"]):
        raise ValueError("LoanMart Field physical venue already exists")
    if any(v["id"] == "venue-0137" for v in venues["venues"]):
        raise ValueError("New venue ID is occupied")
    san = next(v for v in venues["venues"] if v["id"] == "venue-0135")
    if san["name"] != "San Manuel Stadium" or san["visits"] != 18:
        raise ValueError("Existing San Manuel Stadium venue changed")

    schedule = core.schedule(DATE, 14)
    added_games, added_rows, enrichments = [], [], []
    innings = load(DATA / "inning_scores.json")
    plays = load(DATA / "scoring_plays.json")
    decisions = dict(prior_credits)
    for expected in NEW:
        candidates = [s for s in schedule if s.get("gamePk") == expected["source_game_id"]]
        if len(candidates) != 1:
            raise ValueError(f"Not exactly one official game: {expected['id']}")
        game = candidates[0]
        if game.get("officialDate") != DATE or game["status"]["abstractGameState"] != "Final":
            raise ValueError("Date/final mismatch")
        for side in ("away", "home"):
            official = game["teams"][side]
            if not core.same_team(expected[side + "_team"], official["team"]["name"]):
                raise ValueError(f"Official {side} team mismatch: {game['gamePk']}")
            if official["score"] != expected[side + "_score"]:
                raise ValueError(f"Official {side} runs mismatch: {game['gamePk']}")
        e = dict(expected, date=DATE, level="Single-A",
                 source_url="https://www.milb.com/gameday/" + str(game["gamePk"]),
                 box_score_status="verified", attendance_confirmed=True,
                 official_home_team_id=game["teams"]["home"]["team"]["id"],
                 official_away_team_id=game["teams"]["away"]["team"]["id"])
        box = core.fetch(f"{core.API}/game/{game['gamePk']}/boxscore")
        stats = core.make_player_rows(e, game, box)
        if len(stats) < 18:
            raise ValueError("Incomplete official roster")
        for side in ("away", "home"):
            side_runs = sum((r.get("batting") or {}).get("r") or 0 for r in stats if r["side"] == side)
            if side_runs != e[side + "_score"]:
                raise ValueError(f"Box-score batting runs do not match {side} final: {side_runs}")
        detail = details.enrich(e)
        if any(detail.get(field + "_status") != "verified" for field in ("score", "play", "order")):
            raise ValueError(f"Incomplete official game detail: {e['id']}: {detail}")
        credit = credits.official_decisions(e)
        winner_side = "away" if e["away_score"] > e["home_score"] else "home"
        credited = [("winner", winner_side), ("loser", "home" if winner_side == "away" else "away"),
                    ("save", winner_side)]
        for role, side in credited:
            person = credit.get(role)
            if person is not None and not any(
                r["player_id"] == person["id"] and r["side"] == side and r.get("pitching") is not None
                for r in stats
            ):
                raise ValueError(f"Official {role} not in correct team pitching stats: {person}")
        if len({credit[role]["id"] for role in ("winner", "loser", "save") if credit.get(role)}) != sum(bool(credit.get(role)) for role in ("winner", "loser", "save")):
            raise ValueError("Overlapping W/L/S pitcher identities")
        for r in stats:
            patch = detail["order"].get((r["side"], str(r["player_id"])))
            if patch is None:
                raise ValueError(f"Missing lineup order for {r['player_id']}")
            r.update(patch)
            if r.get("pitching") is not None:
                for role, key in (("winner", "w"), ("loser", "l"), ("save", "sv")):
                    r["pitching"][key] = int(bool(credit.get(role) and credit[role]["id"] == r["player_id"]))
        if sum(r["pitching"]["w"] for r in stats if r.get("pitching") is not None) != 1:
            raise ValueError("Bad win credit")
        if sum(r["pitching"]["l"] for r in stats if r.get("pitching") is not None) != 1:
            raise ValueError("Bad loss credit")
        added_games.append(e)
        added_rows.extend(stats)
        innings[str(game["gamePk"])] = detail["scores"]
        plays[str(game["gamePk"])] = detail["plays"]
        decisions[str(game["gamePk"])] = credit
        detail.update(status="verified", decision_status="verified")
        detail.pop("decision_error", None)
        enrichments.append({k: v for k, v in detail.items() if k not in ("order", "scores", "plays", "decisions")})
        print("VERIFIED_GAME", json.dumps({"id": e["id"], "pk": game["gamePk"], "boxscore_players": len(stats), "W": credit["winner"]["name"], "L": credit["loser"]["name"], "SV": (credit.get("save") or {}).get("name")}), flush=True)

    all_games = sorted(games + added_games, key=lambda g: (g["date"], g["id"]))
    all_rows = sorted(rows + added_rows, key=lambda r: (r["date"], r["game_id"], r["side"], r["player_id"]))
    if len(all_games) != 114 or len({g["id"] for g in all_games}) != 114:
        raise ValueError("Missing or duplicate imported game")
    assert len(all_rows) == len(rows) + len(added_rows)
    assert set(decisions) == {str(g["source_game_id"]) for g in all_games}
    newpark = new_venue(added_games[0])
    san["games"].append(stadium_link(added_games[1]))
    san["games"].sort(key=lambda g: (g["date"], g["id"]))
    san["visits"] = len(san["games"])
    san["lastVisit"] = san["games"][-1]["date"]
    venues["venues"].append(newpark)
    venues["venues"].sort(key=lambda v: (v["name"], v["id"]))
    venues["venueCount"] = len(venues["venues"])
    venues["mappedGames"] = sum(len(v["games"]) for v in venues["venues"])
    venues["updated"] = datetime.datetime.now(datetime.timezone.utc).date().isoformat()
    assert venues["venueCount"] == 137 and venues["mappedGames"] == 820

    existing_summaries = [s for s in prev_report["games"] if s["game_id"] not in {g["id"] for g in added_games}]
    summaries = existing_summaries + enrichments
    assert len(summaries) == 114
    stamp = datetime.datetime.now(datetime.timezone.utc).isoformat()
    report = {**prev_report, "timestamp": stamp, "games_checked": 114,
              "innings_verified": sum(s["score_status"] == "verified" for s in summaries),
              "scoring_plays_verified": sum(s["play_status"] == "verified" for s in summaries),
              "pitcher_order_verified": sum(s["order_status"] == "verified" for s in summaries),
              "pitching_decisions_verified": sum(s["decision_status"] == "verified" for s in summaries),
              "games": summaries}
    assert all(report[key] == 114 for key in ("innings_verified", "scoring_plays_verified", "pitcher_order_verified", "pitching_decisions_verified"))
    pitch_rows = [r["pitching"] for r in all_rows if r.get("pitching") is not None]
    assert sum(r["w"] for r in pitch_rows) == sum(r["l"] for r in pitch_rows) == 114
    saves = sum(r["sv"] for r in pitch_rows)
    assert saves == sum(bool(d["save"]) for d in decisions.values())
    audit = {**prior_audit, "verified_at": stamp, "games_checked": 114,
             "games_with_verified_win": 114, "games_with_verified_loss": 114,
             "games_with_verified_save": saves, "games_without_save": 114 - saves,
             "player_game_pitching_rows": len(pitch_rows),
             "games": sorted(prior_audit["games"] + [
                 {"game_id": g["id"], "game_pk": g["source_game_id"],
                  "winner": decisions[str(g["source_game_id"])]["winner"]["id"],
                  "loser": decisions[str(g["source_game_id"])]["loser"]["id"],
                  "save": (decisions[str(g["source_game_id"])].get("save") or {}).get("id")}
                 for g in added_games], key=lambda r: r["game_id"])}
    assert len(audit["games"]) == 114

    home = ROOT / "index.html"
    home_text = home.read_text(encoding="utf8")
    homepage = [("id=\"venueCount\">136", "id=\"venueCount\">137"),
                ("id=\"venueGameCount\">818", "id=\"venueGameCount\">820"),
                ("id=\"venueMapResult\">136 attended venues", "id=\"venueMapResult\">137 attended venues")]
    for old, new in homepage:
        if home_text.count(old) != 1:
            raise ValueError(f"Homepage count marker changed: {old}")
        home_text = home_text.replace(old, new)
    directory_path = ROOT / "venues" / "index.html"
    directory_text = directory_path.read_text(encoding="utf8")
    for old, new in (("136 physical stadiums", "137 physical stadiums"),
                     ("all 136 stadiums", "all 137 stadiums")):
        if directory_text.count(old) != 1:
            raise ValueError(f"Venue directory marker changed: {old}")
        directory_text = directory_text.replace(old, new)

    # All external data has been checked before writing any archive files.
    for filename, value in (("games.json", all_games), ("player_stats.json", all_rows),
                            ("inning_scores.json", innings), ("scoring_plays.json", plays),
                            ("pitching_decisions.json", decisions), ("game_detail_report.json", report),
                            ("pitching_decisions_audit.json", audit)):
        save(DATA / filename, value)
    save(VENUES, venues)
    home.write_text(home_text, encoding="utf8")
    directory_path.write_text(directory_text, encoding="utf8")
    assert (DATA / "college_links.json").read_bytes() == before_college
    print("TWO_GAME_IMPORT_SUCCESS", json.dumps({"games": len(all_games), "players_added": len(added_rows), "venue_count": venues["venueCount"], "mapped_games": venues["mappedGames"], "w_l_s_verified": len(decisions)}), flush=True)


if __name__ == "__main__":
    main()
