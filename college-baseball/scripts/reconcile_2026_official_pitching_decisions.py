#!/usr/bin/env python3
"""Reconcile remaining 2026 NCAA gamebook pitching W/L/S with official scorer.

The Sidearm source feed often prints surname-first W/L ("Kuhns, Tegan")
while player-stat lines use given-first ("Tegan Kuhns"). This script checks
those against the actual pitchers in every Feb/Mar 2026 newly imported HTML
gamebook, credits exactly one win/loss and any documented save, and zeros all
others. Does not touch previously audited April/May or the March 1 PDF.
"""
from pathlib import Path
import json
import re
import unicodedata
import requests
from bs4 import BeautifulSoup

D=Path(__file__).resolve().parents[1]/"data"
IDS=[
 "cb-2026-02-13-nicholls-tennessee-att0375",
 "cb-2026-02-14-nicholls-tennessee-att0376",
 "cb-2026-02-14-nicholls-tennessee-att0377",
 "cb-2026-02-15-michigan-state-louisville-att0378",
 "cb-2026-02-18-eastern-michigan-vanderbilt-att0379",
 "cb-2026-02-20-marist-vanderbilt-att0380",
 "cb-2026-02-21-marist-vanderbilt-att0381",
 "cb-2026-02-22-marist-vanderbilt-att0382",
 "cb-2026-03-06-the-citadel-kentucky-att0384",
 "cb-2026-03-07-the-citadel-kentucky-att0385",
 "cb-2026-03-08-the-citadel-kentucky-att0386",
 "cb-2026-03-10-ohio-austin-peay-att0387",
 "cb-2026-03-10-ohio-austin-peay-att0388",
 "cb-2026-03-10-indiana-state-vanderbilt-att0389",
 "cb-2026-03-13-austin-peay-bellarmine-att0391",
 "cb-2026-03-14-alabama-kentucky-att0393",
]

def load(n):return json.loads((D/n).read_text(encoding="utf-8"))
def dump(n,j):(D/n).write_text(json.dumps(j,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
def name_variants(name):
    s=re.sub(r"\s+"," ",name.strip())
    if "," in s:
        last,first=s.split(",",1)
        s=first.strip()+" "+last.strip()
    norm=lambda x:re.sub(r"[^a-z0-9]+","",unicodedata.normalize("NFKD",x).encode("ascii","ignore").decode().lower())
    words=s.split()
    return {norm(s),norm(" ".join(words[::-1]))}

def extract(html):
    soup=BeautifulSoup(html,"html.parser")
    text=soup.get_text(" ",strip=True)
    result={}
    for label in ("Win","Loss","Save"):
        if label in ("Win","Loss"):
            pat=rf"\b{label}\s*:\s*(.*?)\s*\(\d+-\d+\)"
        else:
            pat=rf"\b{label}\s*:\s*(.*?)\s*\(\d+\)"
        match=re.search(pat,text,re.I)
        if match:result[label.lower()]=match.group(1).strip(" ,;.")
        elif label=="Save":result["save"]=None
        else:raise ValueError(f"Could not extract official {label} pitcher name")
    return result

def main():
    games=load("games.json")
    players=load("player_stats.json")
    audit=load("2026_full_slate_monthly_integrity_audit.json")
    byid={g["id"]:g for g in games}
    if len(games)!=444 or audit["complete_official_player_gamebooks"]!=68:raise ValueError("Season not ready")
    reviews=[]
    session=requests.Session()
    session.headers["User-Agent"]="Mozilla/5.0 CollegeBaseball Source Gamebook Audit"
    for gid in IDS:
        game=byid[gid]
        if game["verification"]!="official_boxscore_verified" or game.get("boxscore_backfill_excluded"):
            raise ValueError("Game unexpectedly not source-verified: "+gid)
        url=game["source_url"]
        response=session.get(url,timeout=35)
        response.raise_for_status()
        found=extract(response.text)
        pitchers=[r for r in players if r["game_id"]==gid and "pitching" in r]
        if len(pitchers)<2:
            raise ValueError("Missing official pitchers: "+gid)
        mapped={}
        for k in ("win","loss","save"):
            source=found[k]
            if source is None:
                if k!="save":raise ValueError("No official winner/loser: "+gid)
                mapped[k]=None
                continue
            matches=[p for p in pitchers if name_variants(p["player"]) & name_variants(source)]
            if len(matches)!=1:
                raise ValueError("Cannot match official "+k+" "+repr(source)+" in "+gid+": "+str([p["player"] for p in pitchers]))
            mapped[k]=matches[0]["player"]
        if len({mapped["win"],mapped["loss"]})!=2:
            raise ValueError("Official W and L pitchers cannot be same person")
        for p in pitchers:
            for k,field in (("win","wins"),("loss","losses"),("save","saves")):
                p["pitching"][field]=int(mapped[k] is not None and p["player"]==mapped[k])
        game["pitching_decisions"]=mapped
        # The two February 14 Tennessee–Nicholls entries are separate
        # official 1:02pm (G1) and 4:32pm (G2) gamebooks; retain the user's
        # source worksheet order but flag attendance-row confirmation.
        if gid=="cb-2026-02-14-nicholls-tennessee-att0376":
            game["game_number"]=1
            game["attendance_segment_confirmation_pending"]=True
        elif gid=="cb-2026-02-14-nicholls-tennessee-att0377":
            game["game_number"]=2
            game["attendance_segment_confirmation_pending"]=True
        reviews.append({"game_id":gid,"source_url":url,"official_decisions":found,
                        "reconciled_player_decisions":mapped,"source_pitchers":len(pitchers)})
        print("PASS SOURCE W/L/S",gid,mapped,flush=True)
    assert len(reviews)==16
    assert sum(1 for r in players if r["game_id"] in IDS and r.get("pitching",{}).get("wins")==1)==16
    assert sum(1 for r in players if r["game_id"] in IDS and r.get("pitching",{}).get("losses")==1)==16
    dump("games.json",games)
    dump("player_stats.json",players)
    dump("2026_feb_march_pitching_decisions_audit.json",
         {"status":"PASS","gamebooks":len(reviews),"checks":reviews,
          "notes":"Win/loss/save exact source scorer parity, independent credited pitcher membership"})
    print("PASS official Feb/Mar 2026 pitching scorer",len(reviews),"games",flush=True)


if __name__=="__main__":
    main()
