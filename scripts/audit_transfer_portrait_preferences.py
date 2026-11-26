"""Check existing transfer portraits against witnessed playing-time preferences."""
import json,subprocess
from pathlib import Path
d=Path('college-baseball/data')
players=json.loads(subprocess.check_output(['node','scripts/export_baseball_portrait_preferences.cjs'],text=True))
reg=json.loads((d/'player_portraits.json').read_text())
report={'transfer_profiles':0,'registered_transfer_profiles':0,'preferred_school_available':[],'preferred_school_missing':[],'owner_preferred':[]}
for p in players:
    schools=p['preference']['schools']
    if len(schools)<2:continue
    report['transfer_profiles']+=1
    r=reg.get(p['id'])
    if not r:continue
    report['registered_transfer_profiles']+=1
    row={'id':p['id'],'name':p['name'],'metric':p['preference']['metric'],'schools':schools,'current_school':r.get('school')}
    if r.get('owner_preferred'):
        report['owner_preferred'].append(row);continue
    preferred=schools[0]['school']
    records=[r,*r.get('fallbacks',[])]
    if any(x.get('provider')=='college' and x.get('school')==preferred for x in records):
        report['preferred_school_available'].append(row)
    else:report['preferred_school_missing'].append(row)
(d/'transfer_portrait_preference_audit.json').write_text(json.dumps(report,indent=2,ensure_ascii=False)+'\n')
print(json.dumps({k:len(v) if isinstance(v,list) else v for k,v in report.items()},indent=2))
