import json,urllib.request,pathlib
base="https://statsapi.mlb.com/api/v1"
def get(url):
 req=urllib.request.Request(url,headers={"User-Agent":"CourtsideArchive/1.0","Accept":"application/json"})
 with urllib.request.urlopen(req,timeout=35) as r:return json.load(r)
r=get(base+"/awards")
allawards=r.get("awards",[])
found=[{"id":a.get("id"),"name":a.get("name"),"description":a.get("description")} for a in allawards if any(x in str(a.get("name","")).lower() for x in ["most valuable","cy young","gold glove","silver slugger","hall of fame","mvp","gold glov"])]
print("AWARDS COUNT",len(allawards))
print("RELEVANT",json.dumps(found,ensure_ascii=False))
allSamples={}
for id in [x["id"] for x in found if x.get("id")][:9]:
 try:
  d=get(base+"/awards/"+str(id)+"/recipients")
  values=d.get("awards",[])
  total=sum(len(a.get("recipient",[])) if isinstance(a.get("recipient"),list) else len(a.get("recipients",[])) for a in values)
  allSamples[id]={"keys":list(d),"awardsCount":len(values),"first":values[0] if values else None,"totalEstimate":total}
  print("SAMPLE",id,"keys",list(d),"count",len(values),"firstKeys",list(values[0]) if values else [])
 except Exception as exc:allSamples[id]={"error":str(exc)}
for suffix in ["/people/605141/awards","/people/605141?hydrate=awards","/people/605141/stats?stats=awards"]:
 try:
  d=get(base+suffix)
  allSamples[suffix]={"keys":list(d),"example":str(d)[:2200]}
  print("PERSON",suffix,"keys",list(d))
 except Exception as exc:allSamples[suffix]={"error":str(exc)}
path=pathlib.Path(__file__).resolve().parents[1]/"data/award_catalog_probe.json"
path.write_text(json.dumps({"catalog":found,"samples":allSamples},indent=2,ensure_ascii=False)+"\n")
