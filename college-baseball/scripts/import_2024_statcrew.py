#!/usr/bin/env python3
"""Parse original university StatCrew HTML with strict R/H/E, inning, lineup, pitching checks."""
import re,hashlib
from bs4 import BeautifulSoup
from import_sidearm_pilot import slug,normalize_name
POS=r"(?:ph|pr|dh|lf|cf|rf|ss|1b|2b|3b|c|p)"
def split_player(text):
    m=re.match(r"^(.+?)\s+("+POS+r"(?:/"+POS+r")*)$",text.strip(),re.I)
    if not m:raise ValueError("StatCrew player/position unreadable: "+text)
    return normalize_name(m.group(1)),m.group(2).lower()
def line_score(text,expected):
    out=[]
    for l in text.splitlines():
        m=re.match(r"^\s*(.+?)\.{2,}\s+([0-9xX ]+)\s+-\s+(\d+)\s+(\d+)\s+(\d+)\s*$",l)
        if not m:continue
        inns=[None if c.lower()=="x" else int(c) for c in re.sub(r"\s","",m.group(2))]
        runs,hits,errors=map(int,m.groups()[2:])
        if not 7<=len(inns)<=18 or sum(x or 0 for x in inns)!=runs:continue
        out.append(dict(innings=inns,runs=runs,hits=hits,errors=errors))
        if len(out)==2:break
    if len(out)!=2 or [x["runs"] for x in out]!=expected:
        raise ValueError("Original StatCrew innings/RHE not consistent with attendance game")
    return out
def parse_bats(soup,first_pre,teams):
    all_bats={};team=None;active=False
    if first_pre:
        iterable=[(l,l.strip(),len(l)-len(l.lstrip())) for l in first_pre.splitlines()]
    else:
        tb=next((t for t in soup.find_all("table") if "Player" in t.get_text(" ",strip=True)
                 and "Totals" in t.get_text(" ",strip=True)),None)
        if tb is None:raise ValueError("No original university batting tables")
        iterable=[]
        for tr in tb.find_all("tr"):
            val=tr.get_text(" ",strip=True)
            cells=tr.find_all(["td","th"],recursive=False)
            lead=cells[0].get_text(" ",strip=False) if cells else ""
            indent=2 if lead.startswith(("  ","\xa0\xa0")) else 0
            iterable.append((val,val,indent))
    for original,line,indent in iterable:
        for t in teams:
            if re.match(re.escape(t)+r"(?: \(Fla\.\))?\s+\d+\s*\(",line,re.I):
                team=t;all_bats[t]=[];active=False;break
        else:
            if line.lower().startswith("player ") and "rbi" in line.lower():
                active=True;continue
            if not team or not active or line.startswith("Totals"):continue
            m=(re.match(r"^\s*(.*?)\.{2,}\s+((?:\d+\s+){8}\d+)\s*$",original)
               if first_pre else re.match(r"^(.*?)\s+((?:\d+\s+){8}\d+)\s*$",line))
            if not m:continue
            name,pos=split_player(m.group(1))
            all_bats[team].append((name,pos,list(map(int,m.group(2).split())),indent>0))
    return all_bats
def pitch_rows(soup,first_pre,teams):
    if first_pre:lines=first_pre.splitlines()
    else:
        t=next((t for t in soup.find_all("table") if re.search(r"\bip\s+h\s+r\s+er\s+bb\s+so\b",
                t.get_text(" ",strip=True),re.I)),None)
        if t is None:raise ValueError("Missing StatCrew university pitching table")
        lines=[tr.get_text(" ",strip=True) for tr in t.find_all("tr") if not tr.find("tr")]
    out={t:[] for t in teams};team=None
    for l in lines:
        s=l.strip()
        matched=False
        for t in teams:
            if re.match(re.escape(t)+r"(?: \(Fla\.\))?\s+ip\s+h\s+r\s+er\s+bb\s+so\b",s,re.I):
                team=t;matched=True;break
        if matched or team is None:continue
        # No partial pitcher lines; require IP plus 7..15 original integers.
        m=re.match(r"^(.+?)(?:\.{2,}|\s{2,}|\s+)(?:([WLS]),\d+(?:-\d+)?\s+)?(\d+\.[012])\s+((?:\d+\s+){6,14}\d+)\s*$",s)
        if not m:continue
        vals=list(map(int,m.group(4).split()))
        if not 7<=len(vals)<=15:continue
        name=normalize_name(m.group(1).strip(" ."))
        outs=int(m.group(3).split(".")[0])*3+int(m.group(3).split(".")[1])
        if any(x[0]==name for x in out[team]):continue
        out[team].append((name,outs,vals))
    return out
