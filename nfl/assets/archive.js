(function () {
"use strict";
const base="./data/";
const GROUPS={
  offense:[["passing","Passing"],["rushing","Rushing"],["receiving","Receiving"]],
  defense:[["defensive","Tackles & Defense"],["interceptions","Interceptions"],["fumbles","Fumbles & Recoveries"]],
  special:[["kicking","Kicking"],["punting","Punting"],["kickReturns","Kick Returns"],["puntReturns","Punt Returns"]]
};
const TITLES={offense:"Offense",defense:"Defense",special:"Special Teams"};
const esc=v=>String(v??"").replace(/[&<>"']/g,c=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[c]));
const date=v=>new Date(v+"T12:00:00").toLocaleDateString("en-US",{month:"long",day:"numeric",year:"numeric"});
const fmt=v=>Number(v).toLocaleString("en-US",{maximumFractionDigits:2});
function numeric(v){const n=Number(String(v??"").replaceAll(",",""));return Number.isFinite(n)?n:0}
function madeAttempt(v){const a=String(v||"").split("/");return [numeric(a[0]),numeric(a[1])]}
function isLong(label){return /^LONG$|^LG$/i.test(label)}
function isRate(label){return /^(AVG|PCT|QBR|RTG|RATE)$/i.test(label)}
function totalColumn(rows,category,label,i){
 const vals=rows.map(x=>String(x.stat_values[i]??""));
 if(["C/ATT","FG","XP"].includes(label)){
  const [made,attempts]=vals.reduce((a,v)=>{const [m,t]=madeAttempt(v);return [a[0]+m,a[1]+t]},[0,0]);
  return made+"/"+attempts;
 }
 if(isLong(label))return fmt(Math.max(0,...vals.map(numeric)));
 if(label==="QBR")return "—";
 if(label==="RTG"&&category==="passing"){
  const labels=rows[0].stat_labels,ca=labels.indexOf("C/ATT"),yd=labels.indexOf("YDS"),td=labels.indexOf("TD"),inter=labels.indexOf("INT");
  if([ca,yd,td,inter].some(i=>i<0))return "—";
  const [com,att]=rows.reduce((a,x)=>{const [m,t]=madeAttempt(x.stat_values[ca]);return [a[0]+m,a[1]+t]},[0,0]);
  if(!att)return "—";
  const yards=rows.reduce((a,x)=>a+numeric(x.stat_values[yd]),0),tds=rows.reduce((a,x)=>a+numeric(x.stat_values[td]),0),ints=rows.reduce((a,x)=>a+numeric(x.stat_values[inter]),0);
  const clip=x=>Math.max(0,Math.min(2.375,x));
  return (((clip((com/att-.3)*5)+clip((yards/att-3)*.25)+clip(tds/att*20)+clip(2.375-ints/att*25))/6)*100).toFixed(1);
 }
 if(label==="AVG"){
  const labels=rows[0].stat_labels,yd=labels.indexOf("YDS");
  const denominatorLabel=({rushing:"CAR",receiving:"REC",punting:"NO",kickReturns:"NO",puntReturns:"NO",passing:"C/ATT"})[category];
  const denominator=labels.indexOf(denominatorLabel);
  if(yd<0||denominator<0)return "—";
  const yards=rows.reduce((a,x)=>a+numeric(x.stat_values[yd]),0);
  const events=rows.reduce((a,x)=>a+(denominatorLabel==="C/ATT"?madeAttempt(x.stat_values[denominator])[1]:numeric(x.stat_values[denominator])),0);
  return events?(yards/events).toFixed(1):"—";
 }
 if(label==="PCT"&&category==="kicking"){
  const iFg=rows[0].stat_labels.indexOf("FG");
  if(iFg<0)return "—";
  const [made,total]=rows.reduce((a,x)=>{const [m,t]=madeAttempt(x.stat_values[iFg]);return [a[0]+m,a[1]+t]},[0,0]);
  return total?(made/total*100).toFixed(1):"—";
 }
 if(isRate(label))return "—";
 const total=vals.reduce((sum,v)=>sum+numeric(v),0);
 return fmt(total);
}
function group(rows,category){
 const map=new Map();
 for(const r of rows.filter(x=>x.category===category)){
  const id=String(r.athlete_id),arr=map.get(id)||[];arr.push(r);map.set(id,arr)
 }
 return [...map.entries()].map(([id,items])=>{
  const first=items[0],labels=first.stat_labels||[];
  return {athlete_id:id,player:first.player,team:[...new Set(items.map(x=>x.team))].join(", "),
    games:new Set(items.map(x=>x.game_id)).size,labels,
    stat_values:labels.map((l,i)=>totalColumn(items,category,l,i))};
 });
}
function scoreValue(r,index){
 const val=r.stat_values[index];if(typeof val==="number")return val;
 if(String(val).includes("/"))return numeric(String(val).split("/")[0]);
 return numeric(val);
}
function defaultColumn(cat,labels){
 const key=({passing:"YDS",rushing:"YDS",receiving:"YDS",defensive:"TOT",interceptions:"INT",
 fumbles:"FUM",kicking:"PTS",punting:"YDS",kickReturns:"YDS",puntReturns:"YDS"})[cat]||"YDS";
 return Math.max(0,labels.indexOf(key));
}
function sortPlayers(rows,cat,index=null,direction="desc"){
 if(!rows.length)return rows;
 const col=index==null?defaultColumn(cat,rows[0].labels||rows[0].stat_labels||[]):index;
 return rows.sort((a,b)=>{
  const va=scoreValue(a,col),vb=scoreValue(b,col);
  return (direction==="asc"?va-vb:vb-va)||a.player.localeCompare(b.player)
 });
}
function table(rows,category,{combined=false,empty="No players with recorded statistics in this category."}={}){
 if(!rows.length)return '<div class="empty">'+esc(empty)+'</div>';
 const labels=(rows[0].labels||rows[0].stat_labels||[]);
 return '<div class="table-wrap"><table><thead><tr><th scope="col">Player</th>'+
   (combined?'<th scope="col">G</th>':'')+labels.map(l=>'<th scope="col">'+esc(l)+'</th>').join("")+
   '</tr></thead><tbody>'+rows.map(x=>'<tr><td><a href="./player.html?id='+encodeURIComponent(x.athlete_id)+'">'+esc(x.player)+'</a><small>'+esc(x.team)+'</small></td>'+
   (combined?'<td>'+x.games+'</td>':'')+
   x.stat_values.map(s=>'<td>'+esc(s)+'</td>').join("")+'</tr>').join("")+'</tbody></table></div>';
}
function nav(active){
 const links=[["index.html","Overview","home"],["game.html","Games & Box Scores","game"],["stats.html","Leaderboards","stats"],["milestones.html","PPR Milestones","milestones"],["records.html","Records","records"],["touchdowns.html","Touchdowns","touchdowns"],["highlights.html","Highlights","highlights"],["hall-of-fame.html","Hall of Fame","hof"]];
 return '<header class="archive-header"><a class="archive-logo" href="./index.html">COURTSIDE ARCHIVE<small>EVERY GAME HAS A STORY · NFL</small></a>'+
   '<nav class="archive-nav" aria-label="NFL archive navigation">'+links.map(([href,title,name])=>'<a href="./'+href+'"'+(active===name?' aria-current="page"':'')+'>'+title+'</a>').join("")+
   '</nav><a class="back-link" href="../index.html">All archives ↗</a></header>';
}
function gameTitle(g){return g.away+" at "+g.home}
function gameCard(g){
 return '<article class="game-card"><div class="game-date">'+esc(date(g.date))+' · '+(g.overtime?'Overtime':'Regulation')+'</div>'+
  '<h3>'+esc(gameTitle(g))+'</h3><div class="game-score">'+esc(g.away_abbr)+' '+g.away_score+' <span>—</span> '+esc(g.home_abbr)+' '+g.home_score+'</div>'+
  '<div class="caption">'+esc(g.stadium)+' · '+esc(g.city)+', '+esc(g.state)+'</div>'+
  '<a class="action-link" href="./game.html?id='+encodeURIComponent(g.id)+'">Game box score ↗</a></article>';
}
function period(n){return n>4?"OT"+(n>5?" "+(n-4):""):"Q"+n}
function scoring(plays,g){
 if(!plays.length)return '<div class="empty">Scoring chronology is not available for this game.</div>';
 return '<div class="scoring-list">'+plays.map(p=>
 '<div class="play"><div class="play-time">'+period(p.period)+'<br>'+esc(p.clock)+'</div>'+
 '<div><div class="play-label">'+esc(p.team)+' · '+esc(p.type)+' · '+p.points+' point'+(p.points===1?'':'s')+'</div>'+
 '<div class="play-description">'+esc(p.description)+'</div>'+(p.conversion?'<div class="play-detail">Conversion: '+esc(p.conversion)+'</div>':'')+'</div>'+
 '<div class="play-score">'+esc(g.away_abbr)+' '+p.away_score+'<br>'+esc(g.home_abbr)+' '+p.home_score+'</div></div>').join("")+'</div>';
}
function scoreboard(g){
 const a=g.quarters.away,h=g.quarters.home,max=Math.max(a.length,h.length);
 const head=Array.from({length:max},(_,i)=>'<th scope="col">'+period(i+1)+'</th>').join("");
 const row=(name,arr,total)=>'<tr><td>'+esc(name)+'</td>'+Array.from({length:max},(_,i)=>'<td>'+esc(arr[i]??"—")+'</td>').join("")+'<td><strong>'+total+'</strong></td></tr>';
 return '<div class="scoreboard"><div class="game-date">'+esc(date(g.date))+' · Week '+g.week+' · '+esc(g.stadium)+'</div>'+
 '<div class="scoreline"><div><div class="team-scoreline"><span class="team-name">'+esc(g.away)+'</span><span class="team-score">'+g.away_score+'</span></div>'+
 '<div class="team-scoreline"><span class="team-name">'+esc(g.home)+'</span><span class="team-score">'+g.home_score+'</span></div></div>'+
 '<span class="game-date">'+(g.overtime?'FINAL / OT':'FINAL')+'</span></div>'+
 '<div class="table-wrap" style="margin-top:20px"><table class="quarters"><thead><tr><th>Team</th>'+head+'<th>Final</th></tr></thead><tbody>'+row(g.away_abbr,a,g.away_score)+row(g.home_abbr,h,g.home_score)+'</tbody></table></div></div>';
}
async function load(){
 const names=["games.json","player_stats.json","scoring_plays.json","fantasy_ppr.json"];
 const a=await Promise.all(names.map(async file=>{const r=await fetch(base+file,{cache:"no-store"});if(!r.ok)throw Error("Unable to load "+file+" ("+r.status+")");return r.json()}));
 return {games:a[0],rows:a[1],scoring:a[2],ppr:a[3]};
}
window.NFLArchive={GROUPS,TITLES,esc,date,fmt,numeric,group,sortPlayers,defaultColumn,table,nav,gameTitle,gameCard,period,scoring,scoreboard,load};
})();
