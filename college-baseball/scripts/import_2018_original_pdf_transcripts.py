#!/usr/bin/env python3
"""Strict import of TWO exact user-uploaded original 2018 USD Automated ScoreBook PDFs.

The original university one-page scorebooks were saved as full line-preserving
text transcripts under data/official_pdf_transcriptions. Recheck all batting
columns, pitcher totals, W/L/S, R/H/E by inning, and original nine batting
slots. Fail closed on conflicting or missing source data. No synthesized stats.
"""
import hashlib
import re
from pathlib import Path

from import_sidearm_pilot import slug

DATA = Path(__file__).resolve().parents[1] / "data"
SOURCES = {
    "cb-2018-03-13-san-diego-state-san-diego-att0017": (
        "2018_03_13_sdsu_san_diego.txt",
        "Mar 13, 2018",
        ("San Diego State", "San Diego"),
        (9, 3),
        ((0,0,0,0,0,7,1,0,1),(0,0,1,0,1,0,1,0,0)),
        ((7,1),(8,3)),
        ("RITCHESON", "DONATELLA", None),
    ),
    "cb-2018-04-14-saint-mary-s-san-diego-att0025": (
        "2018_04_14_saint_marys_san_diego.txt",
        "Apr 14, 2018",
        ("Saint Mary's", "San Diego"),
        (6, 5),
        ((0,1,0,0,0,5,0,0,0),(0,0,0,1,2,0,2,0,0)),
        ((11,1),(8,1)),
        ("MILAM", "MURPHY", "HOBBS"),
    ),
}

def proper_name(source):
    source = source.strip()
    if "," in source:
        last, first = source.split(",", 1)
        name = first.strip() + " " + last.strip()
    else:
        name = source
    name = re.sub(r"\s+", " ", name).strip()
    # Preserve identity capitalization only for display; slugs are stable.
    return " ".join(x if any(ch.islower() for ch in x) else x.title() for x in name.split())

def batter_line(part):
    if not part.strip() or part.strip().startswith(("Player", "Totals")):
        return None
    # PDF export contains nine printed integer fields: AB R H RBI BB SO PO A LOB,
    # followed by an optional season AVG, not part of the game line.
    m = re.fullmatch(r"\s*(.*?)\s+((?:\d+\s+){8}\d+)(?:\s+(?:\.\d+|-))?\s*", part)
    if not m:
        return None
    who = m.group(1)
    mm = re.fullmatch(r"(.*?)\s+(rf/cf|rf/ph|ph/rf|p/3b|ph|pr|[1-9]b|ss|dh|lf|rf|cf|c|p)", who, re.I)
    if not mm:
        raise ValueError("Unknown original source batting position: " + who)
    person = proper_name(mm.group(1))
    pos = mm.group(2).lower()
    vals = list(map(int,m.group(2).split())) if False else list(map(int,m.group(0).split())) if False else list(map(int,re.findall(r"\d+",m.group(0)))) if False else list(map(int,re.findall(r"\b\d+\b",m.group(1).split()[-1]))) if False else list(map(int,re.findall(r"\d+",m.group(0).split()[-1]))) if False else list(map(int,re.findall(r"\d+",m.group(0)))) if False else list(map(int,re.findall(r"\d+",m.group(0)))) if False else list(map(int, re.findall(r"\d+", m.group(0)))) if False else None
    vals = list(map(int, m.group(0).split()[-9:])) if False else list(map(int, re.findall(r"\d+", part[part.find(m.group(1))+len(m.group(1)):].split()[-9:]))) if False else None
    return (person, pos, list(map(int, m.group(2).split())), bool(part and part[0].isspace()))

def pitcher_line(part):
    if not part.strip():
        return None
    m = re.fullmatch(r"\s*(.*?)\s+(\d+\.[012])\s+((?:\d+\s+){7}\d+)(?:\s+\d+\.\d+)?\s*", part)
    if not m: return None
    name = proper_name(m.group(1))
    n, f = map(int, m.group(2).split("."))
    return name, (n*3+f), list(map(int,m.group(3).split()))

def source_column_lines(raw, header):
    chunk = raw.splitlines()
    try:
        start = next(i for i,line in enumerate(chunk) if "Player" in line and "ab" in line.lower() and "rbi" in line.lower())
        end = next(i for i,line in enumerate(chunk[start+1:],start+1) if line.strip().startswith("Score by Innings"))
    except StopIteration:
        raise ValueError("Source transcript missing official two-column batting tables")
    return chunk,chunk[start+1:end]

def resolve_pitcher(abbrev, actual):
    if abbrev is None: return None
    surname = abbrev.split(",")[0].strip().lower()
    candidates=[name for name in actual if name.lower().split()[-1]==surname]
    if len(candidates)!=1:
        raise ValueError("Original winning/losing/saving pitcher not unique: "+abbrev+" / "+str(actual))
    return candidates[0]

