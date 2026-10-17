#!/usr/bin/env python3
"""Produce a compact, source-verified MLB Statcast UI snapshot for the staging site.

Input: complete assembled 2015+ attended-game Statcast event dataset.
This script never publishes or modifies the production site.
"""
import collections
import json
from pathlib import Path

DATA = Path(__file__).resolve().parents[1] / "data"


def read(name):
    return json.loads((DATA / name).read_text())


def main():
    payload = read("statcast_attendance_2015plus.json")
    meta = payload["metadata"]
    names = read("statcast_player_names.json")
    events = payload["events"]
    attended = {int(x["game_pk"]): x for x in read("games.json") if x.get("game_pk")}
    if meta["status"] != "PASS" or len(events) != 22844 or meta["games_source_verified"] != 77:
        raise ValueError("Required verified Statcast audit not present")
    if len({x["event_id"] for x in events}) != len(events):
        raise ValueError("Duplicated pitch events in source")

    def empty_game(e):
        pk = int(e["game_pk"])
        g = attended[pk]
        return {"pk": pk, "attendance_id": g["attendance_id"], "date": g["date"],
                "away": g["away"], "home": g["home"],
                "count": 0, "evCount": 0, "pitchCount": 0, "homers": 0,
                "maxEV": None, "maxEVPlayer": None, "maxPitch": None,
                "maxPitchPlayer": None, "longHR": None, "longHRPlayer": None}

    games, batters, pitchers = {}, {}, {}
    for e in events:
        pk = int(e["game_pk"])
        batter, pitcher = str(e["batter"]), str(e["pitcher"])
        if not names.get(batter) or not names.get(pitcher):
            raise ValueError("Missing official player name crosswalk: " + batter + "/" + pitcher)
        g = games.setdefault(pk, empty_game(e))
        g["count"] += 1
        velo, ev, dist = e.get("release_speed"), e.get("launch_speed"), e.get("hit_distance_sc")
        hr = e.get("events") == "home_run"
        if velo is not None:
            g["pitchCount"] += 1
            if g["maxPitch"] is None or velo > g["maxPitch"]:
                g["maxPitch"], g["maxPitchPlayer"] = velo, pitcher
            p = pitchers.setdefault(pitcher, {"id": pitcher, "games": set(),
                                                "pitchCount": 0, "speedTotal": 0,
                                                "maxSpeed": 0})
            p["games"].add(pk)
            p["pitchCount"] += 1
            p["speedTotal"] += velo
            p["maxSpeed"] = max(p["maxSpeed"], velo)
        if ev is not None or hr:
            b = batters.setdefault(batter, {"id": batter, "games": set(), "bip": 0,
                                             "evTotal": 0, "maxEV": 0, "hardHit": 0,
                                             "hr": 0, "longHR": None})
            b["games"].add(pk)
            if ev is not None:
                g["evCount"] += 1
                if g["maxEV"] is None or ev > g["maxEV"]:
                    g["maxEV"], g["maxEVPlayer"] = ev, batter
                b["bip"] += 1
                b["evTotal"] += ev
                b["maxEV"] = max(b["maxEV"], ev)
                b["hardHit"] += int(ev >= 95)
            if hr:
                b["hr"] += 1
                g["homers"] += 1
                if dist is not None:
                    if g["longHR"] is None or dist > g["longHR"]:
                        g["longHR"], g["longHRPlayer"] = dist, batter
                    if b["longHR"] is None or dist > b["longHR"]:
                        b["longHR"] = dist

    bats = []
    for b in batters.values():
        n = b["bip"]
        bats.append({"id": b["id"], "name": names[b["id"]], "games": len(b["games"]),
                     "bip": n, "avgEV": round(b["evTotal"]/n, 1) if n else None,
                     "maxEV": b["maxEV"] or None, "hardHit": b["hardHit"],
                     "hardHitPct": round(100*b["hardHit"]/n, 1) if n else None,
                     "hr": b["hr"], "longHR": b["longHR"]})
    pits = [{"id": p["id"], "name": names[p["id"]], "games": len(p["games"]),
             "pitchCount": p["pitchCount"],
             "avgSpeed": round(p["speedTotal"]/p["pitchCount"], 1),
             "maxSpeed": p["maxSpeed"]} for p in pitchers.values()]

    leaders = {}
    for label, field, participant in [
        ("hardest", "launch_speed", "batter"),
        ("fastest", "release_speed", "pitcher"),
        ("longest", "hit_distance_sc", "batter"),
    ]:
        selected = (x for x in events if x.get(field) is not None
                    and (label != "longest" or x.get("events") == "home_run"))
        ordered = sorted(selected, key=lambda x: (-x[field], x["game_date"], x["event_id"]))
        leaders[label] = [
            {"id": str(e[participant]), "name": names[str(e[participant])],
             "value": e[field], "pk": int(e["game_pk"]), "date": e["game_date"],
             "type": e.get("pitch_name") or e.get("pitch_type") or "—",
             "result": e.get("events") or e.get("description") or "—",
             "launch": e.get("launch_angle"), "event": e["event_id"]}
            for e in ordered[:150]
        ]

    summary = {
        "meta": meta,
        "games": sorted(games.values(), key=lambda x: x["date"], reverse=True),
        "bats": sorted(bats, key=lambda x: x["name"]),
        "pits": sorted(pits, key=lambda x: x["name"]),
        "leaders": leaders,
    }
    assert len(summary["games"]) == 77 and sum(g["count"] for g in summary["games"]) == len(events)
    assert len({g["pk"] for g in summary["games"]}) == 77
    assert all(len(summary["leaders"][k]) for k in ("hardest", "fastest", "longest"))
    path = DATA / "statcast_summary.json"
    path.write_text(json.dumps(summary, separators=(",", ":"), ensure_ascii=False, allow_nan=False) + "\n")
    print("UI staging snapshot verified:", len(games), "games,", len(events),
          "pitches,", len(bats), "batters,", len(pits), "pitchers;",
          "bytes:", path.stat().st_size)


if __name__ == "__main__":
    main()
