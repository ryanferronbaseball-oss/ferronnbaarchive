#!/usr/bin/env python3
"""Finish the approved 2026 NCAA backfill without guessing any player line.

Read the official university source queues, require one distinct attendance identity
per game, then reconcile the game's inning scoreboard, both source batting tables,
both pitching tables, and source batting order. Never touch JUCO or earlier years.
A failure is recorded in a review audit; it cannot turn into a verified game.
"""
import json
import re
import sys
from pathlib import Path

import requests
from bs4 import BeautifulSoup
from import_sidearm_pilot import (
    official_tables, table_head, table_rows, normalize_name, scrape, slug,
)

D = Path(__file__).resolve().parents[1] / "data"
SESSION = requests.Session()
SESSION.headers["User-Agent"] = "Mozilla/5.0 CourtsideArchive source verification"
TARGET_YEAR = "2026"
SUPPORTED = {"official_boxscore_verified", "attendance_only"}
FILE_AUDIT = "2026_remaining_ncca_gamebook_import_audit.json"


def load(path):
    return json.loads((D / path).read_text(encoding="utf-8"))


def dump(path, value):
    (D / path).write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def source_manifest():
    march = load("2026_march_official_source_queue.json")
    early = load("2026_february_january_official_source_queue.json")
    out = {g["game_id"]: dict(g) for g in march["official_sources"]}
    for g in early["february_2026"]["gamebooks"]:
        if g["game_id"] in out:
            raise ValueError("Duplicate official source for " + g["game_id"])
        item = dict(g)
        item["source_url"] = item["source"]
        # Scores in February official source queue are e.g. 'Marist 1, Vanderbilt 8'.
        score_numbers = re.findall(r"\b\d+\b", item["result"])
        if len(score_numbers) != 2:
            raise ValueError("Cannot parse official final score " + str(item["result"]))
        item["official_score"] = [int(x) for x in score_numbers]
        out[g["game_id"]] = item
    return out


def extract_line_score(soup, expected):
    """Parse ONLY a table displaying both official inning-by-inning R/H/E rows."""
    for table in soup.find_all("table"):
        head = table.find("thead")
        if head is None:
            continue
        headers = [x.get_text(" ", strip=True) for x in head.find_all("th")]
        low = " ".join(headers).lower()
        if not ("team" in low and ("runs" in low or re.search(r"\br\b", low))
                and ("hits" in low or re.search(r"\bh\b", low))
                and ("errors" in low or re.search(r"\be\b", low))):
            continue
        innings = len([h for h in headers if re.search(r"(?:\b\d+(?:st|nd|rd|th)\b|\b\d+\b)", h)])
        if innings < 7 or innings > 18:
            continue
        body = table.find("tbody")
        trs = body.find_all("tr", recursive=False) if body else table.find_all("tr")[1:]
        candidates = []
        for tr in trs:
            cells = [x.get_text(" ", strip=True) for x in tr.find_all(["td", "th"], recursive=False)]
            if len(cells) < innings + 4:
                continue
            suffix = cells[-(innings + 3):]
            if any(not re.fullmatch(r"\d+", x) for x in suffix[-3:]):
                continue
            if any(not re.fullmatch(r"\d+|[xX\-]", x) for x in suffix[:-3]):
                continue
            runs, hits, errors = map(int, suffix[-3:])
            inn = [int(x) if x.isdigit() else None for x in suffix[:-3]]
            if sum(x or 0 for x in inn) != runs:
                continue
            candidates.append({"runs": runs, "hits": hits, "errors": errors, "innings": inn})
        if len(candidates) != 2:
            continue
        if [x["runs"] for x in candidates] != expected:
            continue
        return candidates
    raise ValueError("Official inning R/H/E scoreboard could not be unambiguously parsed and checked")


