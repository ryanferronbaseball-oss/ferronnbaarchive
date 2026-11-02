/* College-to-MLB directory: witnessed college stats never mix with professional stats. */
(()=>{
"use strict";
const $=id=>document.getElementById(id);
const esc=v=>String(v??"").replace(/[&<>"']/g,c=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[c]));
const number=v=>Number.isFinite(Number(v))?Number(v):0;
const fmt=v=>number(v).toLocaleString("en-US");
const date=v=>v?new Date(String(v)+"T12:00:00").toLocaleDateString("en-US",{month:"short",day:"numeric",year:"numeric"}):"Not confirmed";
const ip=outs=>Math.floor(number(outs)/3)+"."+(number(outs)%3);
const playerUrl=id=>"./player.html?id="+encodeURIComponent(id);
const gameUrl=id=>"./game.html?id="+encodeURIComponent(id);
let players=[];

function aggregate(archive,registry){
 if(!registry||!Array.isArray(registry.players))throw Error("Missing verified college-to-MLB roster");
 const byId=new Map(archive.players.map(p=>[p.player_id,p]));
 const seenCollege=new Set(),seenMlb=new Set();
 return registry.players.map(record=>{
  if(!record.college_player_id||!Number.isInteger(record.mlb_player_id)||!record.name||!record.mlb_debut)throw Error("Incomplete verified MLB alumni record");
  if(seenCollege.has(record.college_player_id)||seenMlb.has(record.mlb_player_id))throw Error("Duplicate MLB alumni identity");
  seenCollege.add(record.college_player_id);seenMlb.add(record.mlb_player_id);
  const player=byId.get(record.college_player_id);
  if(!player)throw Error("Unmatched college player: "+record.name);
  const byGame=new Map();
  for(const row of player.rows){
   const game=archive.gameMap.get(row.game_id);
   if(!game)throw Error("Unmatched attended game: "+row.game_id);
   let item=byGame.get(game.id);
   if(!item){item={id:game.id,date:game.date,team:row.team,hits:0,homeRuns:0,rbi:0,outs:0,strikeouts:0,batting:false,pitching:false};byGame.set(game.id,item)}
   if(row.batting){item.batting=true;item.hits+=number(row.batting.hits);item.homeRuns+=number(row.batting.homeRuns);item.rbi+=number(row.batting.rbi)}
   if(row.pitching){item.pitching=true;item.outs+=number(row.pitching.outs);item.strikeouts+=number(row.pitching.strikeOuts)}
  }
  const games=[...byGame.values()].sort((a,b)=>a.date.localeCompare(b.date)||a.id.localeCompare(b.id));
  if(!games.length)throw Error("Missing witnessed college games: "+record.name);
  const pitching=games.filter(g=>g.pitching),batting=games.filter(g=>g.batting);
  const pitchingFirst=pitching.length>batting.length;
  const top=(pitchingFirst?pitching:batting).slice().sort((a,b)=>pitchingFirst
   ?b.strikeouts-a.strikeouts||b.outs-a.outs
   :b.hits-a.hits||b.homeRuns-a.homeRuns||b.rbi-a.rbi)[0]||games[0];
  return {...record,teams:player.teams.slice(),games,
   hits:games.reduce((n,g)=>n+g.hits,0),strikeouts:games.reduce((n,g)=>n+g.strikeouts,0),
   top,topPitching:pitchingFirst};
 });
}

function compareDraftClass(a,b,newestFirst){
 const aYear=a.draft_pick==null?0:Number(a.draft_year)||0;
 const bYear=b.draft_pick==null?0:Number(b.draft_year)||0;
 if(!aYear)return bYear?1:a.name.localeCompare(b.name);
 if(!bYear)return -1;
 return (newestFirst?bYear-aYear:aYear-bYear)||a.draft_pick-b.draft_pick||a.name.localeCompare(b.name);
}

function render(){
 const query=$("search").value.trim().toLowerCase(),sort=$("sort").value;
 const matches=players.filter(p=>[p.name,...p.teams,p.draft_team||"",String(p.draft_year||"")].join(" ").toLowerCase().includes(query));
 matches.sort((a,b)=>sort==="name"?a.name.localeCompare(b.name)
  :sort==="hits"?b.hits-a.hits||a.name.localeCompare(b.name)
  :sort==="strikeouts"?b.strikeouts-a.strikeouts||a.name.localeCompare(b.name)
  :sort==="games"?b.games.length-a.games.length||a.name.localeCompare(b.name)
  :sort==="draft-newest"?compareDraftClass(a,b,true)
  :sort==="draft-oldest"?compareDraftClass(a,b,false)
  :(a.draft_pick??999)-(b.draft_pick??999)||a.name.localeCompare(b.name));
 if(!matches.length){
  $("cards").innerHTML='<div class="alumni-empty">'+(query?"No players match this search.":"No confirmed MLB alumni found.")+'</div>';
  return;
 }
 $("cards").innerHTML=matches.map(p=>{
  const draft=p.draft_pick!=null?`${p.draft_year} · Round ${p.draft_round} · Pick #${p.draft_pick} · ${p.draft_team}`:"Undrafted";
  const top=p.topPitching?ip(p.top.outs)+" IP · "+fmt(p.top.strikeouts)+" K":fmt(p.top.hits)+" H · "+fmt(p.top.homeRuns)+" HR · "+fmt(p.top.rbi)+" RBI";
  const attended=p.games.map(g=>'<a href="'+gameUrl(g.id)+'">'+esc(date(g.date))+'</a> ('+esc(g.team)+', '+(g.pitching&&!g.batting?ip(g.outs)+' IP, '+fmt(g.strikeouts)+' K':fmt(g.hits)+' H, '+fmt(g.rbi)+' RBI')+')').join(" · ");
  const initials=p.name.split(/\s+/).slice(0,2).map(w=>w[0]).join("");
  return '<article class="alumni-player">'
   +'<div class="alumni-head"><div class="alumni-identity"><div class="alumni-portrait">'+esc(initials)+'<img src="https://img.mlbstatic.com/mlb-photos/image/upload/w_213,q_85/v1/people/'+p.mlb_player_id+'/headshot/67/current" alt="" loading="lazy" onerror="this.style.display=\'none\'"></div><div><a class="alumni-name" href="'+playerUrl(p.college_player_id)+'">'+esc(p.name)+'</a><div class="alumni-school">'+p.teams.map(esc).join(" / ")+'</div></div></div><span class="alumni-pill">'+(p.mlb_debut?"MLB alumnus":"Drafted only")+'</span></div>'
   +'<div class="alumni-line"><div><strong>'+fmt(p.games.length)+'</strong><small>Games witnessed</small></div><div><strong>'+fmt(p.hits)+'</strong><small>College hits witnessed</small></div><div><strong>'+fmt(p.strikeouts)+'</strong><small>Pitcher K witnessed</small></div></div>'
   +'<div class="alumni-info"><b>When you watched:</b> '+esc(date(p.games[0].date))+' — '+esc(date(p.games.at(-1).date))+'</div>'
   +'<div class="alumni-info"><b>MLB Draft:</b> '+esc(draft)+'</div>'
   +'<div class="alumni-info"><b>MLB debut:</b> '+esc(date(p.mlb_debut))+'</div>'
   +'<div class="alumni-info"><b>Top attended performance:</b> '+esc(top)+'</div>'
   +'<div class="alumni-dates"><b>All attended appearances:</b> '+attended+'</div>'
   +'<div class="alumni-links"><a href="'+playerUrl(p.college_player_id)+'">College profile ↗</a><a href="https://www.mlb.com/player/'+p.mlb_player_id+'" rel="noopener noreferrer" target="_blank">MLB career source ↗</a></div></article>';
 }).join("");
}

async function start(){
 try{
  const [archive,response]=await Promise.all([window.CollegeBaseballArchive.load(),fetch("./data/mlb_alumni_seed.json",{cache:"no-store"})]);
  if(!response.ok)throw Error("Missing college-to-MLB records");
  const registry=await response.json();players=aggregate(archive,registry);
  const confirmed=players.filter(p=>p.mlb_debut);
  $("mlbCount").textContent=fmt(confirmed.length);
  $("seenCount").textContent=fmt(new Set(players.flatMap(p=>p.games.map(g=>g.id))).size);
  $("firstCount").textContent=fmt(players.filter(p=>p.draft_round==="1").length);
  $("lastVerified").textContent=date(registry.last_verified);$("lastVerified").dateTime=registry.last_verified;
  render();
 }catch(e){$("cards").innerHTML='<div class="alumni-empty">Unable to load the verified MLB directory: '+esc(e.message)+'</div>'}
}
$("search").addEventListener("input",render);$("sort").addEventListener("change",render);
if(document.readyState==="loading")document.addEventListener("DOMContentLoaded",start,{once:true});else start();
})();
