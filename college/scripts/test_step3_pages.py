#!/usr/bin/env python3
"""NCAA Steps 2-3 page structure, source identity, and JS syntax regression."""
import csv
import json
import re
import subprocess
import tempfile
from html.parser import HTMLParser
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
PAGES=["index.html","game.html","stats.html","player.html","records.html","milestones.html","insights.html"]
NEW=PAGES[:2]+PAGES[4:]
COLLEGE=ROOT/"college"

class Structure(HTMLParser):
    def __init__(self):
        super().__init__()
        self.counts={}
        self.ids=set()
        self.links=[]
        self.nav=False
        self.nav_links=[]
        self.inputs=[]
    def handle_starttag(self,tag,attrs):
        d=dict(attrs)
        self.counts[tag]=self.counts.get(tag,0)+1
        if d.get("id"):
            assert d["id"] not in self.ids, "Duplicate DOM ID: "+d["id"]
            self.ids.add(d["id"])
        if tag=="nav":self.nav=True
        if tag=="a" and "href" in d:
            self.links.append(d["href"])
            if self.nav:self.nav_links.append(d["href"])
        if tag in ("select","input","button"):
            self.inputs.append((tag,d.get("id"),d.get("data-tab"),d.get("data-view")))
    def handle_endtag(self,tag):
        if tag=="nav":self.nav=False

def read_structure(html):
    result=Structure()
    result.feed(html)
    return result

def check(ok,label):
    if not ok:raise AssertionError(label)
    print("PASS",label,flush=True)

