#!/usr/bin/env python3
"""Restrict Banana Ball archive crossover candidates to regular team players.

A played-game record alone is insufficient (many MLB veterans have guest cameos).
A sustained same-team recorded stint is a screening SIGNAL, not proof of an
employment contract. Current official team rosters are separate corroboration,
never proof of a past season's full-time status.
The script does not add player tags without validated identities.
"""
import json
import re
import time
import unicodedata
from datetime import datetime
from pathlib import Path
import requests
from bs4 import BeautifulSoup

ROOT=Path(__file__).resolve().parents[2]
SOURCE=ROOT/"college-baseball/data/banana_ball_crossover_audit.json"
OUTPUT=ROOT/"college-baseball/data/banana_ball_regular_roster_audit.json"

OFFICIAL_TEAMS={
    "Savannah Bananas":"https://bananaball.com/savannah-bananas/",
    "Party Animals":"https://bananaball.com/party-animals/",
    "Firefighters":"https://bananaball.com/thefirefighters/",
    "Texas Tailgaters":"https://bananaball.com/the-texas-tailgaters/",
    "Loco Beach Coconuts":"https://bananaball.com/locobeachcoconuts/",
    "Indianapolis Clowns":"https://bananaball.com/indianapolisclowns/",
}
DATE_RX=re.compile(r"Recorded stint:\s*([A-Za-z]+ \d{1,2}, \d{4})(?:\s*[–—-]\s*([A-Za-z]+ \d{1,2}, \d{4}))?",re.I)
ROLE_EXCLUDED=re.compile(r"coach|manager|staff|general manager|mascot|entertainer only",re.I)

def norm(v):
    v=unicodedata.normalize("NFKD",str(v or "")).encode("ascii","ignore").decode().lower()
    return re.sub(r"[^a-z0-9]","",v)

def get_html(session,url):
    last=None
    for attempt in range(3):
        try:
            r=session.get(url,timeout=30)
            r.raise_for_status()
            if len(r.text)<500:raise ValueError("truncated response")
            return r.text
        except (requests.RequestException,ValueError) as e:
            last=str(e)
            time.sleep(2+attempt*2)
    raise RuntimeError(f"{url}: {last}")

def official_roster(session,team,url):
    html=get_html(session,url)
    doc=BeautifulSoup(html,"html.parser")
    active=False; members=[]
    for h in doc.find_all(["h2","h3"]):
        name=h.get_text(" ",strip=True)
        if h.name=="h2":
            if name.lower()=="the roster":active=True
            elif active:break
        elif active and name and not ROLE_EXCLUDED.search(name):
            # Some headings may be coaches; this is a secondary roster reference only
            next_text=h.find_next(string=True)
            members.append(name)
    if len(members)<8:
        raise RuntimeError(f"Only {len(members)} players detected for official {team} roster; parser needs review")
    return sorted(set(members))

def history(session,url):
    soup=BeautifulSoup(get_html(session,url),"html.parser")
    body=(soup.find("main") or soup).get_text(" ",strip=True)
    ranges=[]
    for a,b in DATE_RX.findall(body):
        try:
            start=datetime.strptime(a,"%B %d, %Y")
            end=datetime.strptime(b,"%B %d, %Y") if b else start
            if end<start:continue
            ranges.append({"start":start.date().isoformat(),"end":end.date().isoformat(),"span_days":(end-start).days})
        except ValueError:continue
    return list({(r["start"],r["end"]):r for r in ranges}.values())

