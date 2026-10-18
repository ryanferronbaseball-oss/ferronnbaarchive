#!/usr/bin/env python3
"""Strict 2024 Vanderbilt official two-page scorebook (PDF) transcription.
Fail closed on missing lines, conflicting source totals, incorrect game or scorer.
No inferred batting/fielding statistics, no pre-2024 edits.
"""
import re,io,hashlib,sys,subprocess
from import_sidearm_pilot import slug,normalize_name

def pdf_text(content):
    if not content.startswith(b"%PDF") or len(content)<5000:
        raise ValueError("Official source was not an actual complete PDF")
    try:
        from pypdf import PdfReader
    except ImportError:
        subprocess.check_call([sys.executable,"-m","pip","install","--quiet","pypdf==5.9.0"])
        from pypdf import PdfReader
    src=PdfReader(io.BytesIO(content))
    if len(src.pages)<1:raise ValueError("Official source PDF has no pages")
    txt=src.pages[0].extract_text()
    if not txt or len(txt)<800:raise ValueError("Official PDF has no first-page player scorebook text")
    return txt

# Narrow legacy exception: original Cincinnati scorebooks printed Feb 17
# although the original universities both list these distinct games Feb 18.
# Game number, complete teams/scores, inning lines and scorer still must pass.
CINCINNATI_2018_ARCHIVE = {
    "cb-2018-02-18-cincinnati-san-diego-att0005":
        (1, 10, (7, 4),
         "https://storage.googleapis.com/gobearcats-com-prod/2025/06/23/qre66UMRSF5t969mTcx51AEMiCvv3XATSOCaqyhH.pdf"),
    "cb-2018-02-18-cincinnati-san-diego-att0006":
        (2, 9, (3, 4),
         "https://storage.googleapis.com/gobearcats-com-prod/2025/06/29/EIKFzFi4XIx7rW5a9UvwMzpwiQSNIr5qQEvTHkBg.pdf"),
}

