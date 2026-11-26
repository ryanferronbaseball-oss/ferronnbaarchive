"""Owner-approved Anthony Martinez / Tony Martinez identity merge."""
import json,re,hashlib,subprocess
from pathlib import Path
D=Path('college-baseball/data')
def load(n):return json.loads((D/n).read_text())
def save(n,d):(D/n).write_text(json.dumps(d,indent=2,ensure_ascii=False)+'\n')
paths=[D/'player_stats.json',D/'games.json']
before=[hashlib.sha256(p.read_bytes()).hexdigest() for p in paths]
rows=load('player_stats.json');cross=load('player_identity_crosswalk.json')
def norm(s):return re.sub('[^a-z0-9]','',str(s).lower())
matches=[r for r in rows if r.get('team','').casefold()=='uc irvine' and r.get('player_id') in {'cb-uc-irvine-anthony-martinez','cb-uc-irvine-tony-martinez'}]
ids=sorted({r['player_id'] for r in matches})
assert len(ids)==2,('Expected exactly two Irvine source IDs',ids)
canonical='cb-uc-irvine-anthony-martinez'
assert len({r['game_id'] for r in matches})==len(matches),'Same-game collision: manual review needed'
for m in cross['merges']:
    if set(m['source_player_ids'])&set(ids):raise ValueError('Existing merge overlaps; review manually')
for m in cross.get('owner_rejected_merge_candidates',[]):
    assert not set(m['source_player_ids'])&set(ids),'Previously protected identity'
# Raw IDs can be reused by a faulty gamebook; check corrected effective rows
# before adding any global profile redirect. Never combine an unrelated school.
pre=json.loads(subprocess.check_output(['node','scripts/export_baseball_identity_targets.cjs'],text=True))
affected=[p for p in pre if p['id'] in ids]
assert {p['id'] for p in affected}==set(ids),affected
other=[{'id':p['id'],'row':r} for p in affected for r in p['rows'] if r['team'].casefold()!='uc irvine']
print('Raw non-Irvine rows:',json.dumps([{k:r.get(k) for k in ('game_id','team','player_id','player')} for r in rows if r['player_id'] in ids and r['team']!='UC Irvine']))
assert not other,('Effective rows outside Irvine require explicit identity review',other)
effective_rows=[r for p in affected for r in p['rows']]
assert len({r['game_id'] for r in effective_rows})==len(effective_rows),'Same-game collision after corrections'
evidence='https://ucirvinesports.com/sports/baseball/roster/anthony-martinez/7209'
cross['merges'].append({'name':'Anthony Martinez','display_name':'Anthony Martinez','canonical_id':canonical,'source_player_ids':ids,'schools':['UC Irvine'],'pairs':[{'team':team,'source_player_id':i} for team,i in sorted({(r['team'],r['player_id']) for r in matches})],'source_rows':len(matches),'note':'Owner-approved Anthony Martinez / Tony Martinez name variant; official UC Irvine roster uses Anthony Martinez.','evidence_urls':[evidence]})
cross['activated_person_merges']=len(cross['merges'])
cross['requested_person_merges']=len(cross['merges'])+cross.get('pending_person_merges',0)
assert before==[hashlib.sha256(p.read_bytes()).hexdigest() for p in paths]
audit={'name':'Anthony Martinez','canonical_id':canonical,'merged_ids':ids,'school':'UC Irvine','source_rows':len(matches),'games':sorted({r['game_id'] for r in matches}),'source_rows_modified':0,'evidence_url':evidence}
reg=load('player_portraits.json')
assert canonical in reg,'Missing Anthony Martinez portrait'
assert 'cb-uc-irvine-tony-martinez' not in reg,'Unexpected duplicate portrait'
save('player_identity_crosswalk.json',cross)
players=json.loads(subprocess.check_output(['node','scripts/export_baseball_identity_targets.cjs','UC Irvine'],text=True))
p=next(p for p in players if p['id']==canonical)
assert p['name']=='Anthony Martinez'
assert not any(p['id']=='cb-uc-irvine-tony-martinez' for p in players)
assert len(p['rows'])==len(p['games']),'Duplicate game rows after merge'
audit['canonical_game_count']=len(p['games'])
audit['portrait']=reg[canonical]
audit['irvine_profile_count']=len(players)
audit['irvine_portrait_count']=sum(p['id'] in reg for p in players)
save('identity_anthony_martinez_merge.json',audit)
print(json.dumps(audit,indent=2))