def run():
    initial=json.loads(SOURCE.read_text())
    session=requests.Session()
    session.headers.update({"User-Agent":"Mozilla/5.0 (CourtsideArchive Banana Ball eligibility review)"})
    roster={};errors={}
    for team,url in OFFICIAL_TEAMS.items():
        try:
            roster[team]={"url":url,"names":official_roster(session,team,url)}
            print("ROSTER",team,len(roster[team]["names"]),flush=True)
        except Exception as exc:
            errors[team]=str(exc)
            print("ROSTER ERROR",team,str(exc),flush=True)
    if len(roster)<5:
        raise RuntimeError("Most official rosters unavailable; aborting review without mislabeling player status.")
    normed_rosters={team:{norm(n) for n in item["names"]} for team,item in roster.items()}
    reviews=[]
    for i,p in enumerate(initial["recorded_game_candidates"],1):
        name=p["banana_ball_name"]
        games=p["appearance"]
        same_year=games.get("first_recorded_game","")[:4]
        current_roster=[team for team,names in normed_rosters.items() if norm(name) in names]
        try:
            stints=history(session,p["url"])
            error=None
        except Exception as e:
            stints=[]
            error=str(e)
        longest=max((st["span_days"] for st in stints),default=0)
        years=sorted({d["start"][:4] for d in stints}|{d["end"][:4] for d in stints})
        # Candidate threshold: at least six weeks between documented played dates.
        # This is not final full-time confirmation: check roster/source identity.
        if longest>=42:
            status="regular_play_candidate_needs_identity_and_roster_review"
        elif current_roster and "2026" in years:
            status="official_roster_candidate_needs_year_and_appearance_review"
        elif error:
            status="historical_stint_fetch_failed"
        else:
            status="exclude_guest_or_insufficient_regular_evidence"
        reviews.append({
          "name":name,
          "archive_records":p["archive_records"],
          "source_url":p["url"],
          "source_played_game_date":games.get("first_recorded_game"),
          "historical_stints":stints,
          "longest_recorded_stint_days":longest,
          "official_current_roster_listed_with":current_roster,
          "roster_evidence_urls":[roster[t]["url"] for t in current_roster],
          "source_error":error,
          "status":status,
        })
        if i%15==0:print("REVIEW",i,len(initial["recorded_game_candidates"]),flush=True)
        time.sleep(0.3)
    candidates=[x for x in reviews if x["status"]!="exclude_guest_or_insufficient_regular_evidence"]
    regulars=[x for x in reviews if x["status"].startswith("regular_play_candidate")]
    ignored=[x for x in reviews if x["status"]=="exclude_guest_or_insufficient_regular_evidence"]
    summary={
       "policy":"REGULAR TEAM MEMBERS ONLY. Exclude guest appearances, one-off celebrity cameos, draft-only and roster-only players. Historical and former full-time members can qualify.",
       "source":"2020–2026 participation records with dated team stints; present official roster reference does not prove older historical employment.",
       "previously_reported_mlb_name_matches":54,
       "candidate_name_matches_total":len(reviews),
       "sustained_stint_candidates":len(regulars),
       "all_followup_candidacies":len(candidates),
       "not_regular_or_insufficient":len(ignored),
       "status_counts":{s:sum(x["status"]==s for x in reviews) for s in sorted({x["status"] for x in reviews})},
       "by_level_candidates":{level:len({str(r["player_id"]) for x in candidates for r in x["archive_records"] if r["level"]==level}) for level in ("NCAA","MiLB","MLB")},
       "roster_fetch_errors":errors,
       "tags_published":0,
       "note":"42+ day span between recorded game appearances screens likely regular members; it does not automatically establish full-time contractual status, and every name/identity requires final corroboration."
    }
    out={"summary":summary,"official_roster_reference":{t:{"url":item["url"],"names_count":len(item["names"])} for t,item in roster.items()},"followup_candidates":candidates,"excluded_or_no_regular_evidence":ignored}
    OUTPUT.write_text(json.dumps(out,indent=2,ensure_ascii=False)+"\n")
    print(json.dumps(summary,indent=2),flush=True)
    for x in candidates:
        print("REGULAR CANDIDATE",x["name"],x["status"],x["longest_recorded_stint_days"],[(r["level"],r["player_id"]) for r in x["archive_records"]],flush=True)
    if any(x["status"]=="historical_stint_fetch_failed" for x in candidates):
        raise RuntimeError("Some profiles failed to fetch. Incomplete candidate screening - see report.")
if __name__=="__main__":
    run()