def parse(game, row, global_keys):
    gid=game["id"]
    if gid not in SOURCES: raise ValueError("Unrecognized original uploaded PDF source")
    filename, printed_date, teams, scores, check_innings, hit_error, expected_decisions=SOURCES[gid]
    if ((game["away"],game["home"])!=teams or (game["away_score"],game["home_score"]) not in ((None,None),scores)
        or row.get("official_score")!=list(scores)
        or row.get("original_date")!=game["date"]
        or row.get("source_workbook_row")!=game["source_worksheet_row"]):
        raise ValueError("Original PDF transcript not the correct attendance identity")
    text=(DATA/"official_pdf_transcriptions"/filename).read_text(encoding="utf-8")
    if not (printed_date in text and "Automated ScoreBook" in text and " at San Diego" in text):
        raise ValueError("Printed university original PDF date/team heading missing")
    raw,batsection=source_column_lines(text,teams)
    batters={t:[] for t in teams}
    totals={}
    for line in batsection:
        for team,col in zip(teams,(line[:81],line[81:])):
            clean=col.strip()
            if clean.startswith("Totals"):
                vals=re.findall(r"\d+",clean[len("Totals"):])
                if len(vals)!=9: raise ValueError("Batting totals not 9 source fields: "+team+" "+clean)
                totals[team]=list(map(int,vals))
            elif clean.startswith("Player"): continue
            else:
                candidate=batter_line(col)
                if candidate:
                    batters[team].append(candidate)
    if len(totals)!=2:raise ValueError("Not both printed source batting team totals")
    scoreboard={t:None for t in teams}
    for line in raw:
        for i,t in enumerate(("Saint Mary's College" if teams[0]=="Saint Mary's" else teams[0], teams[1])):
            m=re.fullmatch(r"\s*"+re.escape(t)+r"\s+((?:\d+\s+){11}\d+)\s*",line)
            if m:
                vals=list(map(int,m.group(1).split()))
                scoreboard[teams[i]]={"innings":vals[:9],"runs":vals[9],"hits":vals[10],"errors":vals[11]}
    if any(not scoreboard[t] for t in teams):raise ValueError("Missing both exact nine-inning scores")
    if tuple(tuple(scoreboard[t]["innings"]) for t in teams)!=check_innings:
        raise ValueError("Source inning line failed independently transcribed checksum")
    for i,t in enumerate(teams):
        board=scoreboard[t]
        if (board["runs"],board["hits"],board["errors"])!=(scores[i],*hit_error[i]):
            raise ValueError("Original PDF scoreboard R/H/E differs from official game")
        if sum(board["innings"])!=board["runs"]:
            raise ValueError("Original PDF inning sums differ from scored runs")

    # Extract original PDF pitching columns between pitching heading and Win line.
    try:
        pitch_start = next(i for i,line in enumerate(raw) if "ip" in line.lower() and "np" in line.lower() and all(t in line for t in (teams[1],)))
        pitch_end = next(i for i,line in enumerate(raw[pitch_start+1:],pitch_start+1) if line.strip().startswith("Win -"))
    except StopIteration:
        raise ValueError("Original PDF lacks complete two-column pitcher report")
    staffs={t:[] for t in teams}
    for line in raw[pitch_start+1:pitch_end]:
        for team,col in zip(teams,(line[:81],line[81:])):
            p=pitcher_line(col)
            if p: staffs[team].append(p)
    if any(not staffs[t] for t in teams): raise ValueError("Missing original pitching staff")
    for i,t in enumerate(teams):
        out=teams[1-i]
        if sum(p[1] for p in staffs[t])!=27:raise ValueError("Pitcher outs not 27: "+t)
        if sum(p[2][0] for p in staffs[t])!=scoreboard[out]["hits"]:raise ValueError("Pitcher hits allowed mismatch: "+t)
        if sum(p[2][1] for p in staffs[t])!=scoreboard[out]["runs"]:raise ValueError("Pitcher runs allowed mismatch: "+t)
        if sum(p[2][4] for p in staffs[t])!=totals[out][5]:raise ValueError("Pitcher strikeouts and hitter Ks differ: "+t)
    all_pitchers={t:[name for name,_,_ in staffs[t]] for t in teams}
    decision={}
    for label,expected,side in zip(("win","loss","save"),expected_decisions,(teams[scores[0]<scores[1]],teams[scores[0]>scores[1]],None)):
        m=re.search(r"\b"+label+r"\s*-\s*([^.]+?)\s*\((?:\d+-\d+|\d+)\)",text,re.I)
        if expected is None:
            if not re.search(r"\bSave\s*-\s*None\b",text,re.I):raise ValueError("PDF save explicitly required to be none")
            decision[label]=None
        else:
            if not m or not m.group(1).strip().upper().startswith(expected):
                raise ValueError("Scorer "+label+" differs from official verified header")
            team=teams[0] if (label=="win" and scores[0]>scores[1]) or (label=="loss" and scores[0]<scores[1]) else teams[1]
            if label=="save":team=teams[0] if scores[0]>scores[1] else teams[1]
            decision[label]=resolve_pitcher(expected,all_pitchers[team])
    records={}
    def player(team,name):
        pid="cb-"+slug(team)+"-"+slug(name)
        if pid not in records:
            records[pid]={"game_id":gid,"player_id":pid,"player":name,
                "team":team,"source_url":row["official_full_gamebook_url"],
                "source_type":"official_usd_uploaded_pdf_line_preserving_transcript",
                "verification":"official_boxscore_verified"}
        return records[pid]
    audits=[]
    for i,team in enumerate(teams):
        slots=[]
        for appearance,(name,pos,vals,indented) in enumerate(batters[team]):
            ab,r,h,rbi,bb,so,po,assist,lob=vals
            # Pitchers with no plate appearances in these Statcrew sheets are
            # fielding entries, not tenth starting batting slots. Milam
            # genuinely hit in 2018 and must remain a starter.
            no_batting=pos=="p" and all(v==0 for v in vals[:6])
            if no_batting: continue
            is_sub=(indented or pos.startswith("ph") or pos.startswith("pr")
                    or "/ph" in pos)
            if is_sub:
                if not slots:raise ValueError("Substitution preceded lineup starter")
                slot=len(slots);subidx=len(slots[-1]);slots[-1].append(name)
            else:
                slots.append([name]);slot=len(slots);subidx=0
            rcd=player(team,name)
            rcd.update({"position":pos,"batting_slot":slot,"batting_sub_index":subidx,
                "batting_appearance_index":appearance,
                "batting":{"atBats":ab,"runs":r,"hits":h,"rbi":rbi,
                           "baseOnBalls":bb,"strikeOuts":so}})
        if len(slots)!=9:raise ValueError(team+": PDF batting order resolved to "+str(len(slots))+" slots: "+str(slots))
        for seq,(name,outs,vals) in enumerate(staffs[team]):
            p=player(team,name)
            p["pitching"]={"outs":outs,"hits":vals[0],"runs":vals[1],
                "earnedRuns":vals[2],"baseOnBalls":vals[3],"strikeOuts":vals[4],
                "numberOfPitches":vals[7]}
            p["pitching_appearance_index"]=seq
            for result,field in (("win","wins"),("loss","losses"),("save","saves")):
                p["pitching"][field]=int(name==decision[result]) if decision[result] else 0
        if len([r for r in records.values() if r["team"]==team and "batting" in r])<9:
            raise ValueError("Insufficient source batting records")
        for column,n in enumerate(("atBats","runs","hits","rbi","baseOnBalls","strikeOuts")):
            if sum(r["batting"][n] for r in records.values() if r["team"]==team and "batting" in r)!=totals[team][column]:
                raise ValueError(team+" individual batting "+n+" differs from source totals")
        if (totals[team][1],totals[team][2])!=(scores[i],scoreboard[team]["hits"]):
            raise ValueError("Source batting runs/hits not official board")
        audits.append({"team":team,"slots":9,"batter_rows":sum(r["team"]==team and "batting" in r for r in records.values()),
            "pitcher_rows":len(staffs[team]),"substitutes":sum(len(slot)-1 for slot in slots)})
    result=list(records.values())
    keys={(p["game_id"],p["player_id"]) for p in result}
    if len(result)<18 or len(keys)!=len(result) or keys & global_keys:
        raise ValueError("Duplicate player-game or insufficient player rows")
    game.update({"verification":"official_boxscore_verified","official_boxscore_status":"verified",
        "score_provenance":"official_university_user_supplied_original_pdf",
        "source_url":row["official_full_gamebook_url"],"away_score":scores[0],"home_score":scores[1],
        "away_hits":scoreboard[teams[0]]["hits"],"home_hits":scoreboard[teams[1]]["hits"],
        "away_errors":scoreboard[teams[0]]["errors"],"home_errors":scoreboard[teams[1]]["errors"],
        "innings":[{"inning":i+1,"away":a,"home":b} for i,(a,b) in enumerate(zip(*check_innings))],
        "pitching_decisions":decision})
    global_keys.update(keys)
    audit={"status":"PASS","source":row["official_full_gamebook_url"],
        "transcript_sha256":hashlib.sha256(text.encode("utf-8")).hexdigest(),
        "source_type":"user_supplied_original_university_pdf_verified_full_transcript",
        "player_rows":len(result),"lineup_audit":audits,
        "scoreboard":scoreboard,"pitching_decisions":decision}
    return result,audit
