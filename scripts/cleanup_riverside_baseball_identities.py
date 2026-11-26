"""Owner-approved six UCR merges and two canonical display-name corrections."""
import json,hashlib,subprocess
from pathlib import Path
D=Path('college-baseball/data')
def load(n):return json.loads((D/n).read_text())
def save(n,d):(D/n).write_text(json.dumps(d,indent=2,ensure_ascii=False)+'\n')
def export():return json.loads(subprocess.check_output(['node','scripts/export_baseball_identity_targets.cjs'],text=True))
school='UC Riverside';prefix='cb-uc-riverside-'
specs=[
 ('j-shanks','jacob-shanks','Jacob Shanks','jacob-shanks/6962'),
 ('d-orick','dylan-orick','Dylan Orick','dylan-orick/6643'),
 ('c-pofek','cole-pofek','Cole Pofek','cole-pofek/6646'),
 ('n-webb','nathan-webb','Nathan Webb','nathan-webb/6650'),
 ('y-taylor','yeager-taylor','Yeager Taylor','yeager-taylor/5753'),
 ('t-bohall','travis-bohall','Travis Bohall','travis-bohall/6179')]
before={n:hashlib.sha256((D/n).read_bytes()).hexdigest() for n in ('player_stats.json','games.json')}
raw=load('player_stats.json');cross=load('player_identity_crosswalk.json');reg=load('player_portraits.json')
pre=export();idx={p['id']:p for p in pre}
occupied={i for m in cross['merges']+cross.get('owner_rejected_merge_candidates',[]) for i in m['source_player_ids']}
occupied|={m['canonical_id'] for m in cross['merges']}
aliases={a['player_id'] for a in cross.get('display_aliases',[])}
report={'school':school,'merged':[],'display_corrected':[]}
for old,new,name,bio in specs:
    alias=prefix+old;canonical=prefix+new;ids={alias,canonical}
    assert ids<=set(idx),(name,'Missing profiles')
    assert not ids.intersection(occupied|aliases),(name,'Existing or protected mapping')
    effective=[r for i in ids for r in idx[i]['rows']]
    matches=[r for r in raw if r['player_id'] in ids]
    assert {r['player_id'] for r in matches}==ids,(name,'Missing source IDs')
    assert all(r['team'].casefold()==school.casefold() for r in matches+effective),(name,'Other school rows')
    assert len({r['game_id'] for r in effective})==len(effective),(name,'Same-game overlap')
    assert canonical in reg and alias not in reg,(name,'Portrait conflict')
    source='https://gohighlanders.com/sports/baseball/roster/'+bio
    cross['merges'].append({'name':name,'display_name':name,'canonical_id':canonical,'source_player_ids':sorted(ids),'schools':[school],'pairs':[{'team':t,'source_player_id':i} for t,i in sorted({(r['team'],r['player_id']) for r in matches})],'source_rows':len(matches),'note':'Owner-approved abbreviated UCR name; official same-season roster match.','evidence_urls':[source]})
    occupied.update(ids)
    report['merged'].append({'name':name,'canonical_id':canonical,'alias':alias,'games':sorted({r['game_id'] for r in effective}),'rows':len(effective),'source':source})
for slug,name,bio in [('taylor-juline','Taylor Juline','taylor-juline/6636'),('andre-granillo','Andre Granillo','andre-granillo/6184')]:
    pid=prefix+slug
    m=[m for m in cross['merges'] if m['canonical_id']==pid]
    assert len(m)==1 and pid in idx and pid not in aliases
    m=m[0];m['display_name']=name
    evidence='https://gohighlanders.com/sports/baseball/roster/'+bio
    if evidence not in m.setdefault('evidence_urls',[]):m['evidence_urls'].append(evidence)
    report['display_corrected'].append({'id':pid,'old_name':idx[pid]['name'],'name':name,'source':evidence,'rows':len(idx[pid]['rows'])})
cross['activated_person_merges']=len(cross['merges'])
cross['requested_person_merges']=len(cross['merges'])+cross.get('pending_person_merges',0)
save('player_identity_crosswalk.json',cross)
after=export();newidx={p['id']:p for p in after}
assert len(after)==len(pre)-len(specs),(len(pre),len(after))
for m in report['merged']:
    p=newidx[m['canonical_id']]
    assert m['alias'] not in newidx and p['name']==m['name']
    assert len(p['rows'])==m['rows'] and sorted(p['games'])==m['games']
    assert all(r['player']==m['name'] for r in p['rows'])
for m in report['display_corrected']:
    p=newidx[m['id']]
    assert p['name']==m['name'] and len(p['rows'])==m['rows']
    assert all(r['player']==m['name'] for r in p['rows'])
assert before=={n:hashlib.sha256((D/n).read_bytes()).hexdigest() for n in before}
ucr=[p for p in after if school in p['schools']]
report.update(profiles=len(ucr),registered_portraits=sum(p['id'] in reg for p in ucr),missing=[{'id':p['id'],'name':p['name']} for p in ucr if p['id'] not in reg],raw_source_rows_modified=0)
save('riverside_identity_cleanup.json',report)
print(json.dumps(report,indent=2))
