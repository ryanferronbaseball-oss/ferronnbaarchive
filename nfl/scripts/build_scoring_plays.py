#!/usr/bin/env python3
"""Create audited scoring chronology from archived ESPN scoring plays + full play descriptions."""
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
games=json.loads((ROOT/"data/games.json").read_text())
allgames={}
for g in games:
    f=ROOT/"data/raw"/(g["id"]+".json")
    doc=json.loads(f.read_text())
    originals=doc.get("scoringPlays") or []
    playmap={str(play.get("id")):play
      for d in (doc.get("drives") or {}).get("previous",[])
      for play in d.get("plays",[])}
    timeline=[]
    prevaway=prevhome=0
    for e in originals:
        away=int(e.get("awayScore") or 0)
        home=int(e.get("homeScore") or 0)
        # ESPN's scoring summary has occasional redundant XP events where
        # the TD row already includes the 7th point in the running score.
        pointdelta=(away-prevaway)+(home-prevhome)
        assert pointdelta>=0,(g["id"],e.get("id"),pointdelta)
        e_type=(e.get("type") or {}).get("text","")
        xpoint=("Extra Point" in e_type or "Two Point" in e_type or "2 Point" in e_type)
        play=playmap.get(str(e.get("id")),{})
        description=play.get("text") or e.get("text") or e_type
        # Existing touchdown rows can include a conversion in their scoreboard.
        if xpoint and timeline and timeline[-1]["kind"]=="touchdown":
            td=timeline[-1]
            if td["period"]==int((e.get("period") or {}).get("number") or 1) and td["team"]==(e.get("team") or {}).get("abbreviation"):
                td["conversion"]=description if description not in ("PAT","Extra Point") else e_type
                td["away_score"]=away
                td["home_score"]=home
                td["points"]+=pointdelta
                prevaway,prevhome=away,home
                continue
        if pointdelta==0:
            # Keep only actual scoring changes; audit count retained separately.
            prevaway,prevhome=away,home
            continue
        lower=e_type.lower()
        kind=("touchdown" if "touchdown" in lower else
              "field_goal" if "field goal" in lower else
              "safety" if "safety" in lower else
              "conversion" if xpoint else "other")
        timeline.append({
          "id":str(e.get("id") or ""),
          "period":int((e.get("period") or {}).get("number") or 1),
          "clock":(e.get("clock") or {}).get("displayValue") or "",
          "team":(e.get("team") or {}).get("abbreviation") or "",
          "kind":kind,
          "type":e_type,
          "description":description,
          "points":pointdelta,
          "away_score":away,
          "home_score":home,
          "conversion":None,
          "source":"Archived ESPN NFL scoring summary and drive play-by-play"
        })
        prevaway,prevhome=away,home
    assert (prevaway,prevhome)==(g["away_score"],g["home_score"]),(g["id"],prevaway,prevhome,g["away_score"],g["home_score"])
    assert sum(t["points"] for t in timeline)==g["away_score"]+g["home_score"]
    assert len(timeline)>=7,(g["id"],len(timeline))
    allgames[g["id"]]={"plays":timeline,"source_scoring_events":len(originals),
                         "score_verified":True,"final_score":{"away":prevaway,"home":prevhome}}
    print(g["id"],len(timeline),"scoring entries,",len(originals),"source events",flush=True)
(ROOT/"data/scoring_plays.json").write_text(json.dumps(allgames,indent=2)+"\n")
