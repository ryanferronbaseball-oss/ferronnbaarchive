#!/usr/bin/env python3
"""Diagnostics: identify official SIDEARM football boxscore table structure."""
import json
import pathlib
import urllib.request
from bs4 import BeautifulSoup
ROOT=pathlib.Path(__file__).resolve().parents[1]
games=json.loads((ROOT/"data/games.json").read_text())
for g in games:
 url=g["boxscore_url"]
 print("\nGAME",g["id"],url,flush=True)
 try:
  req=urllib.request.Request(url,headers={"User-Agent":"Mozilla/5.0 Courtside-Archive-Research/1.0"})
  data=urllib.request.urlopen(req,timeout=30).read().decode("utf-8","replace")
  soup=BeautifulSoup(data,"html.parser")
  tables=soup.find_all("table")
  print("HTML",len(data),"tables",len(tables),flush=True)
  for i,t in enumerate(tables):
   text=t.get_text(" ",strip=True)
   header=[x.get_text(" ",strip=True) for x in t.select("thead tr")]
   labels=[h.get_text(" ",strip=True) for h in t.select("th")][:15]
   if any(w in text.lower()[:120] for w in ("player","cmp","yards","rec","defense","tackle","field goal","attempts","int")):
    before=[]
    for p in t.find_all_previous(["h2","h3","h4","h5"],limit=3):before.append(p.get_text(" ",strip=True)[:80])
    print("TABLE",i,"heading",before,"headers",header[:2],"labels",labels[:12],"first",text[:160],flush=True)
 except Exception as exc:print("ERROR",repr(exc),flush=True)
