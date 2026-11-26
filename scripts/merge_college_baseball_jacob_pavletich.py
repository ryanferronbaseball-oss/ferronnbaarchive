"""Owner-approved Jacob / Jake / J. Pavletich consolidation."""
import json,hashlib
from pathlib import Path
D=Path('college-baseball/data')
def load(n):return json.loads((D/n).read_text())
def save(n,d):(D/n).write_text(json.dumps(d,indent=2,ensure_ascii=False)+'\n')
paths=[D/'player_stats.json',D/'games.json']
before=[hashlib.sha256(p.read_bytes()).hexdigest() for p in paths]
rows=load('player_stats.json');cross=load('player_identity_crosswalk.json')
jacob='cb-cal-state-fullerton-jacob-pavletich'
jake='cb-cal-state-fullerton-jake-pavletich'
short='cb-cal-state-fullerton-j-pavletich'
ids={jacob,jake,short}
existing=[m for m in cross['merges'] if ids.intersection(m['source_player_ids'])]
assert len(existing)==1 and set(existing[0]['source_player_ids'])=={jake,short},existing
assert all(not ids.intersection(m['source_player_ids']) for m in cross.get('owner_rejected_merge_candidates',[]))
matches=[r for r in rows if r['player_id'] in ids]
assert {r['team'] for r in matches}=={'Cal State Fullerton'}
assert {r['player_id'] for r in matches}==ids
assert len({r['game_id'] for r in matches})==len(matches),'Same-game collision: review before merging'
m=existing[0]
m.update(name='Jacob Pavletich',display_name='Jacob Pavletich',canonical_id=jacob,source_player_ids=sorted(ids),pairs=[{'team':'Cal State Fullerton','source_player_id':i} for i in sorted(ids)],source_rows=len(matches),note='Owner-approved Jacob / Jake / J. Pavletich identity; preserve original gamebook rows.',evidence_urls=['https://fullertontitans.com/sports/baseball/roster/jacob-pavletich/1838'])
reg=load('player_portraits.json')
old=reg.pop(jake,None)
if old and (jacob not in reg or old.get('owner_preferred') or ('width=300' in old.get('url','') and not reg[jacob].get('owner_preferred'))):
    reg[jacob]=old
assert jacob in reg
assert before==[hashlib.sha256(p.read_bytes()).hexdigest() for p in paths]
save('player_identity_crosswalk.json',cross)
save('player_portraits.json',reg)
save('identity_jacob_pavletich_merge.json',{'name':'Jacob Pavletich','canonical_id':jacob,'merged_ids':sorted(ids),'games':sorted({r['game_id'] for r in matches}),'source_rows':len(matches),'source_rows_modified':0,'portrait':reg[jacob]})
print('Merged',len(matches),'game rows under Jacob Pavletich')
