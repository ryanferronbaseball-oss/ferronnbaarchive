#!/usr/bin/env python3
"""Step 2 source/contract/parity smoke checks. No external packages required."""
import csv
import json
import re
import subprocess
import tempfile
from pathlib import Path
from html.parser import HTMLParser

REPO=Path(__file__).resolve().parents[2]
COLLEGE=REPO/"college"

class Structure(HTMLParser):
    def __init__(self):
        super().__init__()
        self.tags=[]
        self.ids=set()
        self.nav_links=[]
        self.in_nav=False
        self.headings=[]
        self.pending_heading=None
    def handle_starttag(self, tag, attrs):
        a=dict(attrs)
        self.tags.append(tag)
        if "id" in a:
            assert a["id"] not in self.ids, "Duplicate DOM id " + a["id"]
            self.ids.add(a["id"])
        if tag=="nav": self.in_nav=True
        if self.in_nav and tag=="a" and a.get("href","").startswith("./"):
            self.nav_links.append(a["href"])
        if tag in ("h1","h2","h3"): self.pending_heading=tag
    def handle_endtag(self,tag):
        if tag=="nav":self.in_nav=False
        if tag in ("h1","h2","h3"):self.pending_heading=None

def structure(source):
    parser=Structure()
    parser.feed(source)
    return parser

def main():
    for filename in ("stats.html","player.html"):
        nba=(REPO/"nba"/filename).read_text(encoding="utf-8")
        college=(COLLEGE/filename).read_text(encoding="utf-8")
        a,b=structure(nba),structure(college)
        assert a.tags.count("table")==b.tags.count("table"), "Table count drift "+filename
        assert a.tags.count("h2")==b.tags.count("h2"), "Section hierarchy drift "+filename
        assert set(a.nav_links)==set(b.nav_links), "Navbar links changed "+filename
        assert a.ids.issubset(b.ids), "NBA DOM controls removed: "+str(a.ids-b.ids)
        assert '../assets/site.css?v=editorial-ivory-2' in college, "Not using same canonical stylesheet"
        assert '../assets/site.js?v=design-1' in college, "Not using existing nav logic"
        assert "./data/player_boxscores_espn.json" in college
        assert "./data/team_names.json" in college
        assert "https://www.espn.com/nba/boxscore/" not in college
        assert "headshots/nba/" not in college
        assert re.search(r'fetch\([^)]*player_boxscores_espn.json',college)
        assert "My NBA attendance" not in college
        assert "Atlanta Hawks" not in college and "Boston Celtics" not in college
        blocks=re.findall(r"<script(?:\s+[^>]*)?>([\s\S]*?)</script>",college)
        assert blocks, "No script content "+filename
        for index, script in enumerate(blocks):
            if not script.strip():continue
            with tempfile.NamedTemporaryFile(mode="w",suffix=".js",encoding="utf-8") as fh:
                fh.write(script)
                fh.flush()
                subprocess.run(["node","--check",fh.name],check=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
        # Calculations, advanced/stat categories and fields must be carried over unmodified.
        if filename=="stats.html":
            for prefix,next_prefix in [
                ("function aggregate(logs){","function redraw()"),
                ("function advancedRecord(a){","const advDefinitions"),
                ("const advDefinitions={","let leaderboardMode="),
            ]:
                a1=nba.index(prefix);a2=nba.index(next_prefix,a1)
                b1=college.index(prefix);b2=college.index(next_prefix,b1)
                assert nba[a1:a2]==college[b1:b2],"Calculation/stat category parity differs: "+prefix
            for marker in ('data-view="traditional"','data-view="advanced"','data-view="per36"'):
                assert marker in college,marker
        else:
            assert 'id="schoolFilter"' in college
            assert "schoolIds.length<2" in college
            assert "String(p.team_id)===schoolFilter.value" in college
            assert "headshots/mens-college-basketball/players/full/" in college
            for marker in ('data-tab="overview"','data-tab="advanced"','data-tab="games"','data-tab="milestones"'):
                assert marker in college
        print("PASS",filename,"same section count, canonical CSS, NBA math definitions preserved, JS syntax valid")
    games=list(csv.DictReader((COLLEGE/"data"/"games.csv").open(encoding="utf-8")))
    players=json.loads((COLLEGE/"data"/"player_boxscores_espn.json").read_text(encoding="utf-8"))
    teams=json.loads((COLLEGE/"data"/"team_names.json").read_text(encoding="utf-8"))
    assert len(games)==94 and len(players)==1825 and len(teams)==75
    assert all(str(p["team_id"]) in teams for p in players)
    assert len({p["espn_event_id"] for p in players})==94
    print("PASS",len(games),"games",len(players),"rows",len(teams),"school IDs")
    print("Step 2 source and schema smoke checks completed.")

if __name__=="__main__":
    main()