def _source_batters(table, valid_players, team):
    """Only accept a source-indented substitution; never infer a tenth slot."""
    head = table_head(table)
    raw = table.find("tbody")
    trs = raw.find_all("tr", recursive=False) if raw else table.find_all("tr")[1:]
    name_idx = head.index("Player")
    seen = []
    for tr in trs:
        cells = tr.find_all(["td", "th"], recursive=False)
        if name_idx >= len(cells):
            continue
        playercell = cells[name_idx]
        pos = cells[0].get_text(" ", strip=True) if name_idx != 0 else ""
        name = normalize_name(playercell.get_text(" ", strip=True), pos)
        key = slug(name)
        if key not in valid_players:
            continue
        raw_name = playercell.get_text("", strip=False)
        all_style = " ".join([
            str(playercell.get("style", "")),
            " ".join(playercell.get("class", [])),
            str(tr.get("style", "")),
            " ".join(tr.get("class", [])),
        ]).lower()
        indent_style = any(x in all_style for x in (
            "padding-left", "text-indent", "indent", "substitute", "sub-row",
        ))
        # Sidearm Vue markup marks pinch hitters/runners using a child <a>
        # with Tailwind class ml-[10px]; the table cell itself is unindented.
        # This was confirmed against each school's official gamebook HTML.
        child_indent = bool(playercell.select('[class*="ml-[10px]"]'))
        padded = bool(re.match(r"^(?:\u00a0|\s){3,}", raw_name))
        is_sub = indent_style or child_indent or padded or pos.lower() in ("ph", "pr", "ph/dh", "pr/dh")
        seen.append((key, name, is_sub))
    if len(seen) != len(valid_players) or len({x[0] for x in seen}) != len(seen):
        raise ValueError(team + ": cannot exactly match source batter lineup against source player records")
    if len(seen) == 9:
        return [[key] for key, _, _ in seen]
    if not any(sub for _, _, sub in seen):
        raise ValueError(team + ": extra batting entries without unambiguous source indentation")
    slots = []
    for key, _, is_sub in seen:
        if is_sub:
            if not slots:
                raise ValueError(team + ": source substitute precedes starter")
            slots[-1].append(key)
        else:
            slots.append([key])
    if len(slots) != 9:
        raise ValueError(team + ": source batting order resolved to " + str(len(slots)) + " starting slots, not 9")
    return slots


def assign_source_lineups(short_tables, game, rows, totals_by_side):
    used = set()
    audits = []
    if len(short_tables) != 2:
        raise ValueError("No exact pair of official batting summary tables")
    for tb in short_tables:
        total = next((r for r in table_rows(tb, table_head(tb)) if r.get("_totals")), None)
        if total is None:
            raise ValueError("Missing source lineup table total")
        pair = (int(total["R"]), int(total["H"]))
        candidates = [team for team, data in totals_by_side.items()
                      if pair == (data["runs"], data["hits"]) and team not in used]
        if len(candidates) != 1:
            raise ValueError("Lineup team identification not unique for R/H " + str(pair))
        team = candidates[0]
        used.add(team)
        records = [r for r in rows if r["team"] == team and "batting" in r]
        valid = {slug(r["player"]): r for r in records}
        if len(valid) != len(records):
            raise ValueError(team + ": source batting names collide")
        slots = _source_batters(tb, valid, team)
        n = 0
        for slot_index, slot in enumerate(slots, 1):
            for sub_index, key in enumerate(slot):
                person = valid[key]
                person["batting_slot"] = slot_index
                person["batting_sub_index"] = sub_index
                person["batting_appearance_index"] = n
                n += 1
        pitchers = [r for r in rows if r["team"] == team and "pitching" in r]
        for i, record in enumerate(pitchers):
            record["pitching_appearance_index"] = i
        audits.append({"team": team, "nine_starting_slots": True,
                       "batter_rows": len(records), "pitcher_rows": len(pitchers),
                       "substitutes": len(records) - 9})
    if used != set(totals_by_side):
        raise ValueError("Both teams' lineups were not reconciled")
    return audits


def debug_lineup_markup(game, url):
    """Log a short snapshot of official player-cell markup for manual source QA."""
    try:
        page = SESSION.get(url, timeout=30)
        page.raise_for_status()
        short, _, _ = official_tables(page.text, game)
        for ti, tab in enumerate(short):
            head = table_head(tab)
            if "Player" not in head:
                continue
            pi = head.index("Player")
            body = tab.find("tbody")
            trs = body.find_all("tr", recursive=False) if body else tab.find_all("tr")[1:]
            for tr in trs[:24]:
                cells = tr.find_all(["th", "td"], recursive=False)
                if len(cells) <= pi:
                    continue
                node = cells[pi]
                print("SOURCE-LINEUP", game["id"], ti,
                      "player=", repr(node.get_text(" ", strip=False)[:95]),
                      "html=", str(node)[:340].replace("\n", " "), flush=True)
    except Exception as exc:
        print("SOURCE-LINEUP-DEBUG-ERROR", game["id"], str(exc), flush=True)


