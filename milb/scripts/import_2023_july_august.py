#!/usr/bin/env python3
"""Import four user-confirmed 2023 MiLB games, including three ACL Royals games.

Use official dates to distinguish the July 7 ACL Royals game from the July 4
Royals–Rangers game carried on the July 7 live schedule. Preserve all prior
games, MLB links, decisions, and the deferred college-to-MiLB matching state.
"""
import datetime
import json
import pathlib

import enrich_game_details as details
import import_batch1 as core
import import_pitching_decisions as credits

ROOT = pathlib.Path(__file__).resolve().parents[2]
DATA = ROOT / "milb" / "data"
VENUES = ROOT / "venues" / "data" / "venues.json"
NEW = [
    {"id": "milb-2023-07-06-acl-royals-cubs", "date": "2023-07-06", "sport_id": 16,
     "source_game_id": 743303, "away_team": "ACL Royals", "home_team": "ACL Cubs",
     "away_score": 21, "home_score": 11, "level": "Rookie",
     "venue": "Sloan Park", "city": "Mesa, AZ", "venue_id": "venue-0138"},
    {"id": "milb-2023-07-07-acl-rangers-royals", "date": "2023-07-07", "sport_id": 16,
     "source_game_id": 743292, "away_team": "ACL Rangers", "home_team": "ACL Royals",
     "away_score": 8, "home_score": 6, "level": "Rookie",
     "venue": "Surprise Stadium", "city": "Surprise, AZ", "venue_id": "venue-0139"},
    {"id": "milb-2023-07-08-acl-royals-padres", "date": "2023-07-08", "sport_id": 16,
     "source_game_id": 743287, "away_team": "ACL Royals", "home_team": "ACL Padres",
     "away_score": 3, "home_score": 4, "level": "Rookie",
     "venue": "Peoria Stadium", "city": "Peoria, AZ", "venue_id": "venue-0140"},
    {"id": "milb-2023-08-27-rawhide-66ers", "date": "2023-08-27", "sport_id": 14,
     "source_game_id": 724867, "away_team": "Visalia Rawhide", "home_team": "Inland Empire 66ers",
     "away_score": 10, "home_score": 12, "level": "Single-A",
     "venue": "San Manuel Stadium", "city": "San Bernardino, CA", "venue_id": "venue-0135"},
]


def read(path):
    return json.loads(path.read_text(encoding="utf8"))


def write(path, value):
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n", encoding="utf8")


def stadium_game(g):
    return {"id": g["id"], "date": g["date"], "away": g["away_team"],
            "home": g["home_team"], "awayScore": g["away_score"],
            "homeScore": g["home_score"],
            "url": "../milb/game.html?id=" + g["id"]}


