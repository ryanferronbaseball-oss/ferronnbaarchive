"""Inspect actual WMT roster and bio image metadata before changing the extractor."""
import json
from bs4 import BeautifulSoup
from audit_player_portraits import get,save
from urllib.parse import urljoin
urls=['https://goaztecs.com/sports/baseball/roster/season/2023','https://goaztecs.com/sports/baseball/roster/season/2023/player/cade-martinez','https://goaztecs.com/sports/baseball/roster/season/2023/player/tj-fondtain','https://goaztecs.com/sports/baseball/roster/season/2021']
report=[]
for u in urls:
    r=get(u);r.raise_for_status()
    soup=BeautifulSoup(r.text,'html.parser')
    images=[]
    for img in soup.find_all('img'):
        a={k:str(v)[:1000] for k,v in img.attrs.items() if k in ('src','srcset','data-src','data-srcset','alt','class','loading','data-lazy-src')}
        if a:images.append(a)
    anchors=[]
    for a in soup.select('a[href*="/player/"]')[:50]:
        anchors.append({'name':a.get_text(' ',strip=True),'href':a['href'],'parent':str(a.parent)[:2200]})
    metas=[dict(m.attrs) for m in soup.find_all('meta') if any(k in str(m.attrs).lower() for k in ('image','og:title'))]
    scripts=[]
    for sc in soup.find_all('script'):
        t=sc.string or ''
        if not t:continue
        hits=[]
        for term in ('cade-martinez','Cade Martinez','tj-fondtain','TJ Fondtain','headshot','headShot','portrait','playerImage'):
            at=t.lower().find(term.lower())
            if at>=0:hits.append({'term':term,'context':t[max(0,at-400):at+1000]})
        if hits:scripts.append({'attrs':dict(sc.attrs),'hits':hits})
    report.append({'url':r.url,'images':images[:100],'anchors':anchors,'meta':metas,'script_matches':scripts[:20]})
save('college-baseball/data/sdsu_portrait_diagnostics.json',report)
print('Saved image, roster-link and structured metadata diagnostics for',len(report),'official pages')