def parse_decision(soup, key):
    # A decision can be empty or not match the listed pitcher; preserve unknown,
    # not a fabricated zero or guessed pitcher W/L/S.
    s = soup.get_text(" ", strip=True)
    pat = {"win": r"\bWin:\s*(.*?)\s*\(\d+-\d+\)",
           "loss": r"\bLoss:\s*(.*?)\s*\(\d+-\d+\)",
           "save": r"\bSave:\s*(.*?)\s*\(\d+\\?\)"}[key]
    m = re.search(pat, s, re.I)
    return m.group(1).strip(" ,") if m else None


def import_one(game, official, global_keys):
    url = official.get("source_url") or official.get("source")
    if not url or not url.startswith("https://"):
        raise ValueError("No HTTPS official gamebook")
    if url.lower().split("?")[0].endswith(".pdf"):
        raise ValueError("Official PDF needs separately audited PDF line transcription")
    expected = [int(x) for x in official["official_score"]]
    if len(expected) != 2 or expected[0] == expected[1]:
        raise ValueError("Official game final scores missing/ambiguous")
    page = SESSION.get(url, timeout=45)
    page.raise_for_status()
    if len(page.content) < 30000:
        raise ValueError("Official source response unexpectedly short")
    soup = BeautifulSoup(page.text, "html.parser")
    line = extract_line_score(soup, expected)
    short, detail, pitching = official_tables(page.text, game)
    if len(short) != 2 or len(detail) != 2 or len(pitching) != 2:
        raise ValueError("Official source missing either team's batting/pitching table")
    totals_by_side = {}
    for team, scoreboard in zip((game["away"], game["home"]), line):
        totals_by_side[team] = scoreboard
    for table in short:
        total = next((r for r in table_rows(table, table_head(table)) if r.get("_totals")), None)
        if total is None:
            raise ValueError("Batting team total missing")
        if not any((int(total["R"]), int(total["H"])) == (q["runs"], q["hits"]) for q in line):
            raise ValueError("Official boxscore R/H differs from its inning scoreboard")
    payload = dict(game, source_url=url, away_score=expected[0], home_score=expected[1],
                   away_hits=line[0]["hits"], home_hits=line[1]["hits"],
                   away_errors=line[0]["errors"], home_errors=line[1]["errors"],
                   winner=None, loser=None, save=None)
    rows, audit = scrape(payload)
    if len(rows) < 18:
        raise ValueError("Missing official individual batter/pitcher rows")
    lineups = assign_source_lineups(short, game, rows, totals_by_side)
    keys = {(x["game_id"], x["player_id"]) for x in rows}
    if len(keys) != len(rows) or keys & global_keys:
        raise ValueError("Source player-game ID collision")
    if any(sum(x["batting"]["runs"] for x in rows if x["team"] == t and "batting" in x) != totals_by_side[t]["runs"]
           or sum(x["batting"]["hits"] for x in rows if x["team"] == t and "batting" in x) != totals_by_side[t]["hits"]
           for t in (game["away"], game["home"])):
        raise ValueError("Individual source hitters do not total to official inning scoreboard")
    # Decisions must be explicitly cross-matched to source pitcher lines.
    decisions = {k: parse_decision(soup, k) for k in ("win", "loss", "save")}
    resolved = {}
    for key, name in decisions.items():
        match = [r for r in rows if "pitching" in r and name and slug(r["player"]) == slug(name)]
        resolved[key] = name if len(match) == 1 else None
    for r in rows:
        if "pitching" in r:
            for decision, stat in (("win", "wins"), ("loss", "losses"), ("save", "saves")):
                r["pitching"][stat] = int(slug(r["player"]) == slug(resolved[decision])) if resolved[decision] else None
    # All dependent checks have passed; now and only now promote this game.
    game.update({
        "source_url": url, "verification": "official_boxscore_verified",
        "official_boxscore_status": "verified", "score_provenance": "official_boxscore",
        "away_score": expected[0], "home_score": expected[1],
        "away_hits": line[0]["hits"], "home_hits": line[1]["hits"],
        "away_errors": line[0]["errors"], "home_errors": line[1]["errors"],
        "innings": [{"inning": i + 1, "away": a, "home": h}
                    for i, (a, h) in enumerate(zip(line[0]["innings"], line[1]["innings"]))],
        "pitching_decisions": {"win": resolved["win"], "loss": resolved["loss"],
                              "save": resolved["save"]},
        "game_type": "regular_season", "postseason_round": None,
    })
    if official.get("official_doubleheader_game"):
        game["game_number"] = int(official["official_doubleheader_game"])
        game["attendance_segment_confirmation_pending"] = True
    global_keys.update(keys)
    audit.update({"scoreboard": line, "lineup_audit": lineups,
                  "official_decisions": decisions, "resolved_pitcher_decisions": resolved})
    return rows, audit


