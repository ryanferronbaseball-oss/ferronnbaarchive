"""Follow-up audit of remaining historical MLB players using named official photos
and a conservative, rate-limited retry of ID-matched Baseball Reference pages."""
import json
import re
import time
from collections import defaultdict
from urllib.parse import urljoin,urlsplit
from bs4 import BeautifulSoup
from audit_player_portraits import load,save,get,probe,slug
from audit_mlb_historical_portraits import crosswalk,name_norm,reference_candidates

def allowed(u):
    h=urlsplit(u).hostname or ""
    return u.startswith("https://") and any(h==d or h.endswith("."+d) for d in ("mlb.com","mlbstatic.com","sidearmsports.com","sidearmdev.com","sidearmnextgen.com","gohofstra.com","riceowls.com","rolltide.com","cloudfront.net","amazonaws.com"))
def official_candidates(p,urls,notes):
    n=name_norm(p["name"])
    for page in urls:
        try:
            r=get(page);r.raise_for_status()
            soup=BeautifulSoup(r.text,"html.parser")
            if n not in name_norm(soup.get_text(" ",strip=True)):continue
            for tag in soup.find_all("img"):
                alt=name_norm(tag.get("alt",""))
                if alt not in (n,"photoof"+n,"headshotof"+n,n+"headshot","portraitof"+n,n+"portrait"):continue
                for k in ("data-src","src","data-lazy-src"):
                    if not tag.get(k):continue
                    u=urljoin(r.url,tag[k])
                    if allowed(u) and not re.search(r"placeholder|silhouette|default|logo|\.svg",u,re.I):
                        yield u,r.url
        except Exception as e:notes.append(f"{p['name']}: {e}")
def main():
    rp="reports/player_portrait_audit.json"; fp="mlb/data/player_portrait_fallbacks.json"
    report=load(rp);reg=load(fp,{})
    people={str(p["id"]):p for p in report["mlb"]["missing"] if str(p["id"]) not in reg}
    sources=load("mlb/data/portrait_coaching_sources.json",{})
    notes=[];added=[];hashes=set()
    def accept(i,u,source,provider):
        status,h=probe(u)
        if status!="image" or not h or h in hashes:return False
        hashes.add(h)
        reg[i]={"name":people[i]["name"],"url":u,"source":source,"provider":provider}
        added.append({"name":people[i]["name"],"url":u,"source":source,"provider":provider})
        return True
    # Try named photos on exact official team/school pages.
    for i,urls in sources.items():
        if i not in people:continue
        for u,source in official_candidates(people[i],urls,notes):
            if accept(i,u,source,"official"):break
    remaining={i:p for i,p in people.items() if i not in reg}
    ids=crosswalk(remaining,notes)
    # Avoid repeated requests if the source declines access or asks us to slow down.
    for i,p in remaining.items():
        bb,minor,_=ids.get(i,("","",""))
        if not bb or not re.fullmatch(r"[a-z0-9]+",bb):continue
        page=f"https://www.baseball-reference.com/players/{bb[0]}/{bb}.shtml"
        time.sleep(5)
        try:
            r=get(page)
            if r.status_code in (403,429):
                notes.append(f"Baseball Reference declined access ({r.status_code}); stopped source pass.")
                break
            r.raise_for_status()
            soup=BeautifulSoup(r.text,"html.parser")
            name=name_norm(p["name"])
            title=" ".join(x.get_text(" ",strip=True) for x in soup.find_all(["h1","title"]))
            if name not in name_norm(title):continue
            for tag in soup.find_all("img"):
                alt=name_norm(tag.get("alt",""))
                if alt not in (name,"photoof"+name,"imageof"+name,"headshotof"+name):continue
                done=False
                for v in (tag.get("src"),tag.get("data-src")):
                    if not v:continue
                    u=urljoin(r.url,v)
                    h=urlsplit(u).hostname or ""
                    if not u.startswith("https://") or not any(h==d or h.endswith("."+d) for d in ("baseball-reference.com","sports-reference.com","sr-logos.com")):continue
                    if re.search(r"generic|default|placeholder|silhouette|logo|\.svg",u,re.I):continue
                    if accept(i,u,r.url,"historical"):
                        done=True
                        break
                if done:break
        except Exception as e:notes.append(f"{p['name']}: {e}")
        # Stop once the agreed target is reached, avoiding needless traffic.
        if report["mlb"]["current_verified"]+len(reg)>=(9*report["mlb"]["total_older"]+9)//10:break
    save(fp,reg)
    report["mlb"]["fallbacks"]=len(reg)
    report["mlb"]["missing"]=[p for p in report["mlb"]["missing"] if str(p["id"]) not in reg]
    report["mlb_targeted_pass"]={"attempted_pool":len(people),"added":added,"notes":notes,"remaining_to_90":max(0,(9*report["mlb"]["total_older"]+9)//10-report["mlb"]["current_verified"]-len(reg))}
    save(rp,report)
    print(json.dumps(report["mlb_targeted_pass"],indent=2))
if __name__=="__main__":main()
