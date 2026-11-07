/* MiLB Overview — MLB overview layout parity, MiLB-only datasets. */
(()=>{"use strict";
const $=id=>document.getElementById(id);
const esc=value=>String(value??"").replace(/[&<>"']/g,c=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[c]));
const date=value=>value?new Date(String(value)+"T12:00:00").toLocaleDateString("en-US",{month:"short",day:"numeric",year:"numeric"}):"Date pending";
const format=n=>Number(n||0).toLocaleString("en-US");
const encode=v=>encodeURIComponent(String(v));
const gameUrl=g=>"./game.html?id="+encode(g.id);
const playerUrl=r=>"./player.html?id="+encode(r.player_id);
const verified=g=>g.box_score_status==="verified"&&g.source_game_id!=null;
const scores=g=>g.away_score!=null&&g.home_score!=null?g.away_score+" – "+g.home_score:"Score pending";
const count=values=>{
 const valuesCount=new Map();
 for(const v of values){if(v!==null&&v!==undefined&&v!=="")valuesCount.set(v,(valuesCount.get(v)||0)+1);}
 return [...valuesCount.entries()].sort((a,b)=>b[1]-a[1]||String(a[0]).localeCompare(String(b[0])));
};
function bars(entries){
 if(!entries.length)return '<div class="empty">No verified attendance records yet.</div>';
 const max=Math.max(1,...entries.map(x=>x[1]));
 return entries.map(([name,n])=>'<div class="mlb-bar"><span>'+esc(name)+'</span><div class="mlb-track"><div class="mlb-fill" style="width:'+((n/max)*100).toFixed(2)+'%"></div></div><strong>'+format(n)+'</strong></div>').join("");
}
function gameCard(g){
 return '<article class="game-card"><div class="game-date">'+date(g.date)+' · '+esc(g.venue||"Ballpark pending")+'</div>'
 +'<h3>'+esc(g.away_team)+' @ '+esc(g.home_team)+'</h3>'
 +'<div class="game-score">'+esc(scores(g))+'</div>'
 +'<div class="caption">'+(verified(g)?"Verified official game #"+esc(g.source_game_id):"Official box score pending")+' · '+esc(g.level||"Level pending")+'</div>'
 +'<a class="action-link" href="'+gameUrl(g)+'">View game ↗</a></article>';
}
const signatureTypes=[
 ["Hits in a game","batting","h","H"],
 ["Home runs in a game","batting","hr","HR"],
 ["Strikeouts in a game","pitching","so","SO"]
];
function signature(rows,games){
 const indexed=new Map(games.map(g=>[String(g.id),g]));
 return signatureTypes.map(([title,category,key,suffix])=>{
  const top=rows.filter(r=>r[category]&&Number.isFinite(Number(r[category][key]))&&Number(r[category][key])>0&&indexed.has(String(r.game_id))&&verified(indexed.get(String(r.game_id))))
   .sort((a,b)=>Number(b[category][key])-Number(a[category][key])||String(a.date).localeCompare(String(b.date))||String(a.name).localeCompare(String(b.name)))[0];
  if(!top)return '<article class="mlb-record"><small>'+esc(title)+'</small><strong>—</strong><p>Awaiting official individual box scores.</p></article>';
  const initials=(top.name||"?").trim().split(/\s+/).map(s=>s[0]).slice(0,2).join("").toUpperCase();
  return '<article class="mlb-record"><small>'+esc(title)+'</small><div class="mlb-feature">'
   +'<div class="mlb-avatar">'+esc(initials)+'</div><div><strong>'+esc(top[category][key])+' '+suffix+'</strong>'
   +'<div class="person"><a href="'+playerUrl(top)+'">'+esc(top.name)+'</a></div>'
   +'<p>'+date(top.date)+' · '+esc(top.team)+'</p></div></div>'
   +'<a href="'+gameUrl(indexed.get(String(top.game_id)))+'">View performance ↗</a></article>';
 }).join("");
}
function table(games){
 if(!games.length)return '<div class="empty">No attended games match those filters.</div>';
 const rows=games.map(g=>'<tr>'
  +'<td><a href="'+gameUrl(g)+'">'+date(g.date)+'</a></td>'
  +'<td>'+esc(g.away_team)+' @ '+esc(g.home_team)+'</td>'
  +'<td>'+esc(g.venue||"—")+'</td>'
  +'<td>'+esc(scores(g))+'</td>'
  +'<td><span class="mlb-pill '+(verified(g)?"verified":"pending")+'">'+(verified(g)?"Matched":"Pending")+'</span></td>'
  +'<td><a href="'+gameUrl(g)+'">View →</a></td></tr>').join("");
 return '<div class="table-wrap"><table class="mlb-sticky"><thead><tr><th>Date</th><th>Matchup</th><th>Ballpark</th><th>Final</th><th>Status</th><th>Game</th></tr></thead><tbody>'+rows+'</tbody></table></div>';
}
function filters(games){
 const years=[...new Set(games.map(g=>String(g.date||"").slice(0,4)).filter(Boolean))].sort().reverse();
 const teams=[...new Set(games.flatMap(g=>[g.away_team,g.home_team]).filter(Boolean))].sort();
 return '<div class="mlb-filters">'
 +'<label for="search">Find a game<input id="search" type="search" placeholder="Team, venue or year"></label>'
 +'<label for="yearFilter">Season<select id="yearFilter"><option value="">All seasons</option>'+years.map(y=>'<option value="'+esc(y)+'">'+esc(y)+'</option>').join("")+'</select></label>'
 +'<label for="teamFilter">Team<select id="teamFilter"><option value="">All teams</option>'+teams.map(t=>'<option value="'+esc(t)+'">'+esc(t)+'</option>').join("")+'</select></label>'
 +'<label for="sort">Order<select id="sort"><option value="desc">Newest first</option><option value="asc">Oldest first</option></select></label></div>'
 +'<p id="showing" class="mlb-note" aria-live="polite"></p><div id="history"></div>';
}
function history(games){
 const draw=()=>{
  const text=$("search").value.trim().toLowerCase(),year=$("yearFilter").value,team=$("teamFilter").value,order=$("sort").value;
  const found=games.filter(g=>(!year||String(g.date).startsWith(year))&&(!team||g.away_team===team||g.home_team===team)
   &&[g.date,g.away_team,g.home_team,g.venue,g.city,g.level].join(" ").toLowerCase().includes(text))
   .sort((a,b)=>(order==="desc"?String(b.date).localeCompare(String(a.date)):String(a.date).localeCompare(String(b.date)))||String(a.id).localeCompare(String(b.id)));
  $("showing").textContent="Showing "+found.length+" of "+games.length+" attended games.";
  $("history").innerHTML=table(found);
 };
 ["search","yearFilter","teamFilter","sort"].forEach(id=>$(id).addEventListener("input",draw));
 draw();
}
function render(games,rows){
 const official=games.filter(verified);
 const uniquePlayers=new Set(rows.filter(r=>r.player_id!=null).map(r=>String(r.player_id)));
 const seasons=new Set(games.map(g=>String(g.date||"").slice(0,4)).filter(Boolean));
 const latest=games.slice().sort((a,b)=>String(b.date).localeCompare(String(a.date))||String(a.id).localeCompare(String(b.id)));
 const metrics=[["Games attended",games.length],["Officially matched",official.length],["Players imported",uniquePlayers.size],["Seasons represented",seasons.size]];
 $("app").innerHTML='<div class="eyebrow">Minor League Baseball · Personal attendance</div>'
  +'<h1>Your MiLB history.</h1><p class="lead">A personal archive of the minor-league games you witnessed, from Single-A to Triple-A. Explore official box scores, individual player game logs, personal leaderboards, and record-setting performances from those games.</p>'
  +'<div class="metrics">'+metrics.map(([name,value])=>'<div class="metric"><strong>'+format(value)+'</strong><small>'+esc(name)+'</small></div>').join("")+'</div>'
  +'<div class="section-heading"><h2>Recently attended</h2><a class="action-link secondary" href="./game.html">All game box scores ↗</a></div>'
  +(latest.length?'<div class="game-grid">'+latest.slice(0,3).map(gameCard).join("")+'</div>':'<div class="empty">No verified MiLB games imported yet.</div>')
  +'<div class="section-heading"><h2>Signature Performances</h2><a class="action-link secondary" href="./records.html">View Records ↗</a></div>'
  +'<p class="mlb-note">Your strongest verified single-game MiLB performances—one attended game per record, not complete minor-league career statistics.</p>'
  +'<div class="mlb-feature-grid">'+signature(rows,games)+'</div>'
  +'<div class="mlb-charts"><section class="panel"><h2>Most Watched Teams</h2>'+bars(count(games.flatMap(g=>[g.away_team,g.home_team])).slice(0,9))+'</section>'
  +'<section class="panel"><h2>Attendance by Year</h2>'+bars(count(games.map(g=>String(g.date).slice(0,4))).sort((a,b)=>String(a[0]).localeCompare(String(b[0]))))+'</section></div>'
  +'<section class="panel"><h2>Ballpark history</h2>'+bars(count(games.map(g=>g.venue)).slice(0,10))+'</section>'
  +'<section class="panel" id="gameHistorySection"><h2>My Game History</h2>'
  +'<p class="mlb-note">All '+games.length+' MiLB games in your attendance archive. Official game IDs and box-score coverage are identified individually. MiLB and MLB statistics remain independent.</p>'
  +filters(games)+'</section>';
 history(games);
}
document.addEventListener("DOMContentLoaded",async()=>{
 try{
  const fetchJSON=async name=>{const response=await fetch("./data/"+name+".json",{cache:"no-store"});if(!response.ok)throw Error(name+" unavailable");return response.json();};
  const [games,rows]=await Promise.all(["games","player_stats"].map(fetchJSON));
  if(!Array.isArray(games)||!Array.isArray(rows))throw Error("Invalid MiLB attendance data");
  render(games,rows);
 }catch(error){$("app").innerHTML='<div class="empty">Unable to load MiLB overview: '+esc(error.message)+'</div>';}
});
})();
