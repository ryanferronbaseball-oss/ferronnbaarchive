"""Merge two confirmed CSUN school-spelling duplicates without changing raw rows."""
import json,hashlib,subprocess
from pathlib import Path
D=Path('college-baseball/data')
def load(n):return json.loads((D/n).read_text())
def save(n,d):(D/n).write_text(json.dumps(d,indent=2,ensure_ascii=False)+'\n')
def export():return json.loads(subprocess.check_output(['node','scripts/export_baseball_identity_targets.cjs'],text=True))
before={n:hashlib.sha256((D/n).read_bytes()).hexdigest() for n in ('player_stats.json','games.json')}
raw=load('player_stats.json');cross=load('player_identity_crosswalk.json');reg=load('player_portraits.json')
pre=export();idx={p['id']:p for p in pre}
report={'merged':[]}
for slug,name in [('mason-le','Mason Le'),('kamau-neighbors','Kamau Neighbors')]:
    canonical='cb-cal-state-northridge-'+slug;alias='cb-cal-state-northrdige-'+slug
    assert {canonical,alias}<=set(idx)
    assert not any(alias in m['source_player_ids'] for m in cross['merges']+cross.get('owner_rejected_merge_candidates',[]))
    assert not any(a['player_id'] in (canonical,alias) for a in cross.get('display_aliases',[]))
    existing=[m for m in cross['merges'] if m['canonical_id']==canonical]
    assert len(existing)<=1
    ids=set(existing[0]['source_player_ids'] if existing else [canonical])|{alias}
    effective=idx[canonical]['rows']+idx[alias]['rows']
    matches=[r for r in raw if r['player_id'] in ids]
    assert {r['player_id'] for r in matches}==ids
    assert all(r['team'] in ('Cal State Northridge','Cal State Northrdige','Louisville') for r in matches)
    assert len({r['game_id'] for r in effective})==len(effective),(name,'Same-game overlap')
    assert alias not in reg,'Alias portrait requires manual reconciliation'
    m=existing[0] if existing else {'canonical_id':canonical}
    m.update(name=name,display_name=name,source_player_ids=sorted(ids),schools=sorted({r['team'] for r in effective}),pairs=[{'team':t,'source_player_id':i} for t,i in sorted({(r['team'],r['player_id']) for r in matches})],source_rows=len(matches))
    m['note']='CSUN school spelling variants refer to the same player; preserve existing Louisville transfer linkage.'
    m['evidence_urls']=['https://gomatadors.com/sports/baseball/roster/2023','https://gomatadors.com/sports/baseball/roster/2022','https://gomatadors.com/sports/baseball/roster/2021']
    if not existing:cross['merges'].append(m)
    report['merged'].append({'name':name,'canonical_id':canonical,'alias':alias,'rows':len(effective),'games':sorted({r['game_id'] for r in effective})})
cross['activated_person_merges']=len(cross['merges'])
cross['requested_person_merges']=len(cross['merges'])+cross.get('pending_person_merges',0)
save('player_identity_crosswalk.json',cross)
after=export();newidx={p['id']:p for p in after}
assert len(after)==len(pre)-2
for m in report['merged']:
    p=newidx[m['canonical_id']]
    assert m['alias'] not in newidx and p['name']==m['name'] and len(p['rows'])==m['rows'] and sorted(p['games'])==m['games']
assert before=={n:hashlib.sha256((D/n).read_bytes()).hexdigest() for n in before}
csun=[p for p in after if 'Cal State Northridge' in p['schools']]
report.update(profiles=len(csun),registered_portraits=sum(p['id'] in reg for p in csun),missing=[{'id':p['id'],'name':p['name']} for p in csun if p['id'] not in reg],raw_source_rows_modified=0)
save('csun_identity_cleanup.json',report)
print(json.dumps(report,indent=2))
