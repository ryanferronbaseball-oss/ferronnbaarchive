(()=>{
"use strict";
const A=window.MLBArchive;
const esc=A?.esc||((v)=>String(v??"").replace(/[&<>"']/g,c=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[c])));
const num=(v)=>v==null?"—":Number(v).toLocaleString("en-US",{maximumFractionDigits:1});
const date=(v)=>A?.date?.(v)||v;
const gameLink=(g)=>"./game.html?id="+encodeURIComponent(g.attendance_id);
const playerLink=(p)=>"./player.html?id="+encodeURIComponent(p.id);
const label=(g)=>g.away+" @ "+g.home;
let cache;
function getData(){
 if(!cache) cache=fetch("./data/statcast_summary.json",{cache:"no-store"})
 .then(r=>{if(!r.ok)throw Error("The verified Statcast summary has not been staged yet (HTTP "+r.status+").");return r.json()})
 .then(d=>{if(d.meta?.status!=="PASS"||d.games?.length!==77||d.meta?.imported_pitch_events!==22844)throw Error("The Statcast audit manifest is incomplete.");return d})
 .catch(err=>{cache=null;throw err});
 return cache;
}
function unit(v,u){return v==null?"—":num(v)+" "+u}
function summaryCard(k,v){return '<div class="sc-metric"><strong>'+esc(v)+'</strong><small>'+esc(k)+'</small></div>'}
function empty(message){return '<div class="sc-empty">'+esc(message)+'</div>'}
function playerName(p){return '<a href="'+playerLink(p)+'">'+esc(p.name||"Player #"+p.id)+'</a>'}
function gameName(g){return '<a href="'+gameLink(g)+'">'+esc(date(g.date))+' · '+esc(label(g))+'</a>'}
function table(head,rows){return '<div class="sc-table"><table><thead><tr>'+head.map(h=>'<th>'+esc(h)+'</th>').join("")+'</tr></thead><tbody>'+rows.join("")+'</tbody></table></div>'}
function topRows(d,kind,max=10){
 const heads=kind==="fastest"?["#","Pitcher","Velocity","Game","Pitch type"]:["#","Batter",kind==="longest"?"HR distance":"Exit velocity","Game",kind==="longest"?"Launch angle":"Result"];
 const rows=d.leaders[kind].slice(0,max).map((e,i)=>{
 const g=d.games.find(x=>x.pk===e.pk),u=kind==="longest"?"ft":"mph";
 return '<tr><td>'+(i+1)+'</td><td>'+playerName(e)+'</td><td><strong>'+esc(unit(e.value,u))+'</strong></td><td>'+(g?gameName(g):esc(e.date))+'</td><td>'+esc(kind==="fastest"?e.type:kind==="longest"?unit(e.launch,"°"):String(e.result).replaceAll("_"," "))+'</td></tr>';
 });
 return table(heads,rows);
}
function tiles(items){return '<div class="sc-metrics">'+items.map(([k,v])=>summaryCard(k,v)).join("")+'</div>'}
function renderSite(){
 const app=document.getElementById("app"),nav=document.getElementById("navigation");
 if(nav&&A?.nav)nav.innerHTML=A.nav("statcast");
 app.innerHTML='<div class="eyebrow">MLB · Statcast measurements</div><h1>Your baseball history,<br>down to the pitch.</h1>'
 +'<p class="lead">Verified pitch speeds, exit velocities, contact quality and home-run distances from the MLB games you attended. The 2003–2014 traditional box scores remain available separately.</p>'
 +'<div id="sc-status" class="sc-status">Loading source-verified Statcast records…</div><div id="sc-main" hidden>'
 +'<div id="sc-metrics"></div><div class="section-heading"><h2>Signature moments</h2><a class="action-link secondary" href="./records.html">Your record book ↗</a></div><div id="sc-highlights" class="sc-highlights"></div>'
 +'<div class="sc-tabs" role="tablist" aria-label="Statcast views"><button role="tab" data-sc-tab="records" aria-selected="true">Signature Performances</button><button role="tab" data-sc-tab="games" aria-selected="false">Games</button><button role="tab" data-sc-tab="players" aria-selected="false">Players</button><button role="tab" data-sc-tab="methods" aria-selected="false">Data & Methods</button></div>'
 +'<section id="sc-panel-records" class="sc-panel"><h2>Individual event records</h2><p class="mlb-note">Each ranked row is an actual event, so one player can appear more than once.</p><div class="sc-switch" id="sc-record-toggle"><button data-kind="hardest" aria-selected="true">Hardest-hit balls</button><button data-kind="fastest" aria-selected="false">Fastest pitches</button><button data-kind="longest" aria-selected="false">Longest home runs</button></div><div id="sc-record-table"></div></section>'
 +'<section id="sc-panel-games" class="sc-panel" hidden><h2>Game-by-game Statcast</h2><div class="sc-filters"><label for="sc-year">Season</label><select id="sc-year"></select><input type="search" id="sc-game-search" placeholder="Search date, teams or MLB game ID…" aria-label="Search Statcast games"></div><div id="sc-games-table"></div><div id="sc-game-detail" class="panel" hidden></div></section>'
 +'<section id="sc-panel-players" class="sc-panel" hidden><h2>Player Statcast leaderboards</h2><div class="sc-switch" id="sc-role-toggle"><button data-role="bats" aria-selected="true">Hitters</button><button data-role="pits" aria-selected="false">Pitchers</button></div><div class="sc-filters"><label for="sc-sort">Rank by</label><select id="sc-sort"></select><input id="sc-player-search" type="search" placeholder="Search player name…" aria-label="Search players"></div><p id="sc-player-note" class="mlb-note"></p><div id="sc-players-table"></div></section>'
 +'<section id="sc-panel-methods" class="sc-panel" hidden><h2>Scope & methodology</h2><div class="panel"><p>Modern Statcast begins in 2015. All 77 attended games dated 2015–2026 were independently checked against Baseball Savant by game, at-bat, pitch identity and selected measurement fields. The 54 earlier games retain their official traditional statistics without fabricated tracking fields.</p><p>Exit velocity and hard-hit percentage consider only balls with a measured exit velocity. Hard hit means at least 95 mph; rate rankings require at least five measured balls. Average pitch speed uses measured pitches and requires 15 pitches. Fastest-pitch lists are not adjusted for pitch type. Home-run distances use Statcast projected distance when available, not estimated values.</p><p>These are witnessed-game statistics, not full-season or career totals. Missing sensor fields display as unavailable, never as zero.</p></div></section></div>';
 getData().then(d=>{
 const $=id=>document.getElementById(id);
 $("sc-main").hidden=false;$("sc-status").hidden=true;
 $("sc-metrics").innerHTML=tiles([["Statcast-era games",d.games.length],["Verified pitch events",num(d.meta.imported_pitch_events)],["Measured exit velocities",num(d.games.reduce((a,g)=>a+g.evCount,0))],["Recorded home runs",num(d.games.reduce((a,g)=>a+g.homers,0))]]);
 $("sc-highlights").innerHTML=[["Hardest-hit ball","hardest","mph"],["Fastest pitch","fastest","mph"],["Longest home run","longest","ft"]].map(([title,key,u])=>{
  const e=d.leaders[key][0],g=d.games.find(x=>x.pk===e.pk);
  return '<article class="sc-highlight"><small>'+title+'</small><strong>'+esc(unit(e.value,u))+'</strong><h3>'+playerName(e)+'</h3><p>'+ (g?gameName(g):esc(e.date))+'</p></article>';
 }).join("");
 const changeTab=tab=>{document.querySelectorAll("[data-sc-tab]").forEach(b=>b.setAttribute("aria-selected",String(b.dataset.scTab===tab)));
 ["records","games","players","methods"].forEach(x=>$("sc-panel-"+x).hidden=x!==tab)};
 document.querySelectorAll("[data-sc-tab]").forEach(b=>b.addEventListener("click",()=>changeTab(b.dataset.scTab)));
 const showRecords=kind=>{document.querySelectorAll("#sc-record-toggle button").forEach(b=>b.setAttribute("aria-selected",String(b.dataset.kind===kind)));$("sc-record-table").innerHTML=topRows(d,kind,100)};
 document.querySelectorAll("#sc-record-toggle button").forEach(b=>b.addEventListener("click",()=>showRecords(b.dataset.kind)));showRecords("hardest");
 $("sc-year").innerHTML='<option value="">All seasons</option>'+[...new Set(d.games.map(g=>g.date.slice(0,4)))].sort().reverse().map(x=>'<option value="'+x+'">'+x+'</option>').join("");
 function drawGames(){
  const year=$("sc-year").value,q=$("sc-game-search").value.trim().toLowerCase();
  const list=d.games.filter(g=>(!year||g.date.startsWith(year))&&[g.date,g.away,g.home,g.pk].some(z=>String(z).toLowerCase().includes(q)));
  $("sc-games-table").innerHTML=table(["Date & matchup","Pitch events","Exit velo events","Max EV","Fastest pitch","HR","Detail"],list.map(g=>'<tr><td>'+gameName(g)+'</td><td>'+g.count+'</td><td>'+g.evCount+'</td><td>'+esc(unit(g.maxEV,"mph"))+'</td><td>'+esc(unit(g.maxPitch,"mph"))+'</td><td>'+g.homers+'</td><td><button class="sc-detail-button" data-sc-game="'+g.pk+'">Review</button></td></tr>'));
  $("sc-games-table").querySelectorAll("[data-sc-game]").forEach(b=>b.addEventListener("click",()=>{const g=d.games.find(x=>String(x.pk)===b.dataset.scGame);
    $("sc-game-detail").hidden=false;$("sc-game-detail").innerHTML='<h3>'+gameName(g)+'</h3>'+tiles([["Tracked pitch events",g.count],["Pitch speed measurements",g.pitchCount],["Exit velocity measurements",g.evCount],["Hardest contact",unit(g.maxEV,"mph")],["Fastest pitch",unit(g.maxPitch,"mph")],["Longest measured HR",unit(g.longHR,"ft")]])+'<p class="mlb-note">Hardest contact: '+esc(d.bats.find(x=>x.id===g.maxEVPlayer)?.name||"—")+' · Fastest pitch: '+esc(d.pits.find(x=>x.id===g.maxPitchPlayer)?.name||"—")+'.</p><a class="action-link" href="'+gameLink(g)+'">Full box score ↗</a>';
    $("sc-game-detail").scrollIntoView({block:"nearest"});
  }));
 }
 $("sc-year").addEventListener("change",drawGames);$("sc-game-search").addEventListener("input",drawGames);drawGames();
 let role="bats";
 function options(){
  $("sc-sort").innerHTML=role==="bats"?'<option value="maxEV">Maximum exit velocity</option><option value="avgEV">Average exit velocity</option><option value="hardHitPct">Hard-hit percentage</option><option value="bip">Measured batted balls</option><option value="hr">Home runs</option><option value="longHR">Longest HR</option>':'<option value="maxSpeed">Maximum pitch velocity</option><option value="avgSpeed">Average pitch velocity</option><option value="pitchCount">Tracked pitches</option>';
  $("sc-player-note").textContent=role==="bats"?"Rate rankings require at least five measured batted balls. All metrics are from games you attended only.":"Average velocity rankings require at least fifteen tracked pitches; pitch mix is not adjusted.";
 }
 function drawPlayers(){
  const k=$("sc-sort").value,q=$("sc-player-search").value.trim().toLowerCase();
  const list=d[role].filter(x=>x.name.toLowerCase().includes(q) && !(role==="bats"&&["avgEV","hardHitPct"].includes(k)&&x.bip<5)&&!(role==="pits"&&k==="avgSpeed"&&x.pitchCount<15)).sort((a,b)=>(b[k]??-1)-(a[k]??-1)||a.name.localeCompare(b.name)).slice(0,120);
  $("sc-players-table").innerHTML=role==="bats"?table(["Player","Games","Tracked balls","Avg EV","Max EV","Hard-hit %","HR","Longest HR"],list.map(p=>'<tr><td>'+playerName(p)+'</td><td>'+p.games+'</td><td>'+p.bip+'</td><td>'+esc(unit(p.avgEV,"mph"))+'</td><td><strong>'+esc(unit(p.maxEV,"mph"))+'</strong></td><td>'+esc(unit(p.hardHitPct,"%"))+'</td><td>'+p.hr+'</td><td>'+esc(unit(p.longHR,"ft"))+'</td></tr>')):table(["Player","Games","Tracked pitches","Average speed","Fastest"],list.map(p=>'<tr><td>'+playerName(p)+'</td><td>'+p.games+'</td><td>'+p.pitchCount+'</td><td>'+esc(unit(p.avgSpeed,"mph"))+'</td><td><strong>'+esc(unit(p.maxSpeed,"mph"))+'</strong></td></tr>'));
 }
 document.querySelectorAll("#sc-role-toggle button").forEach(b=>b.addEventListener("click",()=>{role=b.dataset.role;document.querySelectorAll("#sc-role-toggle button").forEach(x=>x.setAttribute("aria-selected",String(x===b)));options();drawPlayers()}));
 $("sc-sort").addEventListener("change",drawPlayers);$("sc-player-search").addEventListener("input",drawPlayers);options();drawPlayers();
 }).catch(err=>{document.getElementById("sc-status").innerHTML=empty(err.message+" Your existing MLB statistics are unaffected.")});
}
function renderGame(g,target){
 if(!target)return;
 if(Number(g.date?.slice(0,4))<2015){target.innerHTML='<section class="panel sc-panel-inline"><h2>Statcast</h2><p class="mlb-note">This game predates Statcast (2015). Traditional box scores remain available above and below.</p></section>';return}
 target.innerHTML='<section class="panel sc-panel-inline"><h2>Statcast game summary</h2><p class="mlb-note">Loading verified measurements…</p></section>';
 getData().then(d=>{
  const s=d.games.find(x=>x.pk===Number(g.game_pk));
  if(!s){target.innerHTML=empty("No verified Statcast record available for this game.");return}
  target.innerHTML='<section class="panel sc-panel-inline"><h2>Statcast game summary</h2>'+tiles([["Tracked pitches",s.count],["Batted balls with EV",s.evCount],["Hardest-hit ball",unit(s.maxEV,"mph")],["Fastest pitch",unit(s.maxPitch,"mph")],["Measured longest HR",unit(s.longHR,"ft")]])+'<p class="mlb-note">Measurements from your attended game, cross-checked against Baseball Savant. The pitching and batting box score remains official MLB StatsAPI data.</p><a href="./statcast.html" class="action-link secondary">Explore Statcast rankings ↗</a></section>';
 }).catch(err=>target.innerHTML=empty("Statcast temporarily unavailable; official box score remains intact."));
}
function renderPlayer(p,target){
 if(!target)return;
 target.innerHTML='<section class="panel sc-panel-inline"><h2>Statcast from games you attended</h2><p class="mlb-note">Loading tracked performances…</p></section>';
 getData().then(d=>{
  const id=String(p.player_id),b=d.bats.find(x=>x.id===id),pit=d.pits.find(x=>x.id===id);
  if(!b&&!pit){target.innerHTML='<section class="panel sc-panel-inline"><h2>Statcast from games you attended</h2><p class="mlb-note">No measured Statcast pitches or batted balls for this player in your attended games. Older games before 2015 are not measured.</p></section>';return}
  target.innerHTML='<section class="panel sc-panel-inline"><h2>Statcast from games you attended</h2>'
  +(b?'<h3>Hitting measurements</h3>'+tiles([["Games with tracked contact",b.games],["Measured batted balls",b.bip],["Average exit velocity",unit(b.avgEV,"mph")],["Maximum exit velocity",unit(b.maxEV,"mph")],["Hard-hit rate",unit(b.hardHitPct,"%")],["Longest measured HR",unit(b.longHR,"ft")]]):"")
  +(pit?'<h3>Pitching measurements</h3>'+tiles([["Games with tracked pitches",pit.games],["Pitches measured",pit.pitchCount],["Average pitch speed",unit(pit.avgSpeed,"mph")],["Maximum pitch speed",unit(pit.maxSpeed,"mph")]]):"")
  +'<p class="mlb-note">Statcast coverage is 2015 onward only. All averages include measured events only; these are not full-career statistics.</p><a href="./statcast.html" class="action-link secondary">See all Statcast leaderboards ↗</a></section>';
 }).catch(err=>target.innerHTML=empty("Statcast is temporarily unavailable. Traditional player stats are unchanged."));
}
function renderRecords(target){
 if(!target)return;
 target.innerHTML='<section class="panel sc-panel-inline"><h2>Statcast signature performances</h2><p class="mlb-note">Loading verified individual events…</p></section>';
 getData().then(d=>{
  target.innerHTML='<section class="panel sc-panel-inline"><h2>Statcast signature performances</h2><p class="mlb-note">Fastest pitches, hardest-hit balls and longest measured home runs. Repeated appearances by the same player are preserved.</p>'
  +'<div class="sc-highlights">'+[["Hardest-hit ball","hardest","mph"],["Fastest pitch","fastest","mph"],["Longest home run","longest","ft"]].map(([title,k,u])=>{
    const e=d.leaders[k][0],g=d.games.find(x=>x.pk===e.pk);
    return '<div class="sc-highlight"><small>'+esc(title)+'</small><strong>'+esc(unit(e.value,u))+'</strong><h3>'+playerName(e)+'</h3><p>'+(g?gameName(g):esc(e.date))+'</p></div>';
   }).join("")+'</div><p class="mlb-note"><a href="./statcast.html">See the top 100 events in every Statcast category ↗</a></p></section>';
 }).catch(err=>target.innerHTML=empty("Statcast measurements unavailable right now; traditional records remain intact."));
}
window.MLBStatcast={renderSite,renderGame,renderPlayer,renderRecords};
if(document.body.dataset.page==="statcast"){
 if(document.readyState==="loading")document.addEventListener("DOMContentLoaded",renderSite,{once:true});else renderSite();
}
})();