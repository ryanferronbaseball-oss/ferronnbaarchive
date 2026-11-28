"""Screen every witnessed player against ASA senior professional US league data.
No name match is automatically promoted to the published alumni registry.
"""
import json, re, unicodedata
from pathlib import Path
from collections import defaultdict
import requests
ROOT=Path(__file__).resolve().parents[1]/'college-soccer'
BASE='https://app.americansocceranalysis.com/api/v1'
LEAGUES={'mls':'MLS','uslc':'USL Championship','usl1':'USL League One'}
def read(p):return json.loads((ROOT/p).read_text())
def save(p,d):
    p=ROOT/p;p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(d,indent=2,ensure_ascii=False)+'\n')
def norm(s):return re.sub('[^a-z0-9]','',unicodedata.normalize('NFKD',str(s)).encode('ascii','ignore').decode().lower())
def api(path,params=None):
    r=requests.get(BASE+path,params=params,timeout=(10,90));r.raise_for_status();d=r.json()
    if not isinstance(d,list):raise ValueError('Unexpected API shape: '+path)
    return d
def main():
    inv=read('data/portrait_inventory.json');reg=read('data/pro_crosswalk.json')['players'];aliases=read('data/pro_audit_aliases.json')
    report={'inventory_total':len(inv),'confirmed_players':len(reg),'screened_players':0,'fully_audited_players':0,'source':'American Soccer Analysis (CC BY-SA 4.0), '+BASE+'/__docs__/','leagues':{},'players':{pid:{'name':p['name'],'schools':list(p['schools']),'status':'qualifying_appearance_confirmed_career_incomplete' if pid in reg else 'pending_review','domestic_candidates':[]} for pid,p in inv.items()}}
    for code,league in LEAGUES.items():
        try:
            roster=api('/'+code+'/players');lookup=defaultdict(list)
            for p in roster:
                for name in [p.get('player_name'),p.get('name'),str(p.get('first_name',''))+' '+str(p.get('last_name',''))]:
                    if name and norm(name):lookup[norm(name)].append(p)
            matched={}
            for pid,p in inv.items():
                found={str(row['player_id']):row for name in [p['name'],*aliases.get(pid,[])] for row in lookup.get(norm(name),[]) if row.get('player_id')}
                matched[pid]=found
            ids=sorted({aid for v in matched.values() for aid in v});stats=defaultdict(list);errors=[]
            for i in range(0,len(ids),15):
                block=ids[i:i+15]
                try:
                    rows=api('/'+code+'/players/xgoals',{'player_id':','.join(block),'minimum_minutes':1,'split_by_teams':'true','split_by_seasons':'true'})
                    for row in rows:
                        if float(row.get('minutes_played') or row.get('minutes') or 0)>0:stats[str(row.get('player_id'))].append(row)
                except Exception as e:errors.append(str(e))
            for pid,found in matched.items():
                for aid,p in found.items():
                    report['players'][pid]['domestic_candidates'].append({'league':league,'player_id':aid,'player_name':p.get('player_name',p.get('name')),'birth_date':p.get('birth_date',p.get('birthdate')),'positive_minute_rows':[{k:v for k,v in r.items() if k in ['player_id','team_id','season_name','minutes_played','minutes','count_games','games_played']} for r in stats[aid]],'source_url':BASE+'/'+code+'/players/xgoals?player_id='+aid,'status':'identity_and_appearance_review_required'})
            report['leagues'][code]={'player_records':len(roster),'matched_archive_players':sum(bool(v) for v in matched.values()),'stat_errors':errors,'status':'partial' if errors else 'screened'}
        except Exception as e:report['leagues'][code]={'status':'failed','error':str(e)}
    if all(x.get('status')=='screened' for x in report['leagues'].values()):report['screened_players']=len(inv)
    report['notes']='ASA domestic coverage may omit historical seasons and zero-minute records. A match is a candidate, not proof of identity; no match is not proof of no career. International, historical and cup-only cases require independent review. Registry unchanged by this workflow.'
    save('reports/pro_career_audit.json',report)
    print(json.dumps({k:v for k,v in report.items() if k!='players'},indent=2))
if __name__=='__main__':main()
