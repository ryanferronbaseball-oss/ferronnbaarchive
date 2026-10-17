#!/usr/bin/env python3
"""Locate official full May 22 Auburn–Texas A&M SEC box score PDF without guessing."""
from bs4 import BeautifulSoup
import requests

sess=requests.Session()
sess.headers["User-Agent"]="Mozilla/5.0"
sites=[
"https://auburntigers.com/sports/baseball/schedule/season/2026",
"https://auburntigers.com/news/2026/05/22/no-6-auburn-blanks-no-9-texas-aandm-7-0-to-advance-to-sec-semis",
"https://12thman.com/news/2026/05/23/baseball-falls-to-auburn-in-sec-tournament",
]
for url in sites:
    try:
        response=sess.get(url,timeout=25)
        print("SITE",url,response.status_code,len(response.content),response.url,flush=True)
        soup=BeautifulSoup(response.text,"html.parser")
        count=0
        for a in soup.find_all("a",href=True):
            label=a.get_text(" ",strip=True)
            href=a["href"]
            if not any(x in (label+" "+href).lower() for x in ("box score (pdf)","box (pdf)",".pdf","boxscore")):
                continue
            box_text=""
            ancestor=a
            for level in range(1,6):
                ancestor=ancestor.parent if ancestor else None
                if ancestor is None:break
                t=ancestor.get_text(" ",strip=True)
                if "Texas A&M" in t or "May 22" in t or "May 23" in t:
                    box_text=t[:185]
                    break
            count+=1
            if box_text or count>45:
                print("SOURCE-LINK",count,"label",label[:60],"href",href[:600],"context",box_text,flush=True)
        print("PDF_SOURCE_ANCHORS",count,flush=True)
    except Exception as e:
        print("SOURCE-ERROR",url,type(e).__name__,str(e)[:300],flush=True)
url="https://12thman.com/documents/d22cbc28-fb44-409a-bd89-8e6f04f059b5.pdf"
try:
    r=sess.get(url,timeout=25)
    print("TEXAS_AM_PDF",r.status_code,len(r.content),r.url,r.headers.get("content-type"),repr(r.content[:40]),flush=True)
except Exception as e:
    print("TEXAS_AM_PDF_ERROR",repr(e),flush=True)