def new_venues(games):
    byid = {g["venue_id"]: g for g in games}
    templates = [
        {"id": "venue-0138", "name": "Sloan Park", "sport": "MiLB", "city": "Mesa, AZ",
         "address": "2330 West Rio Salado Parkway, Mesa, AZ 85201",
         "lat": 33.4310672, "lon": -111.8815505, "coordinateConfidence": "High",
         "opened": "2014", "capacity": "15,000 (main spring-training stadium)",
         "occupants": "Chicago Cubs spring training; ACL Cubs development program",
         "history": "Opened in 2014 as the Chicago Cubs' spring-training home, originally called Cubs Park. Sloan Park is part of a larger Mesa training campus with additional practice fields. The official July 6, 2023 ACL schedule identifies Sloan Park as the game venue; its stadium seating capacity should not be interpreted as ACL-game attendance.",
         "sources": ["https://www.mesaaz.gov/Activities-Culture/Parks-Recreation-and-Community-Facilities/Parks-Facilities/Sloan-Park",
                     "https://www.visitmesa.com/things-to-do/spring-training/chicago-cubs/"],
         "factNote": "First attended July 6, 2023, ACL Royals at ACL Cubs."},
        {"id": "venue-0139", "name": "Surprise Stadium", "sport": "MiLB", "city": "Surprise, AZ",
         "address": "15850 North Bullard Avenue, Surprise, AZ 85374",
         "lat": 33.62778, "lon": -112.37778, "coordinateConfidence": "High",
         "opened": "2002", "capacity": "10,714 (main spring-training stadium)",
         "occupants": "Kansas City Royals and Texas Rangers spring training; ACL Royals and ACL Rangers programs",
         "history": "Opened in 2002 as the shared Cactus League home of the Royals and Rangers. Its playing field is named Billy Parker Field. The adjacent Surprise Recreation Campus includes player-development fields; the official July 7, 2023 ACL schedule lists Surprise Stadium as the venue.",
         "sources": ["https://www.surprisestadium.com/stadium-info/about",
                     "https://www.surprisestadium.com/stadium-info/stadium-a-z"],
         "factNote": "First attended July 7, 2023, ACL Rangers at ACL Royals. The separately dated July 4 game on the July 7 live schedule is not counted."},
        {"id": "venue-0140", "name": "Peoria Stadium", "sport": "MiLB", "city": "Peoria, AZ",
         "address": "16101 North 83rd Avenue, Peoria, AZ 85382",
         "lat": 33.6319, "lon": -112.2332, "coordinateConfidence": "High",
         "opened": "1994", "capacity": "12,518 (main stadium at Peoria Sports Complex)",
         "occupants": "San Diego Padres and Seattle Mariners spring training; ACL Padres and ACL Mariners programs",
         "history": "Peoria Sports Complex opened in 1994 as the first shared two-team MLB spring-training complex. It includes the main Peoria Stadium and adjoining practice fields. The official July 8, 2023 ACL game venue is listed as Peoria Stadium; main-stadium seating capacity is not ACL attendance.",
         "sources": ["https://www.peoriasportscomplex.com/spring-training/find-info/about-sports-complex",
                     "https://www.peoriasportscomplex.com/spring-training/find-info/a-to-z-guide"],
         "factNote": "First attended July 8, 2023, ACL Royals at ACL Padres."},
    ]
    for v in templates:
        game = byid[v["id"]]
        v["games"] = [stadium_game(game)]
        v["visits"] = 1
        v["firstVisit"] = game["date"]
        v["lastVisit"] = game["date"]
    return templates


