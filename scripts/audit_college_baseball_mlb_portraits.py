"""First college baseball portrait pass: verified MLB alumni and MLB crossover IDs only."""
from collections import defaultdict
import json
from audit_player_portraits import load,save,official,probe_many,probe

def main():
    fp='college-baseball/data/player_portraits.json'
    reg=load(fp,{})
    ids=defaultdict(set)
    for p in load('college-baseball/data/mlb_alumni_seed.json',{}).get('players',[]):
        if p.get('mlb_debut') and str(p.get('mlb_player_id','')).isdigit():
            ids[p['college_player_id']].add(str(p['mlb_player_id']))
    for p in load('college-baseball/data/mlb_crosswalk.json',[]):
        if p.get('verified') is True and str(p.get('mlb_player_id','')).isdigit():
            ids[p['college_player_id']].add(str(p['mlb_player_id']))
    fallbacks=load('mlb/data/player_portrait_fallbacks.json',{})
    choices={}
    conflicts=[]
    for cid,values in ids.items():
        if len(values)!=1:
            conflicts.append({'id':cid,'mlb_ids':sorted(values)});continue
        if cid in reg:continue
        mid=next(iter(values))
        f=fallbacks.get(mid,{})
        urls=[official(mid)]
        if isinstance(f.get('url'),str) and f['url'].startswith('https://'):urls.append(f['url'])
        urls.append(f'https://img.mlbstatic.com/mlb-photos/image/upload/w_213,q_85/v1/people/{mid}/headshot/milb/current')
        choices[cid]=(mid,list(dict.fromkeys(urls)))
    urls=list(dict.fromkeys(u for _,us in choices.values() for u in us))
    results=probe_many(urls)
    sentinels=set()
    for mid in ['1','999999999']:
        for u in [official(mid),f'https://img.mlbstatic.com/mlb-photos/image/upload/w_213,q_85/v1/people/{mid}/headshot/milb/current']:
            sentinels.add(probe(u)[1])
    hash_ids=defaultdict(set)
    for cid,(mid,us) in choices.items():
        for u in us:
            status,h=results[u]
            if status=='image' and h:hash_ids[h].add(mid)
    added=[];missing=[]
    for cid,(mid,us) in choices.items():
        for u in us:
            status,h=results[u]
            if status!='image' or not h or h in sentinels or len(hash_ids[h])!=1:continue
            f=fallbacks.get(mid,{})
            record={'mlb_player_id':mid,'url':u,'source':f.get('source') if u==f.get('url') else f'https://www.mlb.com/player/{mid}','provider':f.get('provider','mlb') if u==f.get('url') else 'mlb'}
            for k in ['author','license','license_url']:
                if u==f.get('url') and f.get(k):record[k]=f[k]
            reg[cid]=record;added.append(cid);break
        else:missing.append(cid)
    report={'targeted':len(ids),'added':added,'preserved':len(ids)-len(choices)-len(conflicts),'missing':missing,'conflicts':conflicts,'registered':len(reg)}
    save(fp,reg);save('college-baseball/data/player_portrait_audit.json',report)
    print(json.dumps(report,indent=2))
if __name__=='__main__':main()
