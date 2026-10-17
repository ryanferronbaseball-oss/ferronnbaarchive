(()=>{
"use strict";
const esc=v=>String(v??"").replace(/[&<>"']/g,c=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[c]));
const date=v=>new Date(v+"T12:00:00").toLocaleDateString("en-US",{month:"short",day:"numeric",year:"numeric"});
const fmt=v=>Number(v).toLocaleString("en-US",{maximumFractionDigits:2});
const num=v=>Number(v)||0, yes=v=>v!=null&&v!=="";
const asInt=v=>Math.round(num(v)), pad=v=>String(v).padStart(2,"0");
const playerUrl=p=>"./player.html?id="+encodeURIComponent(p.player_id);
const gameUrl=g=>"./game.html?id="+encodeURIComponent(g.attendance_id);
function nav(active){
const paths=[["index.html","Overview","home"],["game.html","Games","games"],["stats.html","Players","players"],["hall-of-fame.html","★ Hall of Fame","hof"],["statcast.html","Statcast","statcast"],["records.html","Records","records"]];
return '<header class="archive-header"><a class="archive-logo" href="./index.html">COURTSIDE ARCHIVE<small>EVERY GAME HAS A STORY · MLB</small></a><nav class="archive-nav" aria-label="MLB archive navigation">'
+paths.map(([href,name,key])=>'<a href="./'+href+'"'+(active===key?' aria-current="page"':'')+'>'+name+'</a>').join("")
+'<a href="../index.html" class="back-link">All sports ↗</a></nav></header>';
}
async function fetchJSON(path,fallback){
try{let res=await fetch(path,{cache:"no-store"});if(!res.ok)return fallback;return await res.json()}catch(e){return fallback}}
async function load(){
const attendance=await fetchJSON("./data/attendance.json",[]);
if(!attendance.length)throw Error("Original MLB game log unavailable");
const games=await fetchJSON("./data/games.json",attendance),rows=await fetchJSON("./data/player_stats.json",[]),scores=await fetchJSON("./data/scoring_plays.json",{}),decisions=await fetchJSON("./data/decisions.json",{});
const byGame=new Map(games.map(g=>[String(g.attendance_id),g]));
const playerMap=new Map();
for(const r of rows){
const id=String(r.player_id);let p=playerMap.get(id);
if(!p){p={player_id:r.player_id,name:r.name,team_ids:new Set(),teams:new Set(),games:new Set(),rows:[],batting:[],pitching:[],fielding:[]};playerMap.set(id,p)}
p.games.add(r.game_pk);p.teams.add(r.team);p.team_ids.add(r.team_id);p.rows.push(r);
if(r.batting&&num(r.batting.plateAppearances)+num(r.batting.atBats)>0)p.batting.push(r);
if(r.pitching&&num(r.pitching.outs)!=null&&r.pitching.outs!==null)p.pitching.push(r);
if(r.fielding)p.fielding.push(r);
}
for(const p of playerMap.values()){p.game_count=p.games.size;p.teams=[...p.teams];p.team_ids=[...p.team_ids];}
return {attendance,games,rows,scores,decisions,players:[...playerMap.values()],byGame,byPlayer:playerMap};
}
const bFields=["plateAppearances","atBats","runs","hits","doubles","triples","homeRuns","rbi","baseOnBalls","strikeOuts","hitByPitch","stolenBases","caughtStealing","sacFlies","sacBunts","totalBases"];
const pFields=["outs","hits","runs","earnedRuns","baseOnBalls","strikeOuts","homeRuns","numberOfPitches","battersFaced","wins","losses","saves"];
const abbr={plateAppearances:"PA",atBats:"AB",runs:"R",hits:"H",doubles:"2B",triples:"3B",homeRuns:"HR",rbi:"RBI",baseOnBalls:"BB",strikeOuts:"SO",hitByPitch:"HBP",stolenBases:"SB",caughtStealing:"CS",totalBases:"TB",inningsPitched:"IP",earnedRuns:"ER",outs:"Outs",battersFaced:"BF",numberOfPitches:"Pitches",wins:"W",losses:"L",saves:"SV",average:"AVG",onBasePercentage:"OBP",sluggingPercentage:"SLG",ops:"OPS",era:"ERA",whip:"WHIP",k9:"K/9",bb9:"BB/9"};
function addStats(rows,type){
const fields=type==="batting"?bFields:pFields;
const totals={};
for(const k of fields)totals[k]=rows.reduce((n,r)=>n+num(r[type]?.[k]),0);
totals.games=rows.length;
if(type==="batting"){
 const {hits:h,atBats:ab,baseOnBalls:bb,hitByPitch:hbp,sacFlies:sf,totalBases:tb}=totals;
 const singles=h-totals.doubles-totals.triples-totals.homeRuns;
 totals.totalBasesComputed=singles+2*totals.doubles+3*totals.triples+4*totals.homeRuns;
 totals.average=ab?h/ab:null;totals.onBasePercentage=ab+bb+hbp+sf?(h+bb+hbp)/(ab+bb+hbp+sf):null;
 totals.sluggingPercentage=ab?totals.totalBasesComputed/ab:null;
 totals.ops=totals.onBasePercentage!=null&&totals.sluggingPercentage!=null?totals.onBasePercentage+totals.sluggingPercentage:null;
}else{
 const {outs,earnedRuns:er,baseOnBalls:bb,hits:h,strikeOuts:k}=totals;
 totals.inningsPitched=Math.floor(outs/3)+"."+(outs%3);
 totals.era=outs?er*27/outs:null;totals.whip=outs?(h+bb)*3/outs:null;totals.k9=outs?k*27/outs:null;totals.bb9=outs?bb*27/outs:null;
}return totals;
}

/* Custom, unofficial single-player game impact index, common scale for batters
   and pitchers. This is NOT a MLB award or traditional pitching Game Score.
   Two-way contributions are summed for one player, with no team-win bias. */
function playerImpact(row){
 const b=row.batting||{},p=row.pitching||{};
 const battingActive=Object.keys(b).length>0 &&
  ["atBats","hits","runs","rbi","baseOnBalls","hitByPitch","stolenBases"].some(k=>num(b[k])>0);
 const pitchingActive=Object.keys(p).length>0 &&
  (p.outs!=null||p.inningsPitched!=null||row.pitching_appearance_index!=null);
 if(!battingActive&&!pitchingActive)return null;
 let hitterScore=0,pitcherScore=0;
 if(battingActive){
  const h=num(b.hits),dbl=num(b.doubles),tri=num(b.triples),hr=num(b.homeRuns);
  const singles=Math.max(0,h-dbl-tri-hr);
  const totalBases=singles+2*dbl+3*tri+4*hr;
  hitterScore=totalBases+0.9*num(b.rbi)+0.7*num(b.runs)
    +0.7*(num(b.baseOnBalls)+num(b.hitByPitch))
    +1.1*num(b.stolenBases)-0.8*num(b.caughtStealing)-0.15*num(b.strikeOuts);
 }
 if(pitchingActive){
  // Use true recorded outs: the final .1 / .2 in IP means one/two outs.
  const outs=p.outs!=null?num(p.outs):0;
  pitcherScore=1.5*outs/3+0.65*num(p.strikeOuts)
    -1.8*num(p.earnedRuns)-0.35*num(p.hits)-0.35*num(p.baseOnBalls)
    -0.5*num(p.homeRuns)-0.2*num(p.hitBatsmen);
  // Rare documented pitching milestone, no inferred fielding or pitch tracking.
  if(outs>=27&&num(p.hits)===0&&num(p.runs)===0)pitcherScore+=2;
 }
 const parts=[];
 if(battingActive){
  const hits=num(b.hits),ab=num(b.atBats),hrs=num(b.homeRuns);
  if(ab||hits)parts.push(hits+"-for-"+ab);
  if(hrs)parts.push(hrs+" HR");
  if(num(b.rbi))parts.push(num(b.rbi)+" RBI");
  if(num(b.stolenBases))parts.push(num(b.stolenBases)+" SB");
  if(!parts.length&&num(b.baseOnBalls))parts.push(num(b.baseOnBalls)+" BB");
 }
 if(pitchingActive){
  if(p.inningsPitched!=null)parts.push(p.inningsPitched+" IP");
  else if(p.outs!=null)parts.push(Math.floor(p.outs/3)+"."+(p.outs%3)+" IP");
  parts.push(num(p.strikeOuts)+" K");
  parts.push(num(p.earnedRuns)+" ER");
 }
 return {row,score:Math.round((hitterScore+pitcherScore)*100)/100,
  battingScore:Math.round(hitterScore*100)/100,pitchingScore:Math.round(pitcherScore*100)/100,
  role:battingActive&&pitchingActive?"Two-way":pitchingActive?"Pitching":"Batting",
  line:parts.join(" · ")};
}
function playerOfGame(gameRows){
 const eligible=gameRows.map(playerImpact).filter(Boolean);
 eligible.sort((a,b)=>b.score-a.score||b.pitchingScore-a.pitchingScore||
   num(b.row.batting?.totalBases)-num(a.row.batting?.totalBases)||
   String(a.row.player_id).localeCompare(String(b.row.player_id)));
 return eligible[0]||null;
}

function oneStat(r,category,key){let raw=r?.[category];if(!raw)return 0;return num(raw[key])}
function disp(value,key){if(value==null)return "—";if(["average","onBasePercentage","sluggingPercentage","ops"].includes(key))return Number(value).toFixed(3).replace(/^0/,"");if(["era","whip","k9","bb9"].includes(key))return Number(value).toFixed(2);return String(value)}
function gameCard(g){
const verified=g.game_pk!=null,score=verified&&yes(g.away_score)&&yes(g.home_score)?g.away_score+" – "+g.home_score:"Match pending";
return '<article class="game-card"><div class="game-date">'+date(g.date)+' · '+esc(g.ballpark)+'</div><h3>'+esc(g.away)+' @ '+esc(g.home)+'</h3><div class="game-score">'+esc(score)+'</div>'
 +'<div class="caption">'+(verified?'Verified official game #'+g.game_pk:'Original attendance entry #'+g.attendance_id)+'</div><a class="action-link" href="'+gameUrl(g)+'">View game ↗</a></article>';
}
function table(headers,body,empty="No verified data available yet"){
const hdr='<thead><tr>'+headers.map(h=>'<th>'+esc(h)+'</th>').join("")+'</tr></thead>';
return '<div class="table-wrap"><table class="mlb-sticky">'+hdr+'<tbody>'+(body.join("")||'<tr><td colspan="'+headers.length+'">'+esc(empty)+'</td></tr>')+'</tbody></table></div>';
}
function bar(entries){const max=Math.max(1,...entries.map(x=>x[1]));return entries.map(([label,n])=>'<div class="mlb-bar"><span>'+esc(label)+'</span><div class="mlb-track"><div class="mlb-fill" style="width:'+((n/max)*100).toFixed(2)+'%"></div></div><strong>'+n+'</strong></div>').join("")}
function tiles(items){return '<div class="metrics">'+items.map(([l,n])=>'<div class="metric"><strong>'+esc(n)+'</strong><small>'+esc(l)+'</small></div>').join("")+'</div>'}
function record(label,value,description,link){return '<article class="mlb-record"><small>'+esc(label)+'</small><strong>'+esc(value)+'</strong><p>'+esc(description||"")+'</p>'+(link?'<a href="'+link+'">Explore →</a>':"")+'</article>'}
function mlbRow(g){return '<tr><td><a href="'+gameUrl(g)+'">'+date(g.date)+'</a></td><td>'+esc(g.away)+" @ "+esc(g.home)+'</td><td>'+esc(g.ballpark)+'</td><td>'+((g.game_pk!=null&&yes(g.away_score)&&yes(g.home_score))?g.away_score+"–"+g.home_score:"—")+'</td><td>'+ (g.game_pk!=null?'<span class="mlb-pill verified">Matched</span>':'<span class="mlb-pill pending">Pending</span>')+'</td><td><a href="'+gameUrl(g)+'">View →</a></td></tr>'}
window.MLBArchive={esc,date,fmt,num,yes,pad,nav,load,addStats,disp,oneStat,gameCard,gameUrl,playerUrl,table,bar,tiles,record,mlbRow,abbr,playerImpact,playerOfGame};
})();
;(()=>{if(document.querySelector('script[data-ca-player-search]'))return;const s=document.createElement('script');s.dataset.caPlayerSearch='1';s.src='../assets/player-search.js?v=quicksearch-20261016v2';document.head.appendChild(s)})();
