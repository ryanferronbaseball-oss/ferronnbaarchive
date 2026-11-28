"""Source-evidence audit for witnessed men's college soccer players.

This script never promotes a name mention into a verified award. The official
player registry changes only after explicit review of award, season and identity.
"""
import argparse, concurrent.futures as cf, json, re, unicodedata
from pathlib import Path
from urllib.parse import urlsplit
import requests
from bs4 import BeautifulSoup
ROOT=Path(__file__).resolve().parents[1]/'college-soccer'
def load(path):
    return json.loads((ROOT/path).read_text())
def save(path,data):
    p=ROOT/path;p.parent.mkdir(parents=True,exist_ok=True)
    p.write_text(json.dumps(data,indent=2,ensure_ascii=False)+'\n')
def norm(s):
    return re.sub(r'[^a-z0-9]+',' ',unicodedata.normalize('NFKD',s).encode('ascii','ignore').decode().lower()).strip()
def fetch(url):
    if urlsplit(url).scheme!='https':raise ValueError('HTTPS required')
    r=requests.get(url,headers={'User-Agent':'Mozilla/5.0 Courtside Archive'},timeout=(7,20));r.raise_for_status()
    soup=BeautifulSoup(r.text,'html.parser')
    for t in soup(['script','style','nav','footer','header']):t.decompose()
    title=soup.title.get_text(' ',strip=True) if soup.title else ''
    chunks=[x.strip() for x in soup.get_text('\n',strip=True).splitlines() if x.strip()]
    return {'url':r.url,'title':title,'chunks':chunks}
def main():
    ap=argparse.ArgumentParser();ap.add_argument('--school',default='San Diego');args=ap.parse_args()
    cfg=load('data/awards_audit_sources.json');inv=load('data/portrait_inventory.json');reg=load('data/individual_honors.json').get('players',{});portraits=load('data/player_portraits.json')
    if args.school not in cfg['school_order']:raise ValueError('Unknown school')
    scope={pid:p for pid,p in inv.items() if args.school in p['schools']}
    claims={pid:reg.get(pid,{}).get('college',[]) for pid in scope}
    urls={x['url'] for x in cfg['sources_by_school'].get(args.school,[])}
    per_player={}
    for pid in scope:
        own={h['source_url'] for h in claims[pid] if h.get('source_url')}
        # Only use a portrait source if it is a genuine individual roster bio.
        bio=portraits.get(pid,{}).get('source','')
        if '/roster/' in bio and (re.search(r'/\d+(?:\?.*)?$',bio) and len(urlsplit(bio).path.split('/'))>=7 or '/player/' in bio):own.add(bio)
        per_player[pid]=own;urls.update(own)
    fetched={};errors={}
    with cf.ThreadPoolExecutor(max_workers=6) as pool:
        jobs={pool.submit(fetch,u):u for u in sorted(urls)}
        for job in cf.as_completed(jobs):
            u=jobs[job]
            try:fetched[u]=job.result()
            except Exception as e:errors[u]=str(e)
    general={x['url'] for x in cfg['sources_by_school'].get(args.school,[])}
    result={}
    for pid,p in scope.items():
        name=norm(p['name']);evidence=[]
        for u in sorted(general|per_player[pid]):
            if u not in fetched:continue
            doc=fetched[u];chunks=doc['chunks'];matches=[]
            for i,line in enumerate(chunks):
                if re.search(r'\b'+re.escape(name)+r'\b',norm(line)):
                    matches.append({'context':' | '.join(chunks[max(0,i-3):i+5])[:850]})
            # Verified individual bio may use name only in its heading; preserve honor-related lines for review.
            if u in per_player[pid] and '/roster/' in u:
                for i,line in enumerate(chunks):
                    if re.search(r'all.conference|all.wcc|all.american|player of the year|defender of the year|goalkeeper of the year|freshman of the year|hermann|national champion',line,re.I):
                        matches.append({'context':' | '.join(chunks[max(0,i-1):i+2])[:850]})
            if matches:evidence.append({'source_url':u,'resolved_url':doc['url'],'title':doc['title'],'matches':matches[:20]})
        result[pid]={'name':p['name'],'witnessed_schools':p['schools'],'existing_awards':claims[pid],'candidate_evidence':evidence,'status':'manual_review_required','failed_sources':sorted((general|per_player[pid])&errors.keys())}
    report={'school':args.school,'players_in_batch':len(scope),'players_with_existing_awards':sum(bool(x) for x in claims.values()),'existing_awards':sum(map(len,claims.values())),'sources_attempted':len(urls),'sources_retrieved':len(fetched),'source_errors':errors,'players':result,'completion_status':'evidence_collected_not_full_career_verified','notes':'Manual confirmation of award, year, school and identity required. No name match alone creates a tag. No evidence is not proof of no awards.'}
    slug=norm(args.school).replace(' ','-')
    save('reports/awards/'+slug+'.json',report)
    state_path=ROOT/'reports/awards_audit_progress.json'
    state=json.loads(state_path.read_text()) if state_path.exists() else {'school_order':cfg['school_order'],'schools':{}}
    state['inventory_total']=len(inv)
    state['tagged_players']=sum(bool(p.get('college')) for p in reg.values())
    state['uploaded_honors']=sum(len(p.get('college',[])) for p in reg.values())
    state['schools'][args.school]={'players':len(scope),'evidence_report':'awards/'+slug+'.json','status':report['completion_status'],'sources_retrieved':len(fetched),'source_errors':len(errors)}
    state['fully_audited_schools']=sum(x.get('status')=='complete' for x in state['schools'].values())
    save('reports/awards_audit_progress.json',state)
    print(json.dumps({k:v for k,v in report.items() if k!='players'},indent=2))
if __name__=='__main__':main()