def main():
    games = load("games.json")
    players = load("player_stats.json")
    report = load("import_report.json")
    if len(games) != 444 or len({g["id"] for g in games}) != 444:
        raise ValueError("Original 444 attendance games must remain intact")
    originals = {g["id"]: g for g in games}
    before = sum(g.get("verification") == "official_boxscore_verified" for g in games)
    manifest = source_manifest()
    keys = {(r["game_id"], r["player_id"]) for r in players}
    if len(keys) != len(players):
        raise ValueError("Existing verified player rows already have identity collision")
    passed, pending = [], []
    for game in sorted(games, key=lambda g: (g["date"], g["id"]), reverse=True):
        if not game["date"].startswith(TARGET_YEAR) or game.get("boxscore_backfill_excluded"):
            continue
        if game.get("verification") == "official_boxscore_verified":
            continue
        if game.get("verification") not in SUPPORTED:
            pending.append({"game_id": game["id"], "reason": "Unexpected prior status; manual review"})
            continue
        official = manifest.get(game["id"])
        if not official:
            pending.append({"game_id": game["id"], "reason": "No verified official source URL"})
            continue
        if official.get("date") != game["date"] or any(
                official.get(k) != game[k] for k in ("away", "home")):
            pending.append({"game_id": game["id"], "reason": "Source identity/date mismatch"})
            continue
        try:
            rows, audit = import_one(game, official, keys)
            players.extend(rows)
            passed.append({"game_id": game["id"], "player_rows": len(rows),
                           "source_url": game["source_url"], "audit": audit})
            print("PASS", game["id"], len(rows), flush=True)
        except Exception as exc:
            pending.append({"game_id": game["id"], "source_url": official.get("source_url"),
                            "reason": str(exc)})
            print("REVIEW", game["id"], str(exc), flush=True)
            if "batting" in str(exc) or "lineup" in str(exc):
                debug_lineup_markup(game, official.get("source_url") or official.get("source"))
    # All JUCO and prior-year records are immutable under this job.
    for gid, orig in originals.items():
        if orig.get("boxscore_backfill_excluded") or not orig["date"].startswith(TARGET_YEAR):
            assert orig is next(g for g in games if g["id"] == gid)
    players.sort(key=lambda r: (r["game_id"], r["team"], r.get("batting_slot", 99),
                               r.get("batting_sub_index", 99),
                               r.get("pitching_appearance_index", 99), r["player_id"]))
    report.update({
        "official_player_boxscores_imported": sum(g["verification"] == "official_boxscore_verified" for g in games),
        "official_score_and_inning_lines_matched": sum(g["verification"] != "attendance_only" for g in games),
        "official_scoreboard_player_lines_pending": sum(g["verification"] == "official_scoreboard_verified" for g in games),
        "attendance_only_pending_official_verification": sum(g["verification"] == "attendance_only" for g in games),
        "player_stat_rows": len(players), "unique_player_ids": len({r["player_id"] for r in players}),
        "latest_verified_batch": "2026 NCAA February/March strict source reconciling (no JUCO)",
        "remaining_official_boxscore_work": len(pending),
        "remaining_2026_eligible_noncaa_pending": len(pending),
        "warning": "2026 NCAA approved, JUCO excluded, older years and publication NOT approved. Incomplete official sources remain unverified, see audit.",
    })
    audit = {"status": "PASS" if not pending else "PARTIAL_REVIEW_REQUIRED",
             "completed_this_run": len(passed), "prior_verified": before,
             "total_verified": report["official_player_boxscores_imported"],
             "eligible_2026": 68, "original_attendance_rows": 444,
             "completed_games": passed, "pending_review": pending,
             "approval": "2026 statistical backfill only; keep draft PR; do not publish"}
    if passed:
        dump("games.json", games)
        dump("player_stats.json", players)
        dump("import_report.json", report)
    dump(FILE_AUDIT, audit)
    print(json.dumps({"completed": len(passed), "2026_total_verified": audit["total_verified"],
                      "pending": len(pending)}), flush=True)


if __name__ == "__main__":
    main()
