/* MiLB to MLB directory mirrors the College Baseball pathway page.
   Only attendance-specific MiLB stats; MLB stats and MiLB stats never combine. */
(()=>{"use strict";
const $=id=>document.getElementById(id);
const esc=v=>String(v??"").replace(/[&<>"']/g,c=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[c]));
const num=v=>v===null||v===undefined||v===""?0:Number.isFinite(Number(v))?Number(v):0;
const fmt=n=>num(n).toLocaleString("en-US");
const date=v=>v?new Date(String(v)+"T12:00:00").toLocaleDateString("en-US",{month:"short",day:"numeric",year:"numeric"}):"Not confirmed";
const toOuts=v=>{const m=/^(\d+)(?:\.([012]))?$/.exec(String(v??""));return m?Number(m[1])*3+Number(m[2]||0):null;};
const ip=outs=>Math.floor(num(outs)/3)+"."+(num(outs)%3);
const playerUrl=id=>"./player.html?id="+encodeURIComponent(id);
const gameUrl=id=>"./game.html?id="+encodeURIComponent(id);
let players=[];
function aggregate(games,rows,registry,links){
 if(!registry||!Array.isArray(registry.players))throw Error("Missing verified MiLB-to-MLB roster");
 const gameMap=new Map(games.filter(g=>g.source_game_id!=null&&g.box_score_status==="verified").map(g=>[String(g.id),g]));
 const byId=new Map();
 for(const r of rows){
  if(!gameMap.has(String(r.game_id)))continue;
  const id=String(r.player_id);
  if(!byId.has(id))byId.set(id,{rows:[],teams:new Set()});
  byId.get(id).rows.push(r);
  if(r.team)byId.get(id).teams.add(r.team);
 }
 const verifiedIds=new Set(links.filter(x=>x.verified===true).map(x=>String(x.milb_id)));
 const seen=new Set();
 return registry.players.map(record=>{
  const id=String(record.milb_player_id);
  if(!record.mlb_debut||!record.name||String(record.mlb_player_id)!==id||!verifiedIds.has(id))
   throw Error("Invalid official MiLB-to-MLB registry identity "+id);
  if(seen.has(id))throw Error("Duplicate MiLB alumni identity "+id);
  seen.add(id);
  const member=byId.get(id);if(!member)throw Error("MiLB alumni not found in attended game box scores: "+record.name);
  const perGame=new Map();
  for(const r of member.rows){
   const g=gameMap.get(String(r.game_id));
   if(!g)throw Error("Missing attended MiLB game: "+r.game_id);
   let item=perGame.get(g.id);
   if(!item){item={id:g.id,date:g.date,team:r.team,hits:0,homeRuns:0,rbi:0,outs:0,strikeouts:0,batting:false,pitching:false};perGame.set(g.id,item);}
   if(r.batting){item.batting=true;item.hits+=num(r.batting.h);item.homeRuns+=num(r.batting.hr);item.rbi+=num(r.batting.rbi);}
   if(r.pitching){
    const outs=toOuts(r.pitching.ip);
    if(outs!==null){item.pitching=true;item.outs+=outs;item.strikeouts+=num(r.pitching.so);}
   }
  }
  const seenGames=[...perGame.values()].sort((a,b)=>a.date.localeCompare(b.date)||String(a.id).localeCompare(String(b.id)));
  if(!seenGames.length)throw Error("MLB alumni has no attended MiLB games: "+record.name);
  const pitching=seenGames.filter(x=>x.pitching),batting=seenGames.filter(x=>x.batting);
  const mostlyPitching=pitching.length>batting.length;
  const top=(mostlyPitching?pitching:batting).slice().sort((a,b)=>mostlyPitching
   ?b.strikeouts-a.strikeouts||b.outs-a.outs
   :b.hits-a.hits||b.homeRuns-a.homeRuns||b.rbi-a.rbi)[0]||seenGames[0];
  return {...record,teams:[...member.teams].sort(),games:seenGames,
   hits:seenGames.reduce((t,g)=>t+g.hits,0),strikeouts:seenGames.reduce((t,g)=>t+g.strikeouts,0),
   top,topPitching:mostlyPitching};
 });
}
function compareDraftClass(a,b,newestFirst){
 const aYear=a.draft_pick==null?0:Number(a.draft_year)||0;
 const bYear=b.draft_pick==null?0:Number(b.draft_year)||0;
 if(!aYear)return bYear?1:a.name.localeCompare(b.name);
 if(!bYear)return -1;
 return (newestFirst?bYear-aYear:aYear-bYear)||(a.draft_pick-b.draft_pick)||a.name.localeCompare(b.name);
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
  :(a.draft_pick??99999)-(b.draft_pick??99999)||a.name.localeCompare(b.name));
 if(!matches.length){$("cards").innerHTML='<div class="alumni-empty">'+(query?"No players match this search.":"No confirmed MLB alumni found yet.")+'</div>';return;}
 $("cards").innerHTML=matches.map(p=>{
  const draft=p.draft_pick!=null?
   p.draft_year+" · Round "+(p.draft_round||"—")+" · Pick #"+p.draft_pick+" · "+(p.draft_team||"Team unavailable"):
   p.draft_year?"Draft "+p.draft_year+" · Selection details pending verification":"Draft record pending verification / undrafted";
  const top=p.topPitching?ip(p.top.outs)+" IP · "+fmt(p.top.strikeouts)+" K":
   fmt(p.top.hits)+" H · "+fmt(p.top.homeRuns)+" HR · "+fmt(p.top.rbi)+" RBI";
  const attended=p.games.map(g=>'<a href="'+gameUrl(g.id)+'">'+esc(date(g.date))+'</a> ('+esc(g.team)+', '
   +(g.pitching&&!g.batting?ip(g.outs)+' IP, '+fmt(g.strikeouts)+' K':fmt(g.hits)+' H, '+fmt(g.rbi)+' RBI')+')').join(" · ");
  const initials=p.name.trim().split(/\s+/).slice(0,2).map(w=>w.charAt(0)).join("");
  return '<article class="alumni-player">'
   +'<div class="alumni-head"><div class="alumni-identity"><div class="alumni-portrait">'+esc(initials)
   +'<img src="https://img.mlbstatic.com/mlb-photos/image/upload/w_213,q_85/v1/people/'+encodeURIComponent(p.mlb_player_id)+'/headshot/67/current" alt="" loading="lazy" onerror="this.style.display=\'none\'"></div>'
   +'<div><a class="alumni-name" href="'+playerUrl(p.milb_player_id)+'">'+esc(p.name)+'</a><div class="alumni-school">'+p.teams.map(esc).join(" / ")+'</div></div></div>'
   +'<span class="alumni-pill">MLB alumnus</span>'
   +(p.mlb_seen?'<div class="alumni-profile-flag">Also witnessed in MLB</div>':"")+'</div>'
   +'<div class="alumni-line"><div><strong>'+fmt(p.games.length)+'</strong><small>Games witnessed</small></div>'
   +'<div><strong>'+fmt(p.hits)+'</strong><small>MiLB hits witnessed</small></div>'
   +'<div><strong>'+fmt(p.strikeouts)+'</strong><small>Pitcher K witnessed</small></div></div>'
   +'<div class="alumni-info"><b>When you watched:</b> '+esc(date(p.games[0].date))+' — '+esc(date(p.games.at(-1).date))+'</div>'
   +'<div class="alumni-info"><b>MLB Draft:</b> '+esc(draft)+'</div>'
   +'<div class="alumni-info"><b>MLB debut:</b> '+esc(date(p.mlb_debut))+'</div>'
   +'<div class="alumni-info"><b>Top attended performance:</b> '+esc(top)+'</div>'
   +'<div class="alumni-dates"><b>All attended appearances:</b> '+attended+'</div>'
   +'<div class="alumni-links"><a href="'+playerUrl(p.milb_player_id)+'">MiLB profile ↗</a>'
   +'<a href="https://www.mlb.com/player/'+encodeURIComponent(p.mlb_player_id)+'" target="_blank" rel="noopener noreferrer">MLB career source ↗</a>'
   +(p.mlb_seen?'<a href="../mlb/player.html?id='+encodeURIComponent(p.mlb_player_id)+'">My MLB profile ↗</a>':"")
   +'</div></article>';
 }).join("");
}
async function start(){
 try{
  const get=async file=>{const r=await fetch("./data/"+file+".json",{cache:"no-store"});if(!r.ok)throw Error("Missing "+file+" data");return r.json();};
  const [games,rows,registry,links]=await Promise.all(["games","player_stats","mlb_alumni_seed","player_links"].map(get));
  if(!Array.isArray(games)||!Array.isArray(rows)||!Array.isArray(links))throw Error("Invalid MiLB attendance data");
  players=aggregate(games,rows,registry,links);
  $("mlbCount").textContent=fmt(players.length);
  $("seenCount").textContent=fmt(new Set(players.flatMap(p=>p.games.map(g=>String(g.id)))).size);
  $("firstCount").textContent=fmt(players.filter(p=>p.draft_round==="1").length);
  $("lastVerified").textContent=date(registry.last_verified);
  $("lastVerified").dateTime=registry.last_verified;
  render();
 }catch(e){$("cards").innerHTML='<div class="alumni-empty">Unable to load verified MiLB-to-MLB alumni directory: '+esc(e.message)+'</div>';}
}
document.addEventListener("DOMContentLoaded",()=>{
 $("search").addEventListener("input",render);
 $("sort").addEventListener("change",render);
 start();
});
})();
