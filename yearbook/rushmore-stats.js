/* Annual witnessed statistics, computed from archive box scores rather than season totals. */
(()=>{
"use strict";
const cache=new Map();
const get=path=>{if(!cache.has(path))cache.set(path,fetch(path).then(r=>{if(!r.ok)throw Error(path);return r.json()}));return cache.get(path)};
const num=v=>v===null||v===undefined||v===""||!Number.isFinite(Number(v))?null:Number(v);
const total=(a,k)=>a.length&&a.every(x=>num(x[k])!==null)?a.reduce((s,x)=>s+Number(x[k]),0):null;
const fmt=(v,d)=>v==null?"—":d==null?String(v):v.toFixed(d).replace(d===3?/^0(?=\.)/:/$^/,"");
const yr=(v,y)=>String(v||"").slice(0,4)===String(y);
const outs=v=>{const m=/^(\d+)(?:\.([012]))?$/.exec(String(v??""));return m?3*Number(m[1])+Number(m[2]||0):null};
const group=(label,items)=>({label,items});
const pitchers=new Set(["111554","276336","150378","117955","134320","461212","435178","450351","477132","450308","456701","518886","543408","488768","664192","605483","519242","cb-san-diego-nick-sprengel","cb-san-diego-chris-murphy","cb-san-diego-jake-miller","cb-san-diego-brycen-mautz","cb-lsu-kade-anderson"]);
function baseball(rows,sport,p){
 const milb=sport==="MiLB",cb=sport==="CB",id=r=>String(r.game_id??r.game_pk??r.attendance_id);
 const batting=rows.filter(r=>r.batting&&(cb||milb||Number(r.batting.plateAppearances||0)+Number(r.batting.atBats||0)>0));
 const pitching=rows.filter(r=>r.pitching&&(cb||milb||r.pitching.outs!=null));
 const b=batting.map(r=>{let x=r.batting;return milb?{ab:x.ab,h:x.h,bb:x.bb,d:x.doubles,t:x.triples,hr:x.hr,rbi:x.rbi,hbp:x.hbp,sf:x.sf,pa:x.pa}:{ab:x.atBats,h:x.hits,bb:x.baseOnBalls,d:x.doubles,t:x.triples,hr:x.homeRuns,rbi:x.rbi,hbp:x.hitByPitch,sf:x.sacFlies,pa:cb?["atBats","baseOnBalls","hitByPitch","sacFlies","sacBunts"].every(k=>num(x[k])!==null)?["atBats","baseOnBalls","hitByPitch","sacFlies","sacBunts"].reduce((s,k)=>s+Number(x[k]),0)+Number(x.catcherInterference||0):null:x.plateAppearances}});
 const q=pitching.map(r=>{let x=r.pitching;return {o:milb?outs(x.ip):x.outs,er:milb?x.er:x.earnedRuns,k:milb?x.so:x.strikeOuts}});
 const sum=k=>total(b,k),ab=sum("ab"),h=sum("h"),bb=sum("bb"),hbp=sum("hbp"),sf=sum("sf"),d=sum("d"),t=sum("t"),hr=sum("hr"),den=[ab,bb,hbp,sf].every(x=>x!==null)?ab+bb+hbp+sf:null;
 const ops=den>0&&ab>0&&[h,d,t,hr].every(x=>x!==null)?(h+bb+hbp)/den+(h+d+2*t+3*hr)/ab:null;
 const o=total(q,"o"),er=total(q,"er");
 const hit=group("Hitting",[["G",new Set(batting.map(id)).size],["PA",fmt(sum("pa"))],["OPS",fmt(ops,3)],["HR",fmt(hr)],["RBI",fmt(sum("rbi"))]]);
 const pitch=group("Pitching",[["G",new Set(pitching.map(id)).size],["IP",o==null?"—":Math.floor(o/3)+"."+o%3],["ERA",fmt(o>0&&er!==null?27*er/o:null,2)],["K",fmt(total(q,"k"))]]);
 if(p.id==="660271")return [hit,pitch].filter(g=>g.items[0][1]>0);
 return pitchers.has(p.id)||(!batting.length&&pitching.length)?[pitch]:[hit];
}
async function stats(p,y){
 if(p.sport==="NBA"||p.sport==="CBB"){
  const rows=await get(p.sport==="NBA"?"../data/player_boxscores_espn.json":"../college/data/player_boxscores_espn.json");
  const a=rows.filter(r=>String(r.player_id)===p.id&&yr(r.date,y)&&!r.did_not_play&&!/DNP|DND|inactive/i.test(String(r.minutes))&&Number.parseFloat(r.minutes)>0);
  if(!a.length)return [];
  return [group(a.length+" games played",[["PPG","pts"],["RPG","reb"],["APG","ast"],["SPG","stl"],["BPG","blk"]].map(([l,k])=>[l,fmt(total(a,k)==null?null:total(a,k)/a.length,1)]))];
 }
 if(["MLB","MiLB","CB"].includes(p.sport)){
  let rows,games;
  if(p.sport==="CB"){const d=await window.CARushmoreCollegeData.load();rows=d.rows;games=d.games;const id=d.redirects.get(p.id)||p.id;p={...p,id};}
  else{const dir=p.sport==="MLB"?"mlb":"milb";[rows,games]=await Promise.all([get("../"+dir+"/data/player_stats.json"),get("../"+dir+"/data/games.json")]);}
  const ids=new Set(games.filter(g=>yr(g.date,y)).map(g=>String(p.sport==="MLB"?g.game_pk:g.id)));
  const a=rows.filter(r=>String(r.player_id)===p.id&&ids.has(String(p.sport==="MLB"?r.game_pk:r.game_id)));
  return a.length?baseball(a,p.sport,p):[];
 }
 if(p.sport==="NFL"||p.sport==="CFB"){
  const rows=await get("../"+p.sport.toLowerCase()+"/data/player_stats.json");
  const a=rows.filter(r=>String(r.athlete_id)===p.id&&yr(r.date,y));
  if(!a.length)return [];
  const val=(r,l)=>num(r.stat_values?.[r.stat_labels?.indexOf(l)]);
  const add=(rs,l)=>rs.length?rs.every(r=>val(r,l)!==null)?rs.reduce((s,r)=>s+val(r,l),0):null:0;
  const pass=a.filter(r=>r.category==="passing");
  if(pass.length)return [group("Passing",[["YDS",fmt(add(pass,"YDS"))],["TD",fmt(add(pass,"TD"))],["INT",fmt(add(pass,"INT"))]])];
  const skill=a.filter(r=>/^(rushing|receiving|kickReturns|puntReturns|kick_returns|punt_returns|kick returns|punt returns)$/i.test(r.category));
  const returns=skill.filter(r=>!/^(rushing|receiving)$/.test(r.category)),rushrec=skill.filter(r=>/^(rushing|receiving)$/.test(r.category));
  const yards=add(rushrec,"YDS"),ret=add(returns,"YDS"),td=add(skill,"TD");
  return [group("Skill position",[["All-purpose YDS",fmt(yards===null||ret===null?null:yards+ret)],["TD",fmt(td)]])];
 }
 if(p.sport==="NHL"){
  const games=await get("../nhl/data/games.json");const a=games.filter(g=>yr(g.date,y)).flatMap(g=>g.players||[]).filter(x=>x.id===p.id&&x.goalie).map(x=>x.goalie);
  if(!a.length)return [];const saves=total(a,"saves"),shots=total(a,"shots_against");
  return [group("Goaltending",[["G",a.length],["SV",fmt(saves)],["SV%",fmt(shots>0&&saves!==null?saves/shots:null,3)],["SO",fmt(total(a,"shutouts"))]])];
 }
 return [];
}
window.CARushmoreStats={stats};
})();
