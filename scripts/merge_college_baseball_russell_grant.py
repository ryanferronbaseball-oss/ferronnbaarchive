"""Owner-approved Russell Grant / Russell Grant II identity merge."""
import json,re,hashlib
from pathlib import Path
D=Path('college-baseball/data')
def load(n):return json.loads((D/n).read_text())
def save(n,d):(D/n).write_text(json.dumps(d,indent=2,ensure_ascii=False)+'\n')
paths=[D/'player_stats.json',D/'games.json']
before=[hashlib.sha256(p.read_bytes()).hexdigest() for p in paths]
rows=load('player_stats.json');cross=load('player_identity_crosswalk.json')
def norm(s):return re.sub('[^a-z0-9]','',str(s).lower())
matches=[r for r in rows if r.get('team')=='Santa Clara' and (norm(r.get('player')) in {'russellgrant','russellgrantii','grantii russell'.replace(' ',''),'grantrussell'} or norm(r.get('player_id')).endswith(('santaclararussellgrant','santaclararussellgrantii')))]
ids=sorted({r['player_id'] for r in matches})
assert len(ids)==2,('Expected exactly two Santa Clara source IDs',ids)
canonical=next(i for i in ids if norm(i).endswith('russellgrantii'))
assert len({r['game_id'] for r in matches})==len(matches),'Same-game collision: manual review needed'
for m in cross['merges']:
    if set(m['source_player_ids'])&set(ids):raise ValueError('Existing merge overlaps; review manually')
for m in cross.get('owner_rejected_merge_candidates',[]):
    assert not set(m['source_player_ids'])&set(ids),'Previously protected identity'
for r in rows:
    if r['player_id'] in ids:assert r['team']=='Santa Clara'
evidence='https://santaclarabroncos.com/sports/baseball/roster/russell-grant-ii/1855'
cross['merges'].append({'name':'Russell Grant II','display_name':'Russell Grant II','canonical_id':canonical,'source_player_ids':ids,'schools':['Santa Clara'],'pairs':[{'team':'Santa Clara','source_player_id':i} for i in ids],'source_rows':len(matches),'note':'Owner-approved Russell Grant / Russell Grant II name variant; official Santa Clara 2021 roster uses Russell Grant II.','evidence_urls':[evidence]})
cross['activated_person_merges']=len(cross['merges'])
cross['requested_person_merges']=len(cross['merges'])+cross.get('pending_person_merges',0)
assert before==[hashlib.sha256(p.read_bytes()).hexdigest() for p in paths]
audit={'name':'Russell Grant II','canonical_id':canonical,'merged_ids':ids,'school':'Santa Clara','source_rows':len(matches),'games':sorted({r['game_id'] for r in matches}),'source_rows_modified':0,'evidence_url':evidence}
save('player_identity_crosswalk.json',cross)
save('identity_russell_grant_merge.json',audit)
print(json.dumps(audit,indent=2))
