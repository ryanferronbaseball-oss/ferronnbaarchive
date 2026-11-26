"""Roster-backed identity audit; preserve raw scorebooks and existing profile links."""
import json,re,subprocess,hashlib,sys
from collections import defaultdict
from pathlib import Path
from urllib.parse import urljoin,urlsplit
from audit_lsu_baseball_portraits import roster,norm,host
D=Path('college-baseball/data')
def load(n):return json.loads((D/n).read_text())
def save(n,d):(D/n).write_text(json.dumps(d,indent=2,ensure_ascii=False)+'\n')
def export(school=None):
    return json.loads(subprocess.check_output(['node','scripts/export_baseball_identity_targets.cjs',*([school] if school else [])],text=True))
before={n:hashlib.sha256((D/n).read_bytes()).hexdigest() for n in ('player_stats.json','games.json')}
school=sys.argv[1] if len(sys.argv)>1 else 'LSU'
players=export(school);assert players
hosts=load('portrait_school_hosts.json');h=hosts[school]
report={'school':school,'profiles_reviewed':len(players),'roster_pages_verified':[],'notes':[],'abbreviated_names':[],'duplicate_candidates':[],'applied':[],'unresolved':[]}
years=sorted({y for p in players for y in p['schools'].get(school,[])})
rosters={}
for y in years:
    page=roster(y,h,report['notes'])
    if not page:continue
    soup,u=page;entries={}
    for a in soup.find_all('a',href=True):
        v=urljoin(u,a['href']);path=urlsplit(v).path
        if host(v)!=h or not re.search(r'/sports/bsb/roster/season/\d{4}/player/[^/]+/?$',path):continue
        name=' '.join(a.get_text(' ',strip=True).split())
        if len(name.split())<2 or len(name)>65 or not re.fullmatch(r"[\w .’'\-]+",name):continue
        slug=path.rstrip('/').split('/')[-1]
        if norm(name)!=norm(slug):continue
        entries[norm(name)]={'name':name,'source':v}
    rosters[y]=entries
    report['roster_pages_verified'].append({'year':y,'names':len(entries)})
cross=load('player_identity_crosswalk.json')
corr=load('player_name_corrections.json')
occupied={i for m in cross['merges'] for i in m['source_player_ids']}
occupied|={m['canonical_id'] for m in cross['merges']}
protected={i for m in cross.get('owner_rejected_merge_candidates',[]) for i in m['source_player_ids']}
aliases={m['player_id'] for m in cross.get('display_aliases',[])}
raw=load('player_stats.json')
rawby=defaultdict(list)
for r in raw:rawby[r['player_id']].append(r)
groups={(g['game_id'],g['team']):g for g in [corr,*corr['games']]}
existing_fixes={(g['game_id'],g['team'],f['source_player_id']) for g in [corr,*corr['games']] for f in g['corrections']}
byname=defaultdict(list)
for p in players:byname[norm(p['name'])].append(p)
for p in players:
    name=p['name'];pid=p['id'];parts=name.split()
    if not parts:continue
    # Genuine initials (with periods) and surname-only entries; do not expand ordinary JT/AJ names.
    abbr=len(parts)==1 or bool(re.fullmatch(r'[A-Za-z]\.?',parts[0])) or bool(re.fullmatch(r'(?:[A-Za-z]\.){1,3}',parts[0]))
    if not abbr:continue
    candidates={};per_year={}
    for y in p['schools'].get(school,[]):
        hits=[]
        for n,entry in rosters.get(y,{}).items():
            words=entry['name'].split()
            match=(len(parts)==1 and norm(' '.join(words[1:]))==norm(name)) or (len(parts)>1 and norm(' '.join(words[1:]))==norm(' '.join(parts[1:])) and norm(words[0]).startswith(norm(parts[0])))
            if match:hits.append(n);candidates[n]=entry
        per_year[y]=hits
    item={'id':pid,'name':name,'witnessed_years':p['schools'].get(school,[]),'candidates':list(candidates.values()),'matches_by_year':per_year}
    report['abbreviated_names'].append(item)
    # Only auto-correct when every witnessed year supports the exact same unique full name,
    # no existing profile with that name, no existing identity mapping, and exact raw rows.
    if len(candidates)!=1 or not per_year or any(len(v)!=1 for v in per_year.values()):
        report['unresolved'].append({**item,'reason':'No unique same-season roster match'});continue
    n,entry=next(iter(candidates.items()))
    others=[q['id'] for q in byname[n] if q['id']!=pid]
    if others:
        report['duplicate_candidates'].append({**item,'existing_ids':others});continue
    rs=rawby[pid]
    if pid in occupied|protected|aliases or not rs or any(r['team']!=school or (r['game_id'],r['team'],pid) in existing_fixes for r in rs):
        report['unresolved'].append({**item,'reason':'Existing mapping or nontrivial raw source rows; manual review'});continue
    for r in rs:
        k=(r['game_id'],r['team'])
        if k not in groups:
            g={'game_id':k[0],'team':k[1],'description':'Verified full roster name','verified_on':'2026-11-25','evidence_urls':[entry['source']],'corrections':[]}
            corr['games'].append(g);groups[k]=g
        g=groups[k]
        if entry['source'] not in g.setdefault('evidence_urls',[]):g['evidence_urls'].append(entry['source'])
        g['corrections'].append({'source_player_id':pid,'source_player_name':r['player'],'player':entry['name'],'canonical_player_id':pid})
    report['applied'].append({'id':pid,'old_name':name,'name':entry['name'],'source':entry['source'],'rows':len(rs)})
# Report exact normalized and reversed-name candidates without merging automatically.
for p in players:
    for q in players:
        if p['id']>=q['id']:continue
        pn,qn=p['name'].split(),q['name'].split()
        if norm(p['name'])==norm(q['name']) or (len(pn)==len(qn)==2 and norm(' '.join(pn[::-1]))==norm(q['name'])):
            report['duplicate_candidates'].append({'ids':[p['id'],q['id']],'names':[p['name'],q['name']],'same_game_overlap':sorted(set(p['games'])&set(q['games']))})
if report['applied']:
    save('player_name_corrections.json',corr)
    after=export(school)
    assert len(after)==len(players)
    index={p['id']:p for p in after}
    for fix in report['applied']:assert index[fix['id']]['name']==fix['name'],fix
assert before=={n:hashlib.sha256((D/n).read_bytes()).hexdigest() for n in before}
save('lsu_identity_portrait_review.json',report)
print(json.dumps({k:len(v) if isinstance(v,list) else v for k,v in report.items()},indent=2))
