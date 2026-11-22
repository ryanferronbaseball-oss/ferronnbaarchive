#!/usr/bin/env python3
"""Cross-match Courtside college players against SENIOR EuroLeague season stats.

Read-only with respect to live player tags. Matches are candidates for identity
verification and are never automatically promoted to the crosswalk.
"""
from __future__ import annotations

import argparse
import csv
import json
import re
import sys
import time
import unicodedata
from collections import defaultdict
from pathlib import Path
from urllib.parse import urlencode

import requests

ROOT = Path(__file__).resolve().parents[1]
REPORTS = ROOT / "reports"
API_HOSTS = [
    ("https://api-live.euroleague.net/v3/competitions/E/statistics/players/traditional", "pascal"),
    ("https://feeds.incrowdsports.com/provider/euroleague-feeds/v3/competitions/E/statistics/players/traditional", "camel"),
]
SUFFIX = re.compile(r"\b(jr|sr|ii|iii|iv|v)\b", re.IGNORECASE)
NONALPHA = re.compile(r"[^a-z0-9 ]+")


def normalize(name: str) -> str:
    name = str(name or "").strip()
    if "," in name:
        parts = name.split(",")
        if len(parts) == 2:
            name = parts[1].strip() + " " + parts[0].strip()
    name = unicodedata.normalize("NFKD", name).encode("ascii", "ignore").decode().lower()
    name = NONALPHA.sub(" ", name)
    name = SUFFIX.sub(" ", name)
    return " ".join(name.split())


def identity_token(name: str) -> str:
    return normalize(name).replace(" ", "")


def surname_initial(name: str) -> str:
    parts = normalize(name).split()
    return parts[-1] + "|" + parts[0][0] if len(parts) >= 2 else ""


def unwrap_players(payload):
    if isinstance(payload, list):
        return payload, None
    if not isinstance(payload, dict):
        raise ValueError("API returned non-object data")
    if isinstance(payload.get("players"), list):
        return payload["players"], payload.get("total")
    nested = payload.get("data")
    if isinstance(nested, dict) and isinstance(nested.get("players"), list):
        return nested["players"], nested.get("total")
    if isinstance(nested, list):
        return nested, payload.get("total")
    raise ValueError("No players array in API response: " + repr(list(payload.keys()))[:200])


def choose(row: dict, *keys):
    for key in keys:
        value = row.get(key)
        if value is not None and value != "":
            return value
    return None


def flatten(row: dict, season: str):
    person = row.get("player") or row.get("Player") or {}
    if not isinstance(person, dict):
        person = {"Name": str(person)}
    team = person.get("team") or person.get("Team") or row.get("team") or {}
    if not isinstance(team, dict):
        team = {"name": str(team)}
    name = choose(person, "name", "Name", "fullName", "FullName") or choose(row, "name", "Name", "playerName")
    code = choose(person, "code", "Code", "playerCode", "PlayerCode") or choose(row, "code", "playerCode", "PlayerCode")
    games = choose(row, "gamesPlayed", "GamesPlayed", "GP") or 0
    if isinstance(games, dict):
        games = games.get("total", 0)
    try:
        games = float(games)
    except (TypeError, ValueError):
        games = 0.0
    return {
        "name": str(name or "").strip(),
        "code": str(code or "").strip(),
        "team": str(choose(team, "name", "Name", "code", "Code") or "").strip(),
        "games": games,
        "season": season,
    }


def request_season(session: requests.Session, year: int, min_interval: float):
    season = "E" + str(year)
    last_error = ""
    for endpoint, style in API_HOSTS:
        all_players = []
        offset = 0
        page_size = 200
        while True:
            keys = ("SeasonMode", "SeasonCode", "statisticMode") if style == "pascal" else ("seasonMode", "seasonCode", "statisticMode")
            params = {
                keys[0]: "Single",
                keys[1]: season,
                keys[2]: "Accumulated",
                "statistic": "gamesPlayed",
                "sortDirection": "descending",
                "limit": page_size,
                "offset": offset,
            }
            url = endpoint + "?" + urlencode(params)
            payload = None
            for attempt in range(3):
                try:
                    response = session.get(endpoint, params=params, timeout=45)
                    if response.status_code == 429:
                        retry = int(response.headers.get("Retry-After", "65"))
                        print(f"{season} rate limited; sleeping {min(retry, 330)}s", flush=True)
                        time.sleep(min(max(retry, 5), 330))
                        continue
                    response.raise_for_status()
                    payload = response.json()
                    break
                except (requests.RequestException, ValueError) as exc:
                    last_error = f"{url}: {exc}"
                    if attempt < 2:
                        time.sleep(4 * (attempt + 1))
                finally:
                    time.sleep(min_interval)
            if payload is None:
                break
            try:
                current, total = unwrap_players(payload)
            except ValueError as exc:
                last_error = f"{url}: {exc}"
                break
            if offset == 0 and not current:
                last_error = f"{url}: empty players response"
                break
            all_players.extend(flatten(x, season) for x in current if isinstance(x, dict))
            offset += len(current)
            if not current or (total is not None and offset >= int(total)) or (total is None and len(current) < page_size):
                break
            if offset >= 1800:
                last_error = f"{url}: unexpected >1800 player rows"
                break
        # Requires substantive season coverage; a truncated feed is not audited.
        unique = {(x["code"], x["name"]) for x in all_players if x["games"] >= 1}
        if len(unique) >= 120:
            return all_players, endpoint, None
        last_error = last_error or f"{season}: only {len(unique)} players with games in {endpoint}"
    return [], None, last_error


