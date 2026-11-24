(function(){
"use strict";
const names={"1":"Atlanta Hawks","2":"Boston Celtics","3":"New Orleans Hornets","4":"Chicago Bulls","5":"Cleveland Cavaliers","7":"Denver Nuggets","9":"Golden State Warriors","10":"Houston Rockets","12":"LA Clippers","13":"LA Lakers","14":"Miami Heat","16":"Minnesota Timberwolves","18":"New York Knicks","21":"Phoenix Suns","23":"Sacramento Kings","24":"San Antonio Spurs","25":"Oklahoma City Thunder","26":"Utah Jazz","30":"Charlotte Bobcats"};
const abbr={"1":"atl","2":"bos","3":"no","4":"chi","5":"cle","7":"den","9":"gs","10":"hou","12":"lac","13":"lal","14":"mia","16":"min","18":"ny","21":"phx","23":"sac","24":"sa","25":"okc","26":"utah","30":"cha"};
const esc=v=>String(v??"").replace(/[&<>"']/g,c=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[c]));
const valid=p=>p&&p.player_id!=null&&p.team_id!=null&&p.minutes!=null&&p.minutes!==""&&p.minutes!=="--";
const teamName=id=>names[String(id)]||"Unknown team";
const logoUrl=(id,date)=>window.CAHistoricalLogos.resolve("nba",id,date)?.src||null;
const logo=(id,name,date)=>window.CAHistoricalLogos.image("nba",id,date,name);
const sum=(rows,key)=>rows.reduce((n,p)=>n+(Number(p[key])||0),0);
const fmt=(n,d=1)=>Number.isFinite(n)?n.toFixed(d):"—";
function group(rows){
 const players=new Map();
 for(const p of rows||[]){
  if(!valid(p))continue;
  const pid=String(p.player_id),tid=String(p.team_id);
  let entry=players.get(pid);
  if(!entry){entry={id:pid,name:p.player||"Unknown player",teams:new Map()};players.set(pid,entry)}
  let team=entry.teams.get(tid);
  if(!team){team={id:tid,name:teamName(tid),first:p.date||"9999",rows:[],seen:new Set()};entry.teams.set(tid,team)}
  if(p.date&&p.date<team.first)team.first=p.date;
  team.name=window.CAHistoricalLogos.name("nba",tid,team.first,teamName(tid));
  // The same player-game must not inflate totals on a repeated import.
  const key=String(p.espn_event_id||p.game_id||p.date||"");
  if(team.seen.has(key))continue;
  team.seen.add(key);
  team.rows.push(p);
 }
 return [...players.values()].map(p=>({id:p.id,name:p.name,teams:[...p.teams.values()].sort((a,b)=>a.first.localeCompare(b.first)||a.name.localeCompare(b.name))})).map(p=>({...p,games:p.teams.reduce((n,t)=>n+t.rows.length,0)}));
}
function stat(t){const r=t.rows,n=r.length;return {games:n,mpg:n?sum(r,"minutes")/n:null,ppg:n?sum(r,"pts")/n:null,rpg:n?sum(r,"reb")/n:null,apg:n?sum(r,"ast")/n:null};}
function journey(teams){return teams.map((t,i)=>(i?'<span class="multi-arrow" aria-hidden="true">→</span>':"")+'<div class="multi-school">'+logo(t.id,t.name,t.first)+'<div><strong>'+esc(t.name)+'</strong><small>First seen '+esc(t.first==="9999"?"—":t.first.slice(0,4))+'</small></div></div>').join("");}
window.NBAMultiTeams={names,abbr,esc,valid,teamName,logoUrl,logo,group,stat,journey,fmt};
})();