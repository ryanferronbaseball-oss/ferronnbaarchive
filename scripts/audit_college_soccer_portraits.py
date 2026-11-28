"""Recover official college soccer portraits, preserving existing records."""
import concurrent.futures as cf
from collections import defaultdict
import json, re
from recover_ucla_soccer_portraits import recover as recover_ucla
from bs4 import BeautifulSoup
from audit_player_portraits import load, save
from audit_ncaaw_school_portraits import get, host, named_images, bio_links, bio_images, valid_bio, verify

def fetch_page(url):
    r=get(url);r.raise_for_status()
    if host(r.url)!=host(url):raise ValueError('Off-school redirect')
    return BeautifulSoup(r.text,'html.parser'),r.url

def main():
    targets=load('college-soccer/data/school_portrait_targets.json',{})
    reg=load('college-soccer/data/player_portraits.json',{})
    inventory=load('college-soccer/data/portrait_inventory.json',{})
    for pid,entry in list(reg.items()):
        if re.search(r'person[-_]?default|dummy-data|placeholder|silhouette|no[-_]?image',entry.get('url',''),re.I):del reg[pid]
    pages={};errors={}
    pdf_added=[]
    try:pdf_added=recover_ucla(reg,targets)
    except Exception as ex:errors['UCLA media roster']=str(ex)
    for url in sorted({u for t in targets.values() for u in t['rosters']}):
        try:pages[url]=fetch_page(url)
        except Exception as e:errors[url]=str(e)
    def find(t):
        school=t['host'];names=t['names'];tested=set();links_seen=set()
        def attempt(urls,source):
            for u in urls:
                if u in tested or re.search(r'person[-_]?default|dummy-data|placeholder|silhouette|no[-_]?image',u,re.I):continue
                tested.add(u)
                got=verify(u,school)
                if got:return got[0],source,got[1]
        for roster in t['rosters']:
            if roster not in pages:continue
            soup,page=pages[roster]
            got=attempt(named_images(soup,page,names,school),page)
            if got:return got,None
            for bio in bio_links(soup,page,names,school):
                if bio in links_seen:continue
                links_seen.add(bio)
                try:
                    bs,bp=fetch_page(bio)
                    if not valid_bio(bs,names):continue
                    got=attempt(bio_images(bs,bp,names,school),bp)
                    if got:return got,None
                except Exception:continue
        return None,f'No verified named portrait; {len(links_seen)} bios, {len(tested)} image candidates'
    report={'targeted':len(targets),'inventory_total':len(inventory),'added':pdf_added,'preserved':[],'missing':[],'roster_errors':errors}
    found={}
    with cf.ThreadPoolExecutor(max_workers=6) as pool:
        jobs={}
        for pid,t in targets.items():
            if pid in reg:report['preserved'].append(pid)
            else:jobs[pool.submit(find,t)]=pid
        for f in cf.as_completed(jobs):
            pid=jobs[f]
            try:
                got,reason=f.result()
                if got:found[pid]=got
                else:report['missing'].append({'id':pid,'name':targets[pid]['names'][0],'reason':reason})
            except Exception as e:report['missing'].append({'id':pid,'name':targets[pid]['names'][0],'reason':str(e)})
    hashes=defaultdict(list)
    for pid,(_,_,h) in found.items():hashes[h].append(pid)
    used_urls={v.get('url') for v in reg.values() if isinstance(v,dict)}
    for pid,(url,source,h) in found.items():
        if len(hashes[h])>1 or url in used_urls:
            report['missing'].append({'id':pid,'name':targets[pid]['names'][0],'reason':'Duplicate portrait'});continue
        reg[pid]={'url':url,'source':source,'provider':'official','school':targets[pid]['school'],'sha256':h}
        used_urls.add(url)
        report['added'].append({'id':pid,'name':targets[pid]['names'][0],'url':url,'source':source})
    report['verified_total']=sum(pid in reg for pid in targets)
    report['archive_verified_total']=sum(pid in reg for pid in inventory)
    save('college-soccer/data/player_portraits.json',reg)
    save('college-soccer/reports/school_portrait_audit.json',report)
    print(json.dumps(report,indent=2))
if __name__=='__main__':main()