def parse(game,item,global_keys,response):
    text=pdf_text(response.content)
    first=text.splitlines()
    month,day=int(game["date"][5:7]),int(game["date"][8:10])
    months=["","Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"]
    legacy=CINCINNATI_2018_ARCHIVE.get(game["id"])
    date_ok=bool(re.search(r"\b"+months[month]+r"\s+"+str(day)+r",\s*"+str(game["date"][:4])+r"\b",text,re.I))
    if legacy:
        dh_number, innings_expected, legacy_scores, archive_url=legacy
        if (game["date"]!="2018-02-18" or (game["away"],game["home"])!=("Cincinnati","San Diego")
            or tuple(item["official_score"])!=legacy_scores or item.get("official_doubleheader_game")!=dh_number
            or item["source_url"]!=archive_url
            or not re.search(r"Feb\s+17,\s*2018\b",text,re.I)):
            raise ValueError("2018 Cincinnati university archive provenance or exact game check failed")
    elif not date_ok:
        raise ValueError("PDF printed game date differs from attendance record")
    # User corrected a previously mistaken April 14 attendance entry to the
    # official Saturday, April 13 Virginia Tech @ Georgia Tech 19-0 run-rule
    # game. Original Georgia Tech PDF states exactly SEVEN innings. Keep the
    # exception fixed to this specific protected attendance identity.
    apr13_gt=(game["id"]=="cb-2024-04-13-virginia-tech-georgia-tech-att0268"
              and game["date"]=="2024-04-13"
              and (game["away"],game["home"])==("Virginia Tech","Georgia Tech")
              and item["official_score"]==[0,19]
              and item["source_url"]=="https://storage.googleapis.com/ramblinwreck-com-prod/2024/04/gt041324.pdf")
    innings_expected=legacy[1] if legacy else (7 if apr13_gt else 9)
    # Named schools must both occur in the original document heading.
    header=" ".join(first[:6])
    if not all(re.search(re.escape(t),header,re.I) for t in (game["away"],game["home"])):
        raise ValueError("Wrong official PDF team pairing")
    dh=item.get("official_doubleheader_game")
    if dh and not re.search(r"\(Game\s+"+str(dh)+r"\)",text,re.I):
        raise ValueError("Wrong Vanderbilt doubleheader PDF game number")
    if not dh and re.search(r"\(Game\s+[12]\)",text,re.I):
        raise ValueError("March 24 PDF incorrectly points to March 23 doubleheader")
    teams=(game["away"],game["home"])
    scores=item["official_score"]
    batting={t:[] for t in teams};pitching={t:[] for t in teams}
    totals={}; innings={};batteam=None;pitchteam=None;mode=None
    for original in first:
        line=original.strip()
        header=next((t for i,t in enumerate(teams) if re.fullmatch(re.escape(t)+r"\s+"+str(scores[i])+r"\s+\([^)]*\)",line)),None)
        if header:
            batteam=header;mode="bat_header";continue
        if line.lower().startswith("player ab r h rbi bb so"):
            mode="bat";continue
        if line.startswith("Totals ") and mode=="bat" and batteam:
            values=line.split()[1:]
            if len(values)!=9 or not all(x.isdigit() for x in values):raise ValueError("Incomplete printed university batting totals")
            totals[batteam]=list(map(int,values)); mode="closed";continue
        pm=next((t for t in teams if re.match(re.escape(t)+r"\s+ip\s+h\s+r\s+er\s+bb\s+so\s+ab\s+bf\s+np",line,re.I)),None)
        if pm:
            pitchteam=pm;mode="pitch";continue
        if mode=="bat" and batteam:
            m=re.match(r"^\s*(.*?)\s+((?:\d+\s+){8}\d+)\s*$",original)
            if m:
                from import_2024_statcrew import split_player
                name,pos=split_player(m.group(1))
                vals=list(map(int,m.group(2).split()))
                batting[batteam].append((name,pos,vals,original.startswith((" ","\t","\u00a0"))))
        if mode=="pitch" and pitchteam:
            m=re.match(r"^(.+?)\s+(\d+\.[012])\s+((?:\d+\s+){7}\d+)\s*$",line)
            if m:
                name=normalize_name(m.group(1))
                ip=m.group(2)
                vals=list(map(int,m.group(3).split()))
                pitching[pitchteam].append((name,3*int(ip.split(".")[0])+int(ip.split(".")[1]),vals))
        if "Score by Innings" in line:
            mode="score"
            continue
        if mode=="score":
            for t in teams:
                if not line.startswith(t+" "):continue
                vals=line[len(t):].split()
                if len(vals)==innings_expected+3 and all(x.isdigit() or x.casefold()=="x" for x in vals):
                    run,hit,err=map(int,vals[-3:])
                    invals=[int(x) if x.isdigit() else None for x in vals[:-3]]
                    if sum(n or 0 for n in invals)!=run:raise ValueError("Printed inning runs do not sum to game total")
                    innings[t]={"innings":invals,"runs":run,"hits":hit,"errors":err}
    if set(innings)!=set(teams) or [innings[t]["runs"] for t in teams]!=scores:
        raise ValueError("Official PDF lacks correctly ordered complete R/H/E and inning scores")
    if any(len(innings[t]["innings"])!=innings_expected for t in teams):
        raise ValueError("Official PDF did not match verified game inning count")
    if set(totals)!=set(teams) or any(not pitching[t] for t in teams):
        raise ValueError("Both original PDF batting and pitching tables required")
    rows={};lineups=[]
    def add(team,name):
        pid="cb-"+slug(team)+"-"+slug(name)
        if pid not in rows:
            rows[pid]={"game_id":game["id"],"player_id":pid,"player":name,"team":team,
                "source_url":item["source_url"],"source_type":"official_university_pdf_gamebook",
                "verification":"official_boxscore_verified"}
        return rows[pid]
    source_defensive={
       ("cb-2024-03-23-vanderbilt-south-carolina-att0260","South Carolina"):{"Evan Stone"},
       ("cb-2024-03-23-vanderbilt-south-carolina-att0261","Vanderbilt"):{"Jacob Humphrey"},
       ("cb-2024-03-23-vanderbilt-south-carolina-att0261","South Carolina"):{"Gavin Casas"},
       ("cb-2024-02-23-iowa-auburn-att0235","Auburn"):{"Deric Fabian"},
       ("cb-2024-04-14-virginia-tech-georgia-tech-att0268","Georgia Tech"):{"Tyler Minnick"},
       # Cincinnati 2018 second game: unindented defensive SS replaces
       # PH Kevin Collard in starter Jeff Houghtby's ninth batting slot.
       ("cb-2018-02-18-cincinnati-san-diego-att0006","San Diego"):{"Trevor Rosenburg"},
    }
    for i,t in enumerate(teams):
        bat=batting[t]
        if not bat or len(bat)<9:raise ValueError("PDF batter rows missing for "+t)
        # GT starting pitcher Cam Jones ALSO batted fifth (1 AB, four BB);
        # VT pitchers listed after batting totals did not enter the order.
        # This is an officially documented two-way starting batting spot.
        hitter=[x for x in bat if x[1]!="p" or
                (apr13_gt and t=="Georgia Tech" and x[0]=="Cam Jones")]
        source_summary=totals[t]
        for k in range(6):
            if sum(x[2][k] for x in bat)!=source_summary[k]:
                raise ValueError("PDF batter column differs from printed Totals for "+t+" "+str(k))
        if source_summary[1:3]!=[innings[t]["runs"],innings[t]["hits"]]:
            raise ValueError("PDF batting totals conflict with scoreboard for "+t)
        slots=[]
        for ix,(name,pos,vals,indent) in enumerate(hitter):
            sub=(indent or pos.startswith(("ph","pr"))
                 or name in source_defensive.get((game["id"],t),set()))
            if sub:
                if not slots:raise ValueError("PDF sub preceded batting starter")
                slot=len(slots);sub_index=len(slots[-1]);slots[-1].append(name)
            else:
                slots.append([name]);slot=len(slots);sub_index=0
            p=add(t,name)
            p.update({"position":pos,"batting_slot":slot,"batting_sub_index":sub_index,
                      "batting_appearance_index":ix})
            ab,r,h,rbi,bb,so,po,a,lob=vals
            p["batting"]={"atBats":ab,"runs":r,"hits":h,"rbi":rbi,"baseOnBalls":bb,
                          "strikeOuts":so}
        if len(slots)!=9:
            raise ValueError("PDF starters not exactly nine: "+t+" "+str(slots))
        for ix,(name,outs,vals) in enumerate(pitching[t]):
            p=add(t,name)
            p["pitching"]={"outs":outs,"hits":vals[0],"runs":vals[1],
                "earnedRuns":vals[2],"baseOnBalls":vals[3],"strikeOuts":vals[4],
                "numberOfPitches":vals[-1]}
            p["pitching_appearance_index"]=ix
        if sum(x[2][1] for x in pitching[t])!=innings[teams[1-i]]["runs"]:
            raise ValueError(t+" pitcher runs do not equal opponent runs")
        if sum(x[2][0] for x in pitching[t])!=innings[teams[1-i]]["hits"]:
            raise ValueError(t+" pitcher hits do not equal opponent hits")
        if sum(x[1] for x in pitching[t])!=source_summary[6]:
            raise ValueError(t+" original pitching outs do not reconcile with official "+str(innings_expected)+"-inning final")
        lineups.append({"team":t,"nine_starting_slots":True,
                        "batter_rows":len(hitter),"pitcher_rows":len(pitching[t]),
                        "substitutes":len(hitter)-9})
    if len(rows)!=len({x["player_id"] for x in rows.values()}):
        raise ValueError("PDF contains duplicate player identity")
    decision_labels={}
    for label in ("Win","Loss","Save"):
        m=re.search(r"\b"+label+r"\s*-\s*([A-Za-z'. ,-]+?)\s*\((\d+(?:-\d+)?)\)",text,re.I)
        if not m and label=="Save" and re.search(r"Save\s*-\s*None",text,re.I):
            decision_labels[label.lower()]=None;continue
        if not m:raise ValueError("Official PDF missing explicit scorer "+label)
        name=m.group(1).strip()
        def identify(p):
            # University PDFs abbreviate decisions "Tilly, C.", "M. Siverling"
            # and "Thomas, B". Match team source full names uniquely.
            source=re.findall(r"[a-z]+",name.lower())
            actual=re.findall(r"[a-z]+",p["player"].lower())
            if not source or not actual:return False
            if source==actual:return True
            if len(source)==1:return source[0]==actual[-1]
            if len(source)==2:
                return (source[0]==actual[-1] and actual[0].startswith(source[1][0])
                    or source[-1]==actual[-1] and actual[0].startswith(source[0][0]))
            return False
        candidates=[p for p in rows.values() if "pitching" in p and identify(p)]
        if len(candidates)!=1:raise ValueError("PDF official "+label+" pitcher not uniquely identified: "+name)
        decision_labels[label.lower()]=candidates[0]["player"]
    if decision_labels["win"]==decision_labels["loss"]:raise ValueError("Same winner/loser in official scorer")
    for p in rows.values():
        if "pitching" in p:
            for key,field in (("win","wins"),("loss","losses"),("save","saves")):
                p["pitching"][field]=int(p["player"]==decision_labels[key]) if decision_labels[key] else 0
    result=list(rows.values());keys={(p["game_id"],p["player_id"]) for p in result}
    if keys & global_keys or len(keys)!=len(result) or len(result)<18:
        raise ValueError("Official PDF player ID collision or incomplete roster")
    game.update({"source_url":item["source_url"],"verification":"official_boxscore_verified",
        "official_boxscore_status":"verified","score_provenance":"official_pdf_gamebook",
        "away_score":scores[0],"home_score":scores[1],
        "away_hits":innings[teams[0]]["hits"],"home_hits":innings[teams[1]]["hits"],
        "away_errors":innings[teams[0]]["errors"],"home_errors":innings[teams[1]]["errors"],
        "pitching_decisions":decision_labels,
        "innings":[{"inning":j+1,"away":aa,"home":bb} for j,(aa,bb) in enumerate(
           zip(innings[teams[0]]["innings"],innings[teams[1]]["innings"]))]})
    global_keys.update(keys)
    audit={"status":"PASS","source":item["source_url"],
      "source_sha256":hashlib.sha256(response.content).hexdigest(),
      "source_type":"official_university_pdf_gamebook","player_rows":len(result),
      "lineup_audit":lineups,"scoreboard":[innings[t] for t in teams],
      "pitching_decisions":decision_labels}
    if legacy:
        audit["archive_source_header_date"]="2018-02-17"
        audit["verified_official_schedule_date"]=game["date"]
        audit["date_discrepancy_evidence"]="Original Cincinnati/SD official Feb 18 schedule, scored Game 1/Game 2 PDFs marked Feb 17"
        audit["source_game_number"]=legacy[0]
    return result,audit