def main():
    games = read(DATA / "games.json")
    rows = read(DATA / "player_stats.json")
    venues = read(VENUES)
    prev = read(DATA / "game_detail_report.json")
    decisions = read(DATA / "pitching_decisions.json")
    prior_audit = read(DATA / "pitching_decisions_audit.json")
    progress = read(DATA / "season_2021_import_progress.json")
    college_before = (DATA / "college_links.json").read_bytes()
    if len(games) != 114 or prev["games_checked"] != 114 or len(decisions) != 114:
        raise ValueError("Expected 114 verified games with W/L/S from earlier batch")
    if prior_audit["games_checked"] != 114 or venues["venueCount"] != 137 or venues["mappedGames"] != 820:
        raise ValueError("Venue and decision baseline changed")
    if progress["2021_games_remaining"] != 0 or not progress["college_matching_deferred"]:
        raise ValueError("Deferred cross-sport policy changed")
    existing_ids = {g["id"] for g in games}
    existing_pks = {g["source_game_id"] for g in games}
    if any(e["id"] in existing_ids or e["source_game_id"] in existing_pks for e in NEW):
        raise ValueError("One of the four games is already imported")
    if any(v["id"] in {"venue-0138", "venue-0139", "venue-0140"} or
           v["name"] in {"Sloan Park", "Surprise Stadium", "Peoria Stadium"} for v in venues["venues"]):
        raise ValueError("A new physical venue is already registered")
    san = next(v for v in venues["venues"] if v["id"] == "venue-0135")
    if san["name"] != "San Manuel Stadium" or san["visits"] != 19:
        raise ValueError("Existing San Manuel venue altered")
    schedules = {}
    new_games, new_rows, summaries = [], [], []
    innings = read(DATA / "inning_scores.json")
    plays = read(DATA / "scoring_plays.json")
    for target in NEW:
        key = target["date"], target["sport_id"]
        if key not in schedules:
            schedules[key] = core.schedule(*key)
        matches = [g for g in schedules[key] if g.get("gamePk") == target["source_game_id"]]
        if len(matches) != 1:
            raise ValueError(f"Missing or ambiguous official game: {target['id']}")
        schedule_game = matches[0]
        if (schedule_game.get("officialDate") != target["date"] or
            schedule_game.get("status", {}).get("abstractGameState") != "Final"):
            raise ValueError(f"Wrong official game date or non-final score: {target['id']}")
        for side in ("away", "home"):
            given = schedule_game["teams"][side]
            if not core.same_team(target[side + "_team"], given["team"]["name"]):
                raise ValueError(f"Wrong {side} club in game {target['id']}")
            if given["score"] != target[side + "_score"]:
                raise ValueError(f"Wrong {side} score in game {target['id']}")
        g = {k: v for k, v in target.items() if k != "sport_id"}
        g.update(source_url="https://www.milb.com/gameday/" + str(g["source_game_id"]),
                 box_score_status="verified", attendance_confirmed=True,
                 official_home_team_id=schedule_game["teams"]["home"]["team"]["id"],
                 official_away_team_id=schedule_game["teams"]["away"]["team"]["id"])
        box = core.fetch(f"{core.API}/game/{g['source_game_id']}/boxscore")
        records = core.make_player_rows(g, schedule_game, box)
        if len(records) < 18:
            raise ValueError(f"Incomplete player box score {g['id']}")
        for side in ("away", "home"):
            runs = sum((r.get("batting") or {}).get("r") or 0 for r in records if r["side"] == side)
            if runs != g[side + "_score"]:
                raise ValueError(f"Batting runs mismatch {g['id']} {side}: {runs}")
        details_record = details.enrich(g)
        if any(details_record.get(field + "_status") != "verified" for field in ("score", "play", "order")):
            raise ValueError(f"Incomplete official line, plays or player order {g['id']}: {details_record}")
        credit = credits.official_decisions(g)
        win_side = "away" if g["away_score"] > g["home_score"] else "home"
        other_side = "home" if win_side == "away" else "away"
        for role, side in (("winner", win_side), ("loser", other_side), ("save", win_side)):
            person = credit.get(role)
            if person and not any(r["player_id"] == person["id"] and r["side"] == side
                                  and r.get("pitching") is not None for r in records):
                raise ValueError(f"Pitching decision player missing from correct team: {g['id']} {role}")
        credited = [credit[role]["id"] for role in ("winner", "loser", "save") if credit.get(role)]
        if len(credited) != len(set(credited)):
            raise ValueError(f"Overlapping W/L/S in {g['id']}")
        for r in records:
            patch = details_record["order"].get((r["side"], str(r["player_id"])))
            if patch is None:
                raise ValueError(f"No player order for {r['player_id']}")
            r.update(patch)
            if r.get("pitching") is not None:
                for role, flag in (("winner", "w"), ("loser", "l"), ("save", "sv")):
                    r["pitching"][flag] = int(bool(credit.get(role) and credit[role]["id"] == r["player_id"]))
        for flag in ("w", "l"):
            if sum(r["pitching"][flag] for r in records if r.get("pitching") is not None) != 1:
                raise ValueError(f"No unique credited {flag} {g['id']}")
        new_games.append(g)
        new_rows.extend(records)
        innings[str(g["source_game_id"])] = details_record["scores"]
        plays[str(g["source_game_id"])] = details_record["plays"]
        decisions[str(g["source_game_id"])] = credit
        details_record.update(status="verified", decision_status="verified")
        details_record.pop("decision_error", None)
        summaries.append({k: v for k, v in details_record.items() if k not in ("order", "scores", "plays", "decisions")})
        print("VERIFIED_GAME", json.dumps({"id": g["id"], "pk": g["source_game_id"],
               "players": len(records), "W": credit["winner"]["name"],
               "L": credit["loser"]["name"], "SV": (credit.get("save") or {}).get("name")}), flush=True)
    allgames = sorted(games + new_games, key=lambda g: (g["date"], g["id"]))
    allrows = sorted(rows + new_rows, key=lambda r: (r["date"], r["game_id"], r["side"], r["player_id"]))
    assert len(allgames) == 118 and len({g["id"] for g in allgames}) == 118
    assert len(allrows) == len(rows) + len(new_rows)
    assert set(decisions) == {str(g["source_game_id"]) for g in allgames}
    san["games"].append(stadium_game(new_games[-1]))
    san["games"].sort(key=lambda r: (r["date"], r["id"]))
    san["visits"] = len(san["games"])
    san["lastVisit"] = san["games"][-1]["date"]
    venues["venues"].extend(new_venues(new_games[:3]))
    venues["venues"].sort(key=lambda v: (v["name"], v["id"]))
    venues["venueCount"] = len(venues["venues"])
    venues["mappedGames"] = sum(len(v["games"]) for v in venues["venues"])
    venues["updated"] = datetime.datetime.now(datetime.timezone.utc).date().isoformat()
    assert venues["venueCount"] == 140 and venues["mappedGames"] == 824
    allsummaries = prev["games"] + summaries
    assert len(allsummaries) == 118
    stamp = datetime.datetime.now(datetime.timezone.utc).isoformat()
    report = {**prev, "timestamp": stamp, "games_checked": 118,
              "innings_verified": sum(s["score_status"] == "verified" for s in allsummaries),
              "scoring_plays_verified": sum(s["play_status"] == "verified" for s in allsummaries),
              "pitcher_order_verified": sum(s["order_status"] == "verified" for s in allsummaries),
              "pitching_decisions_verified": sum(s["decision_status"] == "verified" for s in allsummaries),
              "games": allsummaries}
    assert all(report[k] == 118 for k in ("innings_verified", "scoring_plays_verified", "pitcher_order_verified", "pitching_decisions_verified"))
    pitching = [r["pitching"] for r in allrows if r.get("pitching") is not None]
    wins = sum(r["w"] for r in pitching)
    losses = sum(r["l"] for r in pitching)
    saves = sum(r["sv"] for r in pitching)
    assert wins == losses == 118
    assert saves == sum(bool(d.get("save")) for d in decisions.values())
    audit = {**prior_audit, "verified_at": stamp, "games_checked": 118,
             "games_with_verified_win": 118, "games_with_verified_loss": 118,
             "games_with_verified_save": saves, "games_without_save": 118 - saves,
             "player_game_pitching_rows": len(pitching),
             "games": sorted(prior_audit["games"] + [
                 {"game_id": g["id"], "game_pk": g["source_game_id"],
                  "winner": decisions[str(g["source_game_id"])]["winner"]["id"],
                  "loser": decisions[str(g["source_game_id"])]["loser"]["id"],
                  "save": (decisions[str(g["source_game_id"])].get("save") or {}).get("id")}
                 for g in new_games], key=lambda r: r["game_id"])}
    assert len(audit["games"]) == 118
    progress["all_milb_games_imported"] = 118
    progress["updated"] = stamp
    home = ROOT / "index.html"
    homepage = home.read_text(encoding="utf8")
    for old, new in (("id=\"venueCount\">137", "id=\"venueCount\">140"),
                     ("id=\"venueGameCount\">820", "id=\"venueGameCount\">824"),
                     ("id=\"venueMapResult\">137 attended venues", "id=\"venueMapResult\">140 attended venues")):
        if homepage.count(old) != 1:
            raise ValueError("Homepage venue count changed: " + old)
        homepage = homepage.replace(old, new)
    directory_path = ROOT / "venues" / "index.html"
    directory = directory_path.read_text(encoding="utf8")
    for old, new in (("137 physical stadiums", "140 physical stadiums"),
                     ("all 137 stadiums", "all 140 stadiums")):
        if directory.count(old) != 1:
            raise ValueError("Venue directory count changed: " + old)
        directory = directory.replace(old, new)
    overview_path = ROOT / "milb" / "assets" / "overview.js"
    overview = overview_path.read_text(encoding="utf8")
    old = "from Single-A to Triple-A"
    if overview.count(old) != 1:
        raise ValueError("MiLB level description changed")
    overview = overview.replace(old, "from rookie-level complex leagues through Triple-A")
    page_path = ROOT / "milb" / "index.html"
    page = page_path.read_text(encoding="utf8")
    old = "overview.js?v=milb-mlb-overview-20261106"
    if page.count(old) != 1:
        raise ValueError("MiLB overview cache marker changed")
    page = page.replace(old, "overview.js?v=milb-acl-20261107")
    # All official data and every output invariant verified before any writes.
    for name, value in (("games.json", allgames), ("player_stats.json", allrows),
                        ("inning_scores.json", innings), ("scoring_plays.json", plays),
                        ("pitching_decisions.json", decisions), ("game_detail_report.json", report),
                        ("pitching_decisions_audit.json", audit),
                        ("season_2021_import_progress.json", progress)):
        write(DATA / name, value)
    write(VENUES, venues)
    home.write_text(homepage, encoding="utf8")
    directory_path.write_text(directory, encoding="utf8")
    overview_path.write_text(overview, encoding="utf8")
    page_path.write_text(page, encoding="utf8")
    assert (DATA / "college_links.json").read_bytes() == college_before
    print("FOUR_GAME_IMPORT_SUCCESS", json.dumps({"total_games": 118, "player_rows_added": len(new_rows),
          "venues": 140, "mapped_games": 824, "w_l_s_verified": len(decisions)}), flush=True)


if __name__ == "__main__":
    main()
