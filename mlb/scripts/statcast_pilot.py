#!/usr/bin/env python3
"""Import a small, verified sample of attended MLB Statcast games.

Run from the repository root:
    pip install pybaseball pandas
    python mlb/scripts/statcast_pilot.py

Outputs are generated on this feature branch, not automatically deployed.
"""
import json
import math
from pathlib import Path
from pybaseball import statcast_single_game
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
PILOT_YEARS = (2015, 2018, 2022, 2024, 2026)
FIELDS = ("game_pk", "at_bat_number", "pitch_number", "game_date",
          "pitcher", "batter", "pitch_type", "pitch_name", "release_speed",
          "launch_speed", "launch_angle", "hit_distance_sc", "events",
          "description", "inning", "inning_topbot", "home_team", "away_team")

def clean(v):
    if v is None: return None
    if pd.isna(v): return None
    if hasattr(v, "item"): v = v.item()
    if hasattr(v, "isoformat"): return v.isoformat()
    return v

def metric(row, key):
    v = clean(row.get(key))
    try: return float(v) if v is not None else None
    except (TypeError, ValueError): return None

def run():
    games = json.loads((DATA / "games.json").read_text())
    chosen = [next((g for g in games if g["date"].startswith(str(year)) and g.get("game_pk")), None)
              for year in PILOT_YEARS]
    chosen = [g for g in chosen if g]
    events, report, highlights = [], [], {}
    for game in chosen:
        pk = int(game["game_pk"])
        try:
            frame = statcast_single_game(pk)
            if frame is None or frame.empty:
                report.append({"game_pk": pk, "date": game["date"], "status": "no_data"})
                continue
            observed = frame.to_dict("records")
            pitches = []
            for r in observed:
                if int(clean(r.get("game_pk")) or 0) != pk: continue
                at_bat, pitch = clean(r.get("at_bat_number")), clean(r.get("pitch_number"))
                if at_bat is None or pitch is None: continue
                item = {k: clean(r.get(k)) for k in FIELDS}
                item["event_id"] = f"{pk}:{int(at_bat)}:{int(pitch)}"
                item["attendance_id"] = game["attendance_id"]
                pitches.append(item)
            if not pitches:
                report.append({"game_pk": pk, "date": game["date"], "status": "no_usable_events"})
                continue
            events.extend(pitches)
            fast = sorted((p for p in pitches if metric(p, "release_speed") is not None),
                          key=lambda p: metric(p, "release_speed"), reverse=True)
            hard = sorted((p for p in pitches if metric(p, "launch_speed") is not None),
                          key=lambda p: metric(p, "launch_speed"), reverse=True)
            homers = sorted((p for p in pitches if p.get("events") == "home_run"
                             and metric(p, "hit_distance_sc") is not None),
                            key=lambda p: metric(p, "hit_distance_sc"), reverse=True)
            highlights[str(pk)] = {
                "fastest_pitch": fast[0] if fast else None,
                "hardest_hit_ball": hard[0] if hard else None,
                "longest_home_run": homers[0] if homers else None,
            }
            report.append({"game_pk":pk,"date":game["date"],"status":"imported",
                           "events":len(pitches),"pitch_velocities":len(fast),
                           "exit_velocities":len(hard),"measured_home_runs":len(homers)})
        except Exception as exc:
            report.append({"game_pk":pk,"date":game["date"],"status":"fetch_error",
                           "error":str(exc)[:250]})
    unique = {p["event_id"]:p for p in events}
    events = list(unique.values())
    leaders = {
        "fastest_pitches": sorted((p for p in events if metric(p,"release_speed") is not None),
                                  key=lambda p:metric(p,"release_speed"),reverse=True),
        "hardest_hit_balls": sorted((p for p in events if metric(p,"launch_speed") is not None),
                                   key=lambda p:metric(p,"launch_speed"),reverse=True),
        "longest_home_runs": sorted((p for p in events if p.get("events")=="home_run"
                                    and metric(p,"hit_distance_sc") is not None),
                                   key=lambda p:metric(p,"hit_distance_sc"),reverse=True),
    }
    out = {"metadata":{"scope":"pilot","coverage":"imported games only",
                       "not_complete_attendance_leaderboards":True,
                       "historical_pitch_speed_caution":"Measurement systems vary across eras"},
           "report":report,"events":events,"highlights":highlights,"leaders":leaders}
    path = DATA / "statcast_pilot.json"
    path.write_text(json.dumps(out,indent=2,allow_nan=False)+"\n")
    print(json.dumps(report,indent=2))
    if not any(r["status"] == "imported" for r in report):
        raise RuntimeError("No pilot Statcast games imported; check source/network before treating results as verified")
    print("Wrote",path)

if __name__=="__main__":
    run()