def decision(text,key):
    pat=(r"\bSave\s*-\s*(.+?)\s*\(\d+\)" if key=="save"
         else r"\b"+key.capitalize()+r"\s*-\s*(.+?)\s*\(\d+-\d+\)")
    if key=="save" and re.search(r"\bSave\s*-\s*None",text,re.I):return None
    m=re.search(pat,text,re.I|re.S)
    if not m:
        if key=="save":return None
        raise ValueError("StatCrew source has no "+key+" decision")
    return m.group(1).strip(" ,.;")
def match_pitcher(name,pitchers):
    if name is None:return None
    n=re.sub(r"[.,]"," ",name).casefold().split()
    hits=[]
    for p in pitchers:
        terms=p["player"].casefold().split()
        if (terms==n or (terms[-1] in n and (len(n)==1 or
              terms[0][0] in n[0] or n[-1]==terms[-1])) or
              (len(n)==1 and terms[-1]==n[0])):
            hits.append(p)
    if len(hits)!=1:raise ValueError("Ambiguous original StatCrew pitcher "+name+" "+str([x["player"] for x in hits]))
    return hits[0]["player"]
def import_statcrew(game,item,global_keys,response):
    soup=BeautifulSoup(response.text,"html.parser")
    pres=[p.get_text() for p in soup.find_all("pre")]
    if not any("Score by Innings" in p for p in pres):raise ValueError("No original StatCrew scoreboard pre")
    first_pre=next((p for p in pres if "Player" in p and "Score by Innings" in p),None)
    score=line_score("\n".join(pres),item["official_score"])
    teams=(game["away"],game["home"])
    bats=parse_bats(soup,first_pre,teams);pitches=pitch_rows(soup,first_pre,teams)
    if any(t not in bats or len(bats[t])<9 or not pitches[t] for t in teams):
        print("STATCREW-STRUCTURE",game["id"],"bats",{k:len(v) for k,v in bats.items()},
            "pitches",{k:len(v) for k,v in pitches.items()},
            "first_trows",[tr.get_text(" ",strip=True)[:200]
                          for t in soup.find_all("table") for tr in t.find_all("tr")
                          if not tr.find("tr") and "ip h r er" in tr.get_text(" ",strip=True).lower()][:4],
            "pitch-table",[tr.get_text(" ",strip=True)[:135] for t in soup.find_all("table")
                 if "ip h r er" in t.get_text(" ",strip=True).lower()
                 for tr in t.find_all("tr") if not tr.find("tr")][:10],
            flush=True)
        raise ValueError("Original source missing team batting/pitching lines")
    records={};lineups=[]
    def row(team,name):
        pid="cb-"+slug(team)+"-"+slug(name)
        if pid not in records:
            records[pid]={"game_id":game["id"],"player_id":pid,"player":name,"team":team,
                          "source_url":item["source_url"],"source_type":"official_university_statcrew_html",
                          "verification":"official_boxscore_verified"}
        return records[pid]
    for i,team in enumerate(teams):
        hitters=[x for x in bats[team] if x[1]!="p" or any(x[2][:6])]
        lineup=[];was_sub=False
        for n,(name,pos,values,indent) in enumerate(hitters):
            sub=indent or pos.startswith(("ph","pr")) or (was_sub and len(lineup)>=9)
            if sub:
                if not lineup:raise ValueError(team+": sub before starter")
                idx=len(lineup[-1]);lineup[-1].append(name)
            else:
                lineup.append([name]);idx=0
            was_sub=sub
            person=row(team,name);person["position"]=pos
            person["batting_slot"]=len(lineup)
            person["batting_sub_index"]=idx
            person["batting_appearance_index"]=n
            ab,r,h,rbi,bb,so,po,a,lob=values
            person["batting"]={"atBats":ab,"runs":r,"hits":h,"rbi":rbi,"baseOnBalls":bb,"strikeOuts":so}
        if len(lineup)!=9:raise ValueError(team+": found "+str(len(lineup))+" source starting slots, expected nine")
        if (sum(x[2][1] for x in hitters),sum(x[2][2] for x in hitters))!=(score[i]["runs"],score[i]["hits"]):
            raise ValueError(team+": source player batting totals disagree with scoreboard")
        for n,(name,outs,vals) in enumerate(pitches[team]):
            person=row(team,name)
            person["pitching"]={"outs":outs,"hits":vals[0],"runs":vals[1],"earnedRuns":vals[2],
                               "baseOnBalls":vals[3],"strikeOuts":vals[4],
                               "numberOfPitches":vals[-1] if len(vals)>=15 else None}
            person["pitching_appearance_index"]=n
        team_pitch=[p["pitching"] for p in records.values() if p["team"]==team and "pitching" in p]
        if sum(p["runs"] for p in team_pitch)!=score[1-i]["runs"] or sum(p["hits"] for p in team_pitch)!=score[1-i]["hits"]:
            print("STATCREW-PITCH-REVIEW",game["id"], team,
                  [(x[0],x[1],x[2][:6]) for x in pitches[team]],
                  "totals",[(sum(p[k] for p in team_pitch)) for k in ("runs","hits")],
                  "opponents",score[1-i],flush=True)
            raise ValueError(team+": pitchers runs/hits do not reconcile with opponents")
        lineups.append({"team":team,"nine_starting_slots":True,"batter_rows":len(hitters),
                        "pitcher_rows":len(pitches[team]),"substitutes":len(hitters)-9})
    text=first_pre or soup.get_text(" ",strip=True)
    pitchers=[p for p in records.values() if "pitching" in p]
    decisions={k:match_pitcher(decision(text,k),pitchers) for k in ("win","loss","save")}
    if not decisions["win"] or not decisions["loss"] or decisions["win"]==decisions["loss"]:
        raise ValueError("Source winning and losing pitchers not fully resolved")
    for p in pitchers:
        for k,field in (("win","wins"),("loss","losses"),("save","saves")):
            p["pitching"][field]=int(p["player"]==decisions[k]) if decisions[k] else 0
    result=list(records.values())
    keys={(p["game_id"],p["player_id"]) for p in result}
    if len(keys)!=len(result) or keys & global_keys or len(result)<18:
        raise ValueError("Source identity collision or too few complete player lines")
    game.update({"source_url":item["source_url"],"verification":"official_boxscore_verified",
       "official_boxscore_status":"verified","score_provenance":"official_boxscore",
       "away_score":score[0]["runs"],"home_score":score[1]["runs"],
       "away_hits":score[0]["hits"],"home_hits":score[1]["hits"],
       "away_errors":score[0]["errors"],"home_errors":score[1]["errors"],
       "pitching_decisions":decisions,
       "innings":[{"inning":n+1,"away":a,"home":b} for n,(a,b) in enumerate(zip(score[0]["innings"],score[1]["innings"]))]})
    global_keys.update(keys)
    audit={"status":"PASS","game_id":game["id"],"source":item["source_url"],
           "source_bytes":len(response.content),"source_sha256":hashlib.sha256(response.content).hexdigest(),
           "player_rows":len(result),"scoreboard":score,"lineup_audit":lineups,
           "pitching_decisions":decisions,"source_type":"official_university_statcrew_html"}
    return result,audit
