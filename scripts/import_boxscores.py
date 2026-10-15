"""Import player box scores from NBA Stats. Requires nba_api."""
import csv, json, pathlib, time
from nba_api.stats.endpoints import boxscoretraditionalv2

base=pathlib.Path(__file__).resolve().parents[1]/"data"
rows=list(csv.DictReader((base/"games.csv").open()))
out=base/"player_boxscores.json"
report_file=base/"import_report.json"
logs=json.loads(out.read_text()) if out.exists() else []
report=json.loads(report_file.read_text()) if report_file.exists() else {}
imported={p["game_id"] for p in logs}
for game in rows:
    gid=game["nba_game_id"]
    if not gid or gid in imported: continue
    try:
        frame=boxscoretraditionalv2.BoxScoreTraditionalV2(game_id=gid,timeout=25).player_stats.get_data_frame()
        players=[]
        for row in frame.to_dict("records"):
            if not row.get("MIN") or row.get("COMMENT"): continue
            stats={k.lower(): int(row.get(k) or 0) for k in ["PTS","REB","AST","STL","BLK","FGM","FGA","FG3M","FG3A","FTM","FTA","OREB","DREB"]}
            stats.update({"game_id":gid,"date":game["date"],"player_id":int(row["PLAYER_ID"]),"player":row["PLAYER_NAME"],"team":row["TEAM_ABBREVIATION"],"minutes":str(row["MIN"])})
            players.append(stats)
        totals={}
        for player in players:
            totals[player["team"]]=totals.get(player["team"],0)+player["pts"]
            assert player["pts"]==2*player["fgm"]+player["fg3m"]+player["ftm"],"points mismatch"
            assert player["reb"]==player["oreb"]+player["dreb"],"rebounds mismatch"
        assert len(totals)==2 and players,"missing team or players"
        if game["away_score"] and game["home_score"]:
            assert sorted(totals.values())==sorted([int(game["away_score"]),int(game["home_score"])]),"score mismatch"
        logs.extend(players)
        imported.add(gid)
        report[game["id"]]={"status":"validated","players":len(players),"game_id":gid}
        print("Imported",gid,len(players))
    except Exception as exc:
        report[game["id"]]={"status":"needs_review","game_id":gid,"error":str(exc)}
        print("Needs review",gid,str(exc))
    out.write_text(json.dumps(logs,indent=2)+"\n")
    report_file.write_text(json.dumps(report,indent=2)+"\n")
    time.sleep(2)
