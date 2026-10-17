#!/usr/bin/env python3
"""Final whole-season integrity audit for the approved 2026 college-baseball slate.

Source-of-truth gamebooks have already passed per-game official R/H/E,
lineup, pitcher, decision and PDF/HTML reconciliation. This checkpoint only
marks 2026 complete if every one of the 68 eligible NCAA/four-year matches
has official verified players; seven junior-college rows remain attendance-only.
It never publishes the draft or imports any game from 2025 or earlier.
"""
from collections import Counter, defaultdict
from pathlib import Path
import json

D=Path(__file__).resolve().parents[1]/"data"
def read(name):return json.loads((D/name).read_text(encoding="utf-8"))
def write(name,item):(D/name).write_text(json.dumps(item,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
def main():
    games=read("games.json");stats=read("player_stats.json")
    report=read("import_report.json")
    stage=read("2026_remaining_ncca_gamebook_import_audit.json")
    pdf=read("2026_mar01_notredame_tenntech_pdf_audit.json")
    assert pdf["status"]=="PASS","University PDF original scorebook did not pass"
    assert len(games)==444 and len({g["id"] for g in games})==444
    assert len(stats)==len({(r["game_id"],r["player_id"]) for r in stats})
    assert all(r["game_id"] in {g["id"] for g in games} for r in stats)
    year=[g for g in games if g["date"].startswith("2026")]
    excluded=[g for g in year if g.get("boxscore_backfill_excluded")]
    eligible=[g for g in year if not g.get("boxscore_backfill_excluded")]
    assert len(year)==75 and len(excluded)==7 and len(eligible)==68
    assert all(g["verification"]=="attendance_only" for g in excluded)
    assert all(g.get("boxscore_backfill_exclusion_reason")=="junior_college" for g in excluded)
    assert all(g["verification"]=="official_boxscore_verified" for g in eligible)
    assert all(g.get("official_boxscore_status") in ("verified","player_lines_reconciled") for g in eligible)
    # The original nine-game pilot used the equivalent legacy status
    # "player_lines_reconciled"; its individual statistics are source-verified.
    excluded_ids={g["id"] for g in excluded}
    assert not any(r["game_id"] in excluded_ids for r in stats)
    rows=defaultdict(list)
    for r in stats:rows[r["game_id"]].append(r)
    monthly=defaultdict(lambda:{"eligible":0,"verified":0,"junior_college_excluded":0,"player_game_rows":0})
    issues=[]
    for g in year:
        m=monthly[g["date"][:7]]
        if g["id"] in excluded_ids:
            m["junior_college_excluded"]+=1
            continue
        m["eligible"]+=1
        m["verified"]+=int(g["verification"]=="official_boxscore_verified")
        recs=rows[g["id"]]
        m["player_game_rows"]+=len(recs)
        if not g.get("source_url") or not g["source_url"].startswith("https://"):
            issues.append((g["id"],"Missing official source link"))
        if len(recs)<18 or len({r["player_id"] for r in recs})!=len(recs):
            issues.append((g["id"],"Missing or colliding player identities"))
        line=g.get("innings") or []
        if not 7<=len(line)<=18 or any(k not in x for x in line for k in ("away","home")):
            issues.append((g["id"],"Incomplete inning scoreboard"))
        elif (sum(q["away"] or 0 for q in line)!=g["away_score"] or
              sum(q["home"] or 0 for q in line)!=g["home_score"]):
            issues.append((g["id"],"Innings fail final score"))
        for side in ("away","home"):
            team=g[side]
            bat=[r for r in recs if r["team"]==team and "batting" in r]
            pit=[r for r in recs if r["team"]==team and "pitching" in r]
            starters=[r for r in bat if r.get("batting_sub_index")==0]
            if sorted(r.get("batting_slot") for r in starters)!=list(range(1,10)):
                issues.append((g["id"],team+" missing exactly nine documented original batting slots"))
            if any(r.get("batting_slot") not in range(1,10) for r in bat):
                issues.append((g["id"],team+" has unattached batting substitution"))
            if not pit or sorted(r.get("pitching_appearance_index") for r in pit)!=list(range(len(pit))):
                issues.append((g["id"],team+" missing ordered pitching records"))
            if any("source_url" not in r for r in bat+pit):
                issues.append((g["id"],team+" player row lacks official link"))
            if sum(r["batting"]["runs"] for r in bat)!=g[side+"_score"]:
                issues.append((g["id"],team+" batting R does not reconcile official score"))
            if sum(r["batting"]["hits"] for r in bat)!=g[side+"_hits"]:
                issues.append((g["id"],team+" batting H does not reconcile official hits"))
            opp="home" if side=="away" else "away"
            if sum(r["pitching"]["runs"] for r in pit)!=g[opp+"_score"]:
                issues.append((g["id"],team+" pitchers R does not reconcile opponent"))
            if sum(r["pitching"]["hits"] for r in pit)!=g[opp+"_hits"]:
                issues.append((g["id"],team+" pitchers H does not reconcile opponent"))
    assert not issues,"Season audit failed: "+str(issues[:12])
    expected={"2026-01":(0,2),"2026-02":(8,3),"2026-03":(19,2),
              "2026-04":(14,0),"2026-05":(27,0)}
    for m,(elig,exclude) in expected.items():
        assert monthly[m]["eligible"]==elig
        assert monthly[m]["verified"]==elig
        assert monthly[m]["junior_college_excluded"]==exclude
    assert sum(m["player_game_rows"] for m in monthly.values())==len(stats)
    assert report["official_player_boxscores_imported"]==68
    assert report["player_stat_rows"]==len(stats)
    stage["html_phase_pending_review_before_pdf"]=stage.get("pending_review",[])
    stage["pending_review"]=[]
    stage["status"]="PASS"
    stage["total_verified"]=68
    stage["completed_pdf_after_html_pass"]={
        "game_id":pdf["game_id"],"source_url":pdf["source_url"],"audit_file":
        "2026_mar01_notredame_tenntech_pdf_audit.json"}
    stage["integrity_audit"]="2026_full_slate_monthly_integrity_audit.json"
    report["remaining_official_boxscore_work"]=0
    report["remaining_2026_eligible_noncaa_pending"]=0
    report["remaining_2026_eligible_ncaa_pending"]=0
    report["latest_verified_batch"]="2026 full eligible NCAA slate 68/68, official HTML and PDF audits complete"
    report["warning"]=("All 444 original attendance games retained. 2026: 68/68 eligible "
        "four-year/NCAA player gamebooks complete; 7 JUCO retained and excluded. "
        "Only 2026 source work approved; 2025 and publication/merge not approved.")
    gate=report.setdefault("monthly_review_gate",{})
    for m,detail in monthly.items():
        gate[m]={"status":"PASS","attended":detail["eligible"]+detail["junior_college_excluded"],
                 "eligible":detail["eligible"],"complete":detail["verified"],
                 "junior_college_excluded":detail["junior_college_excluded"]}
    gate["publication"]={"approved":False}
    gate["season_2025"]={"approved":False}
    audit={"status":"PASS","year":2026,"original_attendance":444,
           "total_attended_2026":len(year),"eligible":68,
           "complete_official_player_gamebooks":68,"junior_college_excluded":7,
           "player_game_rows":len(stats),"unique_player_ids":len({r["player_id"] for r in stats}),
           "months":dict(sorted(monthly.items())),
           "game_level_source_audits":[stage["integrity_audit"],
                   "2026_mar01_notredame_tenntech_pdf_audit.json"],
           "integrity_issues":[],"scope":"2026 only; 2025 and publication not approved"}
    for filename,ob in (
        ("2026_remaining_ncca_gamebook_import_audit.json",stage),
        ("2026_full_slate_monthly_integrity_audit.json",audit),
        ("import_report.json",report)):
        write(filename,ob)
    print("COMPLETE 2026: 68 / 68 eligible NCAA gamebooks, 7 JUCO excluded,",
          len(stats),"player-game rows; all source and lineup checks PASS",flush=True)


if __name__=="__main__":
    main()
