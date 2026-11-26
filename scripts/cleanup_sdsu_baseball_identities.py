"""Owner-approved SDSU identity and official roster name corrections."""
import hashlib,json,subprocess
from pathlib import Path
D=Path('college-baseball/data')
def load(n):return json.loads((D/n).read_text())
def save(n,d):(D/n).write_text(json.dumps(d,indent=2,ensure_ascii=False)+'\n')
def export():return json.loads(subprocess.check_output(['node','scripts/export_baseball_identity_targets.cjs'],text=True))
school='San Diego State'
prefix='cb-san-diego-state-'
before={n:hashlib.sha256((D/n).read_bytes()).hexdigest() for n in ('player_stats.json','games.json')}
raw=load('player_stats.json')
cross=load('player_identity_crosswalk.json');corr=load('player_name_corrections.json');reg=load('player_portraits.json')
pre=export();index={p['id']:p for p in pre}
ids={prefix+'justi-goossen-brown',prefix+'justin-goossen-brown'}
canonical=prefix+'justin-goossen-brown'
assert ids<=set(index)
assert all(not ids.intersection(m['source_player_ids']) for m in cross['merges']+cross.get('owner_rejected_merge_candidates',[]))
matches=[r for r in raw if r['player_id'] in ids]
assert {r['player_id'] for r in matches}==ids
assert all(r['team'].casefold()==school.casefold() for r in matches)
effective=[r for i in ids for r in index[i]['rows']]
assert all(r['team'].casefold()==school.casefold() for r in effective)
assert len({r['game_id'] for r in effective})==len(effective),'Same-game overlap: review required'
source='https://goaztecs.com/sports/baseball/roster/season/2019/player/justin-goossen-brown'
cross['merges'].append({'name':'Justin Goossen-Brown','display_name':'Justin Goossen-Brown','canonical_id':canonical,'source_player_ids':sorted(ids),'schools':[school],'pairs':[{'team':t,'source_player_id':i} for t,i in sorted({(r['team'],r['player_id']) for r in matches})],'source_rows':len(matches),'note':'Owner-approved truncated first name correction; official 2019 SDSU roster.','evidence_urls':[source]})
cross['activated_person_merges']=len(cross['merges'])
cross['requested_person_merges']=len(cross['merges'])+cross.get('pending_person_merges',0)
assert canonical in reg and prefix+'justi-goossen-brown' not in reg
fixes={
    'eldridge-armstrong':('Eldridge Armstrong III','https://goaztecs.com/sports/baseball/roster/player/eldridge-armstrong-iii'),
    'xavier-cardenas':('Xavier Cardenas III','https://goaztecs.com/sports/baseball/roster/season/2024/player/xavier-cardenas-iii'),
    'tj-fondtain':('TJ Fondtain','https://goaztecs.com/sports/baseball/roster/season/2023/player/tj-fondtain'),
    'tyson-de-wall':('Tyson De Wall','https://goaztecs.com/news/2023/02/22/aztecs-drop-home-opener-to-csun-7-5')
}
groups={(g['game_id'],g['team']):g for g in [corr,*corr['games']]}
existing={(g['game_id'],g['team'],f['source_player_id']) for g in [corr,*corr['games']] for f in g['corrections']}
report={'merge':{'canonical_id':canonical,'source_ids':sorted(ids),'games':sorted({r['game_id'] for r in effective})},'corrected':[]}
for slug,(name,url) in fixes.items():
    pid=prefix+slug
    assert pid in index
    assert all(pid not in m['source_player_ids'] for m in cross['merges'])
    assert all(a['player_id']!=pid for a in cross.get('display_aliases',[]))
    rows=[r for r in raw if r['player_id']==pid]
    assert rows and all(r['team'].casefold()==school.casefold() for r in rows)
    assert len(rows)==len(index[pid]['rows'])
    assert not any((r['game_id'],r['team'],pid) in existing for r in rows)
    for r in rows:
        k=(r['game_id'],r['team'])
        if k not in groups:
            g={'game_id':k[0],'team':k[1],'description':'Official SDSU roster spelling','verified_on':'2026-11-25','evidence_urls':[url],'corrections':[]}
            corr['games'].append(g);groups[k]=g
        g=groups[k]
        if url not in g.setdefault('evidence_urls',[]):g['evidence_urls'].append(url)
        g['corrections'].append({'source_player_id':pid,'source_player_name':r['player'],'player':name,'canonical_player_id':pid})
    report['corrected'].append({'id':pid,'old_name':index[pid]['name'],'name':name,'rows':len(rows),'source':url})
save('player_identity_crosswalk.json',cross);save('player_name_corrections.json',corr)
after=export();idx={p['id']:p for p in after}
assert len(after)==len(pre)-1 and prefix+'justi-goossen-brown' not in idx
assert idx[canonical]['name']=='Justin Goossen-Brown'
assert len(idx[canonical]['rows'])==len(effective)
for f in report['corrected']:
    p=idx[f['id']]
    assert p['name']==f['name'],(p['name'],f)
    assert all(r['player']==f['name'] for r in p['rows'])
assert before=={n:hashlib.sha256((D/n).read_bytes()).hexdigest() for n in before}
sdsu=[p for p in after if school in p['schools']]
report.update(profiles=len(sdsu),registered_portraits=sum(p['id'] in reg for p in sdsu),missing=[{'id':p['id'],'name':p['name']} for p in sdsu if p['id'] not in reg],raw_source_rows_modified=0)
save('sdsu_identity_cleanup.json',report)
print(json.dumps(report,indent=2))