def main():
    for file in PAGES:
        original=(ROOT/"nba"/file).read_text(encoding="utf8")
        rendered=(COLLEGE/file).read_text(encoding="utf8")
        a,b=read_structure(original),read_structure(rendered)
        for tag in ("header","nav","h1","h2","h3","table","select","footer"):
            if tag=="select" and file=="player.html":
                check(b.counts.get(tag,0)==a.counts.get(tag,0)+1,file+" retains all NBA selectors plus optional school filter")
            else:
                check(a.counts.get(tag,0)==b.counts.get(tag,0),file+" has original NBA "+tag+" count")
        check(a.ids.issubset(b.ids),file+" preserves all NBA control IDs")
        check([x for x in b.nav_links if x!="./nba-alumni.html"]==a.nav_links and "./nba-alumni.html" in b.nav_links,file+" retains original NBA navigation plus the college career link")
        check(all((COLLEGE/ref.removeprefix("./")).is_file()
                  for ref in b.links if ref.startswith("./") and "?" not in ref and "#" not in ref),
              file+" links to existing college pages")
        check("../assets/site.css?v=editorial-ivory-2" in rendered and
              "../assets/site.js?v=design-1" in rendered,file+" uses identical canonical NBA theme/nav")
        check("./data/" in rendered,file+" uses college-scoped JSON/CSV")
        check("https://www.espn.com/nba/" not in rendered and
              "headshots/nba/players" not in rendered,file+" no NBA ESPN player URLs")
        blocks=re.findall(r"<script(?:\s+[^>]*)?>([\s\S]*?)</script>",rendered)
        check(bool(blocks),file+" has inline JS")
        for text in blocks:
            if not text.strip():continue
            with tempfile.NamedTemporaryFile(suffix=".js",mode="w",encoding="utf8") as tmp:
                tmp.write(text)
                tmp.flush()
                p=subprocess.run(["node","--check",tmp.name],capture_output=True,text=True)
                check(p.returncode==0,file+" inline JavaScript syntax "+p.stderr.strip()[:160])
        if file in NEW:
            check(not re.search(r"\bNBA\b|\bnba\b|2006-02-26|31-game archive",rendered.replace('<a href="./nba-alumni.html" data-nav="nba-alumni">To the NBA</a>', "")),
                  file+" has no inherited NBA-specific content")
    home=(COLLEGE/"index.html").read_text(encoding="utf8")
    check("2006-02-26" not in home and "parseCSV(csv)" in home,"Homepage uses imported data, not hardcoded NBA history")
    game=(COLLEGE/"game.html").read_text(encoding="utf8")
    check("String(p.game_id)===String(g.id)" in game and "NCAA" in game,
          "Game box scores join by attendance ID and show college sources")
    milestones=(COLLEGE/"milestones.html").read_text(encoding="utf8")
    check("byDateMatch=new Map(games.map(g=>[String(g.espn_event_id),g]))" in milestones and
          "String(p.game_id)===String(g.id)" in milestones,
          "Record game links use matched NCAA event IDs and attendance IDs")
    insights=(COLLEGE/"insights.html").read_text(encoding="utf8")
    check("PNC Arena" in insights and
          "results.filter(g=>g.arenaIdentity)" in insights,
          "Arena insights avoid invented venues and aggregate confirmed naming-rights aliases")
    games=list(csv.DictReader((COLLEGE/"data/games.csv").open(encoding="utf8",newline="")))
    players=json.loads((COLLEGE/"data/player_boxscores_espn.json").read_text(encoding="utf8"))
    teams=json.loads((COLLEGE/"data/team_names.json").read_text(encoding="utf8"))
    check(len(games)==94 and len(players)==1825 and len(teams)==75,
          "94 games / 1,825 performances / 75 schools remain intact")
    check(all(g["arena"] and g["site_type"] in ("home","neutral") for g in games),
          "All 94 game locations have a sourced venue and explicit site classification")
    check(len({g["arena"] for g in games})==19,"19 historically named venue labels in original games")
    check(sum(g["site_type"]=="neutral" for g in games)==6,"Six tournament / neutral site games marked explicitly")
    check(len({("Lenovo Center" if g["arena"]=="PNC Arena" else g["arena"]) for g in games})==18,
          "18 distinct physical arenas after sourced naming-rights alias normalization")
    venue_rows=list(csv.DictReader((COLLEGE/"data/verified_venues.csv").open(encoding="utf8",newline="")))
    venue_by_id={r["attendance_id"]:r for r in venue_rows}
    check(len(venue_rows)==len(venue_by_id)==len(games)==94,
          "All 94 source-certified venue rows uniquely match attendance IDs")
    check(all((v:=venue_by_id.get(g["id"])) is not None and
              v["espn_event_id"]==g["espn_event_id"] and v["arena"]==g["arena"] and
              v["site_type"]==g["site_type"] and v["source_url"].startswith("https://") and
              bool(v["source_name"])
              for g in games),
          "Venue source URLs, attendance IDs, provider event IDs and site classifications reconcile")
    check(next(g for g in games if g["id"]=="60")["arena"]=="The Pavilion at JSerra","CSUN Tennessee State neutral-site venue sourced")
    check(next(g for g in games if g["id"]=="18")["arena"]=="Jenny Craig Pavilion","2018 Colorado at USD venue sourced")
    check(next(g for g in games if g["id"]=="54")["arena"]=="Jenny Craig Pavilion","2022 Gonzaga at USD venue sourced")
    check(next(g for g in games if g["id"]=="79")["arena"]=="PNC Arena","2024 historical PNC Arena label retained")
    check(next(g for g in games if g["id"]=="85")["arena"]=="Lenovo Center","2025 Lenovo Center label retained")
    check(next(g for g in games if g["id"]=="76")["site_type"]=="neutral" and
          next(g for g in games if g["id"]=="76")["arena"]=="The Pavilion at JSerra",
          "2023 California SDSU SoCal Showcase correctly identified as off-campus neutral court")
    check(next(g for g in games if g["id"]=="25")["arena"]=="Viejas Arena","2019 Nevada at SDSU in Viejas Arena")
    check(next(g for g in games if g["id"]=="31")["arena"]=="Bren Events Center","2019 Eastern Michigan UCI venue")
    check(next(g for g in games if g["id"]=="58")["arena"]=="LionTree Arena","2022 UCSD hosting Cal venue")
    check(next(g for g in games if g["id"]=="64")["arena"]=="Pauley Pavilion","UCLA Denver venue")
    check(next(g for g in games if g["id"]=="83")["arena"]=="Jenny Craig Pavilion","2025 USD Santa Clara venue")
    print("Static seven-page parity checks completed.")
if __name__=="__main__":main()