def run(year_start: int, year_end: int, delay: float, output_path: Path):
    archive_rows = json.loads((ROOT / "data" / "player_boxscores_espn.json").read_text())
    crosswalk = json.loads((ROOT / "data" / "euroleague_crosswalk.json").read_text())
    tagged = {x["player_id"] for x in crosswalk}
    players = {}
    for record in archive_rows:
        pid = record["player_id"]
        entry = players.setdefault(pid, {"player_id": pid, "name": record["player"], "schools": set()})
        entry["schools"].add(record["team"])
    by_name = defaultdict(list)
    by_surname = defaultdict(list)
    for pid, p in players.items():
        by_name[identity_token(p["name"])].append(pid)
        by_surname[surname_initial(p["name"])].append(pid)

    session = requests.Session()
    session.headers.update({"User-Agent": "CourtsideArchiveEuroleagueHistoricalAudit/1.0 (research; one request ~7s)", "Accept": "application/json"})
    matches = defaultdict(list)
    season_status = []
    for year in range(year_start, year_end + 1):
        season = "E" + str(year)
        all_rows, endpoint, error = request_season(session, year, delay)
        season_status.append({"season": season, "status": "scanned" if endpoint else "failed", "rows": len(all_rows), "source": endpoint, "error": error})
        print(f"{season}: {len(all_rows)} rows; {'OK' if endpoint else error}", flush=True)
        if not endpoint:
            continue
        for player in all_rows:
            if player["games"] < 1 or not player["name"]:
                continue
            full_key = identity_token(player["name"])
            pids = by_name.get(full_key, [])
            match_kind = "exact_name" if pids else "initial_surname_candidate"
            if not pids:
                pids = by_surname.get(surname_initial(player["name"]), [])
                # Fuzzy matches are review-only and must never count as confirmed.
                if len(pids) != 1:
                    continue
            for pid in pids:
                matches[pid].append({**player, "match_kind": match_kind,
                    "source_url": endpoint + "?SeasonMode=Single&SeasonCode=" + season + "&statisticMode=Accumulated&statistic=gamesPlayed&limit=1000"})
    findings = []
    for pid, evidence in sorted(matches.items(), key=lambda x: players[x[0]]["name"].lower()):
        p = players[pid]
        unique_evidence = list({(x["season"], x["code"], x["team"]): x for x in evidence}.values())
        unique_evidence.sort(key=lambda e: (e["season"], e["name"]))
        kinds = {x["match_kind"] for x in unique_evidence}
        findings.append({
            "player_id": pid, "archive_name": p["name"], "schools": sorted(p["schools"]),
            "already_tagged": pid in tagged,
            "status": "existing_tag_match" if pid in tagged else ("review_exact_name" if "exact_name" in kinds else "review_name_similarity"),
            "evidence": unique_evidence,
        })
    untagged = [x for x in findings if not x["already_tagged"]]
    complete = all(x["status"] == "scanned" for x in season_status)
    summary = {
        "scope": "senior men's EuroLeague E; 2013-14 to 2026-27 by default; exclude EuroCup/U, youth ANGT, roster-only",
        "archive_players": len(players), "previous_tagged_players": len(tagged),
        "seasons_requested": len(season_status),
        "seasons_scanned": sum(x["status"] == "scanned" for x in season_status),
        "complete_requested_coverage": complete,
        "existing_tagged_with_name_matches": sum(x["already_tagged"] for x in findings),
        "new_identity_review_candidates": len(untagged),
        "note": "No new tags automatically issued. Name-only matches are not proof of identity; game statistics with >=1 GP are evidence of competition, subject to identity review.",
    }
    output = {"summary": summary, "seasons": season_status, "candidates": findings}
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(output, indent=2, ensure_ascii=False) + "\n")
    csv_path = output_path.with_suffix(".csv")
    with csv_path.open("w", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(["player_id", "archive_name", "schools", "tagged", "status", "euroleague_name", "euroleague_code", "season", "games", "club", "match_kind", "source_url"])
        for item in findings:
            for e in item["evidence"]:
                writer.writerow([item["player_id"], item["archive_name"], "; ".join(item["schools"]), item["already_tagged"], item["status"], e["name"], e["code"], e["season"], e["games"], e["team"], e["match_kind"], e["source_url"]])
    print(json.dumps(summary, indent=2), flush=True)
    return 0 if complete else 2


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--from-season", type=int, default=2013)
    parser.add_argument("--to-season", type=int, default=2026)
    parser.add_argument("--delay", type=float, default=7.0)
    parser.add_argument("--output", type=Path, default=REPORTS / "euroleague-historical-crossmatch.json")
    args = parser.parse_args()
    if args.from_season > args.to_season:
        parser.error("from-season must be <= to-season")
    sys.exit(run(args.from_season, args.to_season, args.delay, args.output))
