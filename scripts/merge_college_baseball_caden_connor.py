"""Owner-approved Caden Connor / Connor Caden identity merge."""
import json,re,hashlib
from pathlib import Path
D=Path('college-baseball/data')
def load(n):return json.loads((D/n).read_text())
def save(n,d):(D/n).write_text(json.dumps(d,indent=2,ensure_ascii=False)+'\n')
paths=[D/'player_stats.json',D/'games.json']
before=[hashlib.sha256(p.read_bytes()).hexdigest() for p in paths]
rows=load('player_stats.json');cross=load('player_identity_crosswalk.json')
def norm(s):return re.sub('[^a-z0-9]','',str(s).lower())
matches=[r for r in rows if r.get('team')=='Cal State Fullerton' and r.get('player_id') in {'cb-cal-state-fullerton-caden-connor','cb-cal-state-fullerton-connor-caden'}]
ids=sorted({r['player_id'] for r in matches})
assert len(ids)==2,('Expected exactly two Fullerton source IDs',ids)
canonical='cb-cal-state-fullerton-caden-connor'
assert len({r['game_id'] for r in matches})==len(matches),'Same-game collision: manual review needed'
for m in cross['merges']:
    if set(m['source_player_ids'])&set(ids):raise ValueError('Existing merge overlaps; review manually')
for m in cross.get('owner_rejected_merge_candidates',[]):
    assert not set(m['source_player_ids'])&set(ids),'Previously protected identity'
for r in rows:
    if r['player_id'] in ids:assert r['team']=='Cal State Fullerton'
evidence='https://fullertontitans.com/sports/baseball/roster/2023'
cross['merges'].append({'name':'Caden Connor','display_name':'Caden Connor','canonical_id':canonical,'source_player_ids':ids,'schools':['Cal State Fullerton'],'pairs':[{'team':'Cal State Fullerton','source_player_id':i} for i in ids],'source_rows':len(matches),'note':'Owner-approved Caden Connor / Connor Caden name variant; official Cal State Fullerton roster uses Caden Connor.','evidence_urls':[evidence]})
cross['activated_person_merges']=len(cross['merges'])
cross['requested_person_merges']=len(cross['merges'])+cross.get('pending_person_merges',0)
assert before==[hashlib.sha256(p.read_bytes()).hexdigest() for p in paths]
audit={'name':'Caden Connor','canonical_id':canonical,'merged_ids':ids,'school':'Cal State Fullerton','source_rows':len(matches),'games':sorted({r['game_id'] for r in matches}),'source_rows_modified':0,'evidence_url':evidence}
save('player_identity_crosswalk.json',cross)
save('identity_caden_connor_merge.json',audit)
print(json.dumps(audit,indent=2))
