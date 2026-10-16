(() => {
"use strict";
const esc = value => String(value??"").replace(/[&<>"']/g,x=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[x]));
const fmt=value=>Number(value).toLocaleString("en-US",{maximumFractionDigits:1});
const date=v=>new Date(v+"T12:00:00").toLocaleDateString("en-US",{month:"short",day:"numeric",year:"numeric"});
const slug=x=>String(x).normalize("NFKD").replace(/[\u0300-\u036f]/g,"").toLowerCase().replace(/[^a-z0-9]+/g,"-").replace(/^-|-$/g,"");
const playerUrl=p=>"./player.html?id="+encodeURIComponent(slug(p));
const gameUrl=m=>"./game.html?id="+encodeURIComponent(m.id);
const goalTypes=new Set(["goal","penalty_goal","own_goal"]);
const isGoal=e=>goalTypes.has(e.type);
const eventOrder=e=>{let [m,s]=String(e.minute).split("+");return Number(m)*100+Number(s||0)};
const eventName={goal:"Goal",penalty_goal:"Penalty goal",own_goal:"Own goal",yellow:"Yellow card",red:"Red card",substitution:"Substitution"};
function nav(active){
 const links=[["index.html","Overview","home"],["game.html","Games","games"],["stats.html","Leaderboards","stats"],["records.html","Records","records"],["goals.html","Goals","goals"]];
 return '<header class="archive-header"><a class="archive-logo" href="./index.html">COURTSIDE ARCHIVE<small>EVERY GAME HAS A STORY · PRO SOCCER</small></a>'
 +'<nav class="archive-nav" aria-label="Soccer archive navigation">'
 +links.map(([href,label,key])=>'<a href="./'+href+'"'+(active===key?' aria-current="page"':'')+'>'+label+'</a>').join("")
 +'<a href="../index.html" class="back-link">All sports ↗</a></nav></header>';
}
async function load(){
 const r=await fetch("./data/matches.json",{cache:"no-store"});if(!r.ok)throw Error("Match data unavailable ("+r.status+")");const matches=await r.json();
 const players=new Map(); const byId=new Map(matches.map(m=>[m.id,m]));
 const ensure=(name,team,m)=>{
  const id=slug(name);let p=players.get(id);
  if(!p){p={id,name,teams:new Set(),matches:new Set(),starts:0,goals:0,assists:0,secondary_assists:0,penalties:0,own_goals:0,yellow:0,red:0,clean_sheets:0,events:[],matchLog:new Map()};players.set(id,p)}
  p.teams.add(team);
  if(!p.matchLog.has(m.id))p.matchLog.set(m.id,{id:m.id,date:m.date,team,opponent:team===m.home_abbr?m.away_abbr:m.home_abbr,started:false,goals:0,assists:0,secondary_assists:0,yellow:0,red:0,penalties:0,own_goals:0});
  return p;
 };
 for(const m of matches){
  for(const [team,starters,subs,against] of [
   [m.home_abbr,m.home_starters||[],m.home_subs_used||[],m.away_score],
   [m.away_abbr,m.away_starters||[],m.away_subs_used||[],m.home_score]
  ]){
   for(const name of new Set([...starters,...subs])){
    const p=ensure(name,team,m);p.matches.add(m.id);
    if(starters.includes(name)){p.starts++;p.matchLog.get(m.id).started=true;
      if(against===0 && starters[0]===name) p.clean_sheets++;// first listed starter is verified starting GK
    }
   }
  }
  for(const e of m.events||[]){
   if(e.player && e.type!=="own_goal"){
    const p=ensure(e.player,e.team,m),log=p.matchLog.get(m.id);
    p.events.push({...e,match_id:m.id,date:m.date});
    if(e.type==="goal"||e.type==="penalty_goal"){p.goals++;log.goals++;if(e.type==="penalty_goal"){p.penalties++;log.penalties++}}
    if(e.type==="yellow"){p.yellow++;log.yellow++}if(e.type==="red"){p.red++;log.red++}
   }
   if(e.type==="own_goal"&&e.player){
    const sourceTeam=e.team===m.home_abbr?m.away_abbr:m.home_abbr;
    const p=ensure(e.player,sourceTeam,m),log=p.matchLog.get(m.id);
    p.own_goals++;log.own_goals++;p.events.push({...e,match_id:m.id,date:m.date});
   }
   if(isGoal(e)){
    for(const [name,kind] of [[e.assist,"assists"],[e.secondary_assist,"secondary_assists"]]){
     if(!name)continue;const p=ensure(name,e.team,m);p[kind]++;p.matchLog.get(m.id)[kind]++;
    }
   }
  }
 }
 for(const p of players.values()){p.appearances=p.matches.size;p.contributions=p.goals+p.assists;p.teams=[...p.teams];p.matchLog=[...p.matchLog.values()].filter(x=>p.matches.has(x.id)).sort((a,b)=>b.date.localeCompare(a.date));}
 return {matches,players:[...players.values()],byId};
}
function statValue(p,key){return Number(p[key]||0)}
function leaderRows(players,key,limit,onlyNonzero=true){return players.filter(p=>!onlyNonzero||statValue(p,key)>0).sort((a,b)=>statValue(b,key)-statValue(a,key)||b.goals-a.goals||a.name.localeCompare(b.name)).slice(0,limit);}
function matchCard(m){return '<article class="game-card"><div class="eyebrow">'+esc(m.competition)+' · '+date(m.date)+'</div>'
 +'<h3>'+esc(m.home)+' <span class="green">'+m.home_score+'–'+m.away_score+'</span> '+esc(m.away)+'</h3>'
 +'<div class="caption">'+esc(m.venue)+' · '+esc(m.city)+'</div>'
 +'<a class="action-link" href="'+gameUrl(m)+'">Match report & lineups ↗</a></article>';}
function playerLink(p){return '<a href="'+playerUrl(p.name)+'">'+esc(p.name)+'</a>'}
function formatMetric(n){return n===null||n===undefined?"—":fmt(n)}
function scored(m){return (m.events||[]).filter(isGoal).sort((a,b)=>eventOrder(a)-eventOrder(b))}
function scorerLabel(e){return esc(e.player||"Unattributed")+(e.type==="own_goal"?" (OG)":e.type==="penalty_goal"?" (PK)":"")}
function playerMatchStat(m,name){
 const ev=m.events||[];return {goals:ev.filter(e=>e.player===name&&(e.type==="goal"||e.type==="penalty_goal")).length,
 assists:ev.filter(e=>e.assist===name).length,secondary:ev.filter(e=>e.secondary_assist===name).length,
 yellow:ev.filter(e=>e.player===name&&e.type==="yellow").length,red:ev.filter(e=>e.player===name&&e.type==="red").length};
}
window.SoccerArchive={esc,fmt,date,slug,playerUrl,gameUrl,isGoal,eventOrder,eventName,nav,load,leaderRows,matchCard,playerLink,formatMetric,scored,scorerLabel,playerMatchStat};
})();