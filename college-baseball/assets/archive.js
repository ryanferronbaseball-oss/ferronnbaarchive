/* College Baseball Courtside Archive. Source-scoped data; no mixing MLB career lines. */
(()=>{
"use strict";
const $=id=>document.getElementById(id);
const esc=v=>String(v??"").replace(/[&<>"']/g,c=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[c]));
const date=v=>{if(!v)return "Date not recorded";const d=new Date(v+"T12:00:00");return Number.isNaN(+d)?v:d.toLocaleDateString("en-US",{month:"short",day:"numeric",year:"numeric"})};
const fmt=n=>n==null?"—":Number(n).toLocaleString("en-US",{maximumFractionDigits:2});
const stat=v=>v===null||v===undefined||v===""?null:Number.isFinite(Number(v))?Number(v):null;
const link=(s)=>{try{let u=new URL(s);return ["https:","http:"].includes(u.protocol)?u.href:null}catch{return null}};
const gameUrl=g=>"./game.html?id="+encodeURIComponent(g.id);
const playerUrl=p=>"./player.html?id="+encodeURIComponent(p.player_id);
const unique=a=>[...new Set(a.filter(x=>x!=null&&x!==""))];
function nav(active){
 const links=[["index.html","Overview","home"],["game.html","Games","games"],["stats.html","Players","players"],["records.html","Records","records"]];
 return '<header class="archive-header"><a class="archive-logo" href="./index.html">COURTSIDE ARCHIVE<small>EVERY GAME HAS A STORY · COLLEGE BASEBALL</small></a>'
 +'<nav class="archive-nav" aria-label="College Baseball archive navigation">'+links.map(([href,label,name])=>'<a href="./'+href+'"'+(active===name||active==="player"&&name==="players"?' aria-current="page"':'')+'>'+label+'</a>').join("")+'</nav>'
 +'<a class="back-link" href="../index.html">All archives ↗</a></header>';
}
async function json(name,fallback){const r=await fetch("./data/"+name,{cache:"no-store"});if(!r.ok)throw Error("Missing "+name+" ("+r.status+")");return r.json()}
async function load(){
 const [games,rows,report,crosswalk]=await Promise.all([json("games.json"),json("player_stats.json"),json("import_report.json"),json("mlb_crosswalk.json")]);
 if(!Array.isArray(games)||!Array.isArray(rows)||!Array.isArray(crosswalk))throw Error("Unexpected college baseball data structure");
 const gameMap=new Map(games.map(g=>[g.id,g]));
 if(gameMap.size!==games.length)throw Error("Duplicate college baseball game IDs");
 if(rows.some(r=>!gameMap.has(r.game_id)))throw Error("Unmatched player-stat game ID");
 const byPlayer=new Map();
 for(const r of rows){
  const id=String(r.player_id||"");
  if(!id)continue;
  let p=byPlayer.get(id);
  if(!p){p={player_id:id,name:r.player||"Player",teams:new Set(),games:new Set(),rows:[]};byPlayer.set(id,p)}
  if(r.team)p.teams.add(r.team);
  p.games.add(r.game_id);
  p.rows.push(r);
 }
 const players=[...byPlayer.values()].map(p=>({...p,teams:[...p.teams],games:[...p.games]}));
 return {games:games.slice().sort((a,b)=>b.date.localeCompare(a.date)||a.id.localeCompare(b.id)),rows,players,gameMap,report,crosswalk};
}
function sum(rows,category,key){
 const values=rows.map(r=>stat(r[category]?.[key])).filter(v=>v!=null);
 return values.length?values.reduce((a,b)=>a+b,0):null;
}
function bat(rows){
 const ab=sum(rows,"batting","atBats"),h=sum(rows,"batting","hits"),d=sum(rows,"batting","doubles"),t=sum(rows,"batting","triples"),hr=sum(rows,"batting","homeRuns");
 const bb=sum(rows,"batting","baseOnBalls"),hbp=sum(rows,"batting","hitByPitch"),sf=sum(rows,"batting","sacFlies");
 const singles=h!=null&&d!=null&&t!=null&&hr!=null?h-d-t-hr:null;
 const tb=singles==null?null:singles+2*d+3*t+4*hr;
 const obDen=ab!=null&&bb!=null&&hbp!=null&&sf!=null?ab+bb+hbp+sf:null;
 return {atBats:ab,hits:h,runs:sum(rows,"batting","runs"),homeRuns:hr,rbi:sum(rows,"batting","rbi"),
   walks:bb,strikeouts:sum(rows,"batting","strikeOuts"),stolenBases:sum(rows,"batting","stolenBases"),
   average:ab>0&&h!=null?h/ab:null,
   obp:obDen>0&&h!=null?(h+bb+hbp)/obDen:null,
   slg:ab>0&&tb!=null?tb/ab:null,
   ops:obDen>0&&ab>0&&tb!=null&&h!=null?(h+bb+hbp)/obDen+tb/ab:null};
}
function pitch(rows){
 const outs=sum(rows,"pitching","outs"),earnedRuns=sum(rows,"pitching","earnedRuns"),h=sum(rows,"pitching","hits"),walks=sum(rows,"pitching","baseOnBalls");
 return {outs,innings:outs==null?null:Math.floor(outs/3)+"."+(outs%3),strikeouts:sum(rows,"pitching","strikeOuts"),
  hits:h,walks,earnedRuns,era:outs>0&&earnedRuns!=null?27*earnedRuns/outs:null,
  whip:outs>0&&h!=null&&walks!=null?3*(h+walks)/outs:null,
  wins:sum(rows,"pitching","wins"),losses:sum(rows,"pitching","losses"),saves:sum(rows,"pitching","saves")};
}
const rate=(v,n)=>v==null?"—":Number(v).toFixed(n).replace(n===3?/^0(?=\.)/:/$^/,"");
function metrics(items){return '<div class="metrics">'+items.map(([name,val])=>'<div class="metric"><strong>'+esc(val==null?"—":String(val))+'</strong><small>'+esc(name)+'</small></div>').join("")+'</div>'}
function pending(message){return '<div class="cb-empty">'+esc(message)+'</div>'}
function score(g){return g.away_score==null||g.home_score==null?"Score pending":fmt(g.away_score)+" – "+fmt(g.home_score)}
function gameLabel(g){return g.away+" @ "+g.home}
function sourceLabel(g){return g.verification==="official_boxscore_verified"?"Official player box score verified":g.verification==="official_scoreboard_verified"?"Official score & innings verified · player stats pending":g.away_score!=null?"Score from attendance list · source check pending":"Attendance logged · box score pending"}
function gameName(g){return '<a href="'+gameUrl(g)+'">'+esc(date(g.date))+" · "+esc(gameLabel(g))+'</a>'}
function gameCard(g){
 return '<article class="cb-game-card"><div class="cb-card-meta">'+esc(date(g.date))+(g.game_number?' · Game '+g.game_number:'')+'</div>'
 +'<h3>'+gameName(g)+'</h3><div class="cb-score">'+esc(score(g))+'</div>'
 +'<p class="cb-card-meta">'+esc(g.ballpark||"Ballpark not recorded")+' · '+esc(sourceLabel(g))+'</p>'
 +'<a class="cb-link" href="'+gameUrl(g)+'">View game ↗</a></article>';
}
function htmlTable(columns,rows,whenEmpty="No verified player statistics yet"){
 return '<div class="cb-table-wrap"><table class="cb-table"><thead><tr>'+columns.map(s=>'<th scope="col">'+esc(s)+'</th>').join("")+'</tr></thead><tbody>'
 +(rows.length?rows.join(""):'<tr><td colspan="'+columns.length+'">'+esc(whenEmpty)+'</td></tr>')+'</tbody></table></div>';
}
function chart(items){
 const max=Math.max(1,...items.map(x=>x[1]));
 return '<div class="cb-bars">'+items.map(([k,v])=>'<div class="cb-bar"><span class="cb-bar-label">'+esc(k)+'</span><span class="cb-track"><span class="cb-fill" style="display:block;width:'+(100*v/max).toFixed(1)+'%"></span></span><strong>'+fmt(v)+'</strong></div>').join("")+'</div>';
}
function counts(items){
 const m=new Map();for(const i of items)if(i)m.set(i,(m.get(i)||0)+1);
 return [...m.entries()].sort((a,b)=>b[1]-a[1]||a[0].localeCompare(b[0]));
}
function gameSearch(g,q){return [g.date,g.away,g.home,g.ballpark,g.city,g.state,g.postseason_round].some(x=>String(x||"").toLowerCase().includes(q))}
function renderHome(d){
 const seasons=unique(d.games.map(g=>g.season));const teams=counts(d.games.flatMap(g=>[g.home,g.away]));const parks=counts(d.games.map(g=>g.ballpark));
 $("app").innerHTML='<div class="cb-intro"><div class="eyebrow">College Baseball · Attendance history</div><h1>Your college baseball history.</h1><p class="lead">Every college game you attended—box scores, the players you witnessed, historic performances, ballparks, and the eventual road to professional baseball.</p></div>'
 +'<div class="cb-note"><strong>Independent college archive:</strong> College batting and pitching totals stay separate from MLB and Minor League Baseball. Player profiles can connect across levels only when their identity is verified.</div>'
 +metrics([["Games logged",d.games.length],["Seasons",seasons.length],["Schools seen",teams.length],["Ballparks logged",parks.length]])
 +(d.games.length?
 '<div class="cb-chart-grid"><section class="panel"><h2>Most-watched programs</h2>'+chart(teams.slice(0,8))+'</section><section class="panel"><h2>Ballpark history</h2>'+(parks.length?chart(parks.slice(0,8)):pending("Ballpark details await import."))+'</section></div>'
 +'<div class="section-heading"><h2>Recently attended games</h2><a href="./game.html" class="action-link secondary">Explore all games ↗</a></div><div class="cb-grid">'+d.games.slice(0,6).map(gameCard).join("")+'</div>'
 :pending("Ready for your first college baseball attendance list. No games have been added or invented. The import template accepts dates, teams, ballparks, tournament rounds, and doubleheader game numbers."))
 +'<div class="section-heading"><h2>Build your college baseball archive</h2></div><div class="cb-grid">'
 +'<div class="cb-game-card"><h3>Games & box scores</h3><p class="cb-sub">Inning-by-inning results, lineups, batting, pitching, scoring details and pitching decisions when official sources are verified.</p><a href="./game.html" class="cb-link">View games ↗</a></div>'
 +'<div class="cb-game-card"><h3>Players & leaderboards</h3><p class="cb-sub">Every player you watched, with witnessed-game career lines and hitter/pitcher summaries, including two-way players.</p><a href="./stats.html" class="cb-link">View players ↗</a></div>'
 +'<div class="cb-game-card"><h3>Signature performances</h3><p class="cb-sub">Best single-game hitting and pitching performances, records, and tournament milestones; no fabricated data.</p><a href="./records.html" class="cb-link">View records ↗</a></div></div>';
}
function renderGames(d){
 $("app").innerHTML='<div class="eyebrow">College Baseball · Game archive</div><h1>Games & Box Scores</h1>'
 +'<p class="lead">Search your personal game history. Scores and player totals are shown only to the extent documented in the original attendance list or later verified official gamebooks.</p>'
 +'<div class="cb-toolbar"><label for="cb-game-select">Game</label><select id="cb-game-select"><option value="">Select an attended game</option>'+d.games.map(g=>'<option value="'+esc(g.id)+'">'+esc(date(g.date)+" · "+gameLabel(g))+'</option>').join("")+'</select></div><div id="cb-game-details"></div>'
 +'<div class="section-heading"><h2>All attended games</h2></div><div class="cb-toolbar"><input id="cb-game-search" type="search" aria-label="Search dates teams and parks" placeholder="Search teams, dates, venue or tournament…"><select id="cb-season-filter" aria-label="Season filter"><option value="">All seasons</option>'+unique(d.games.map(g=>g.season)).sort((a,b)=>b-a).map(y=>'<option>'+y+'</option>').join("")+'</select></div><div id="cb-game-list"></div>';
 const chosen=new URLSearchParams(location.search).get("id");
 const picker=$("cb-game-select");
 if(chosen&&d.gameMap.has(chosen))picker.value=chosen;
 const showGame=()=>{
  const g=d.gameMap.get(picker.value);
  if(!g){$("cb-game-details").innerHTML=pending(d.games.length?"Select a game above to open its score and verified player box score.":"No college baseball games imported yet.");return}
  const source=link(g.source_url),players=d.rows.filter(x=>x.game_id===g.id);
  const innings=Array.isArray(g.innings)&&g.innings.length?renderInnings(g):"";
  const box=players.length?renderBox(g,players):pending(g.verification==="official_scoreboard_verified"?"The official final score, inning line and pitching decisions are verified. Complete individual batting and pitching box score import remains pending.":"Official college player box score not yet imported for this attended game. No batting or pitching lines have been fabricated.");
  $("cb-game-details").innerHTML='<section class="cb-game-summary"><div class="cb-card-meta">'+esc(date(g.date))+(g.game_number?' · Doubleheader game '+g.game_number:'')+'</div><h2>'+esc(gameLabel(g))+'</h2>'
  +'<div class="cb-score">'+esc(score(g))+'</div><span class="cb-chip '+(g.verification==="official_boxscore_verified"?"":"pending")+'">'+esc(sourceLabel(g))+'</span>'
  +'<p class="cb-card-meta">'+esc(g.ballpark||"Ballpark pending")+(g.city?' · '+esc(g.city):"")+(g.state?', '+esc(g.state):"")+(g.neutral_site===true?' · Neutral site':'')+(g.postseason_round?' · '+esc(g.postseason_round):"")+'</p>'
  +(source?'<a href="'+esc(source)+'" target="_blank" rel="noopener noreferrer" class="cb-link">Game source ↗</a>':"")
  +'</section>'+innings+(g.pitching_decisions?'<div class="panel"><h2>Official pitching decisions</h2><p class="cb-sub">W: '+esc(g.pitching_decisions.winner||"—")+' · L: '+esc(g.pitching_decisions.loser||"—")+(g.pitching_decisions.save?' · SV: '+esc(g.pitching_decisions.save):'')+'</p></div>':'')+'<div class="section-heading"><h2>Player box score</h2></div>'+box;
 };
 picker.addEventListener("change",()=>{if(picker.value)history.replaceState(null,"","?id="+encodeURIComponent(picker.value));else history.replaceState(null,"",location.pathname);showGame()});
 const draw=()=>{
  const q=$("cb-game-search").value.trim().toLowerCase(),year=$("cb-season-filter").value;
  const list=d.games.filter(g=>(!year||String(g.season)===year)&&gameSearch(g,q));
  $("cb-game-list").innerHTML=list.length?htmlTable(["Date","Matchup","Score","Ballpark","Verification"],list.map(g=>'<tr><td><a href="'+gameUrl(g)+'">'+esc(date(g.date))+'</a></td><td>'+esc(gameLabel(g))+'</td><td>'+esc(score(g))+'</td><td>'+esc(g.ballpark||"—")+'</td><td>'+esc(sourceLabel(g))+'</td></tr>')):pending("No matching attended games. Import a college baseball list or adjust the filters.");
 };
 $("cb-game-search").addEventListener("input",draw);$("cb-season-filter").addEventListener("change",draw);
 draw();showGame();
}
function renderInnings(g){
 const arr=g.innings;
 return '<div class="section-heading"><h2>Inning-by-inning</h2></div>'
 +htmlTable(["Club",...arr.map((_,i)=>String(i+1)),"R"],
 [[g.away,...arr.map(x=>x.away),g.away_score],[g.home,...arr.map(x=>x.home),g.home_score]].map((row)=>'<tr>'+row.map(x=>'<td>'+esc(x==null?"—":x)+'</td>').join("")+'</tr>'));
}
function renderBox(g,rows){
 const sides=[["Away",g.away],["Home",g.home]];
 return '<div class="cb-boxscore">'+sides.map(([label,team])=>{
 const own=rows.filter(x=>x.team===team||x.team_id===team);
 const bats=own.filter(x=>x.batting!=null),pits=own.filter(x=>x.pitching!=null);
 const player=x=>'<a href="'+playerUrl(x)+'">'+esc(x.player||"Unknown player")+'</a>';
 const numStat=(r,cat,key)=>{const n=stat(r[cat]?.[key]);return n==null?"—":fmt(n)};
 const batting=htmlTable(["Batter","AB","R","H","2B","3B","HR","RBI","BB","SO"],bats.map(r=>'<tr><td>'+player(r)+'</td>'+["atBats","runs","hits","doubles","triples","homeRuns","rbi","baseOnBalls","strikeOuts"].map(k=>'<td>'+numStat(r,"batting",k)+'</td>').join("")+'</tr>'));
 const pitching=htmlTable(["Pitcher","IP","H","R","ER","BB","SO","Pitches"],pits.map(r=>'<tr><td>'+player(r)+'</td><td>'+esc(r.pitching.outs==null?"—":Math.floor(r.pitching.outs/3)+"."+(r.pitching.outs%3))+'</td>'+["hits","runs","earnedRuns","baseOnBalls","strikeOuts","numberOfPitches"].map(k=>'<td>'+numStat(r,"pitching",k)+'</td>').join("")+'</tr>'));
 return '<section><h3>'+esc(label+" · "+team)+"</h3><h4>Batting</h4>"+batting+"<h4>Pitching</h4>"+pitching+"</section>";
 }).join("")+'</div>';
}
function renderPlayers(d){
 $("app").innerHTML='<div class="eyebrow">College Baseball · Witnessed players</div><h1>Players & leaderboards</h1><p class="lead">College box-score statistics only. When players reach professional baseball, their college lines will remain independent and can connect to separate verified MLB profiles.</p>'
 +'<div class="cb-toolbar"><input id="cb-player-search" type="search" placeholder="Search player or college…" aria-label="Player name or school">'
 +'<select id="cb-role" aria-label="Player role"><option value="hit">Batting</option><option value="pitch">Pitching</option></select>'
 +'<select id="cb-sort" aria-label="Sort statistical leaderboard"></select></div><p id="cb-board-note" class="cb-sub"></p><div id="cb-player-board"></div>';
 const roles={hit:[["hits","Hits"],["homeRuns","Home runs"],["rbi","RBI"],["average","AVG"],["ops","OPS"],["atBats","At-bats"]],pitch:[["strikeouts","Strikeouts"],["outs","Outs pitched"],["era","ERA"],["whip","WHIP"],["wins","Wins"],["saves","Saves"]]};
 let role="hit";
 function options(){const sel=$("cb-sort");sel.innerHTML=roles[role].map(([key,label])=>'<option value="'+key+'">'+label+'</option>').join("");sel.value=role==="hit"?"hits":"strikeouts"}
 function draw(){
  const field=$("cb-sort").value,q=$("cb-player-search").value.trim().toLowerCase();
  const rows=d.players.map(p=>({...p,stats:role==="hit"?bat(p.rows):pitch(p.rows)}))
  .filter(p=>p.name.toLowerCase().includes(q)||p.teams.join(" ").toLowerCase().includes(q))
  .filter(p=>p.stats[field]!=null)
  .sort((a,b)=>field==="era"||field==="whip"?(a.stats[field]-b.stats[field])||a.name.localeCompare(b.name):(b.stats[field]-a.stats[field])||a.name.localeCompare(b.name)).slice(0,200);
  $("cb-board-note").textContent="Rankings include only recorded values from imported college box scores. Missing categories are excluded rather than counted as zeros.";
  if(!d.players.length){$("cb-player-board").innerHTML=pending("No college player box scores have been imported yet. This leaderboard will populate as official college gamebooks are verified.");return}
  const cols=role==="hit"?["Player / school","Games","AB","H","HR","RBI","AVG","OPS"]:["Player / school","Games","IP","H","BB","SO","ERA","WHIP"];
  const body=rows.map(p=>{
   const s=p.stats;
   const vals=role==="hit"?[s.atBats,s.hits,s.homeRuns,s.rbi,rate(s.average,3),rate(s.ops,3)]:[s.innings,s.hits,s.walks,s.strikeouts,rate(s.era,2),rate(s.whip,2)];
   return '<tr><td><a href="'+playerUrl(p)+'">'+esc(p.name)+'</a><div class="cb-card-meta">'+esc(p.teams.join(" / "))+'</div></td><td>'+p.games.length+'</td>'+vals.map(x=>'<td>'+esc(x==null?"—":fmt(Number(x))===x?x:String(x))+'</td>').join("")+'</tr>';
  });
  $("cb-player-board").innerHTML=htmlTable(cols,body,"No players have recorded statistics in this category.");
 }
 $("cb-role").addEventListener("change",()=>{role=$("cb-role").value;options();draw()});
 $("cb-sort").addEventListener("change",draw);$("cb-player-search").addEventListener("input",draw);
 options();draw();
}
function renderPlayer(d){
 const id=new URLSearchParams(location.search).get("id"),p=d.players.find(x=>String(x.player_id)===id);
 if(!p){$("app").innerHTML='<div class="eyebrow">College Baseball · Player profile</div><h1>Player profile</h1>'+pending("No verified college baseball player profile is available for this ID. Players appear after official gamebook imports.");return}
 const b=bat(p.rows),pi=pitch(p.rows);
 const qualifiedHit=p.rows.some(x=>x.batting!=null),qualifiedPitch=p.rows.some(x=>x.pitching!=null);
 const cross=d.crosswalk.find(x=>x.verified===true&&String(x.college_player_id)===id);
 const entries=unique(p.rows.map(x=>x.game_id)).map(game_id=>d.gameMap.get(game_id)).filter(Boolean).sort((a,b)=>a.date.localeCompare(b.date));
 $("app").innerHTML='<div class="eyebrow">College Baseball · Player profile</div><h1>'+esc(p.name)+'</h1><p class="lead">'+esc(p.teams.join(" / "))+' · '+p.games.length+' game'+(p.games.length===1?"":"s")+' witnessed</p>'
 +'<div class="cb-note">Only college baseball appearances from attended games appear here; professional seasons are not added to college totals.</div>'
 +(qualifiedHit?'<h2>Hitting in games you attended</h2>'+metrics([["Games with batting",p.rows.filter(r=>r.batting!=null).length],["Hits",fmt(b.hits)],["Home runs",fmt(b.homeRuns)],["AVG",rate(b.average,3)],["RBI",fmt(b.rbi)],["OPS",rate(b.ops,3)] ]):"")
 +(qualifiedPitch?'<h2>Pitching in games you attended</h2>'+metrics([["IP",pi.innings??"—"],["Strikeouts",fmt(pi.strikeouts)],["Wins",fmt(pi.wins)],["Losses",fmt(pi.losses)],["ERA",rate(pi.era,2)],["WHIP",rate(pi.whip,2)]]):"")
 +(cross?'<div class="cb-note"><strong>Professional connection:</strong> Verified identity link to this player’s independent <a class="cb-link" href="../mlb/player.html?id='+encodeURIComponent(cross.mlb_player_id)+'">MLB attendance profile ↗</a>. College and MLB statistics remain separate.</div>':"")
 +'<h2>Every game you witnessed</h2><div class="cb-grid">'+entries.map(gameCard).join("")+'</div>'
 +'<h2>Recorded college game logs</h2>'
 +htmlTable(["Date","Matchup","AB","H","HR","RBI","IP","K"],p.rows.map(r=>{
  const g=d.gameMap.get(r.game_id);
  return '<tr><td><a href="'+gameUrl(g)+'">'+esc(date(g.date))+'</a></td><td>'+esc(gameLabel(g))+'</td>'
  +[stat(r.batting?.atBats),stat(r.batting?.hits),stat(r.batting?.homeRuns),stat(r.batting?.rbi),r.pitching?.outs!=null?Math.floor(r.pitching.outs/3)+"."+(r.pitching.outs%3):null,stat(r.pitching?.strikeOuts)].map(x=>'<td>'+esc(x==null?"—":x)+'</td>').join("")+'</tr>';
 })) ;
}
function renderRecords(d){
 const defs=[["Hits","batting","hits"],["Home runs","batting","homeRuns"],["RBI","batting","rbi"],["Strikeouts","pitching","strikeOuts"],["Outs pitched","pitching","outs"],["Stolen bases","batting","stolenBases"]];
 $("app").innerHTML='<div class="eyebrow">College Baseball · Historical records</div><h1>Signature Performances</h1><p class="lead">Best single-game performances you witnessed, drawn strictly from imported and source-verified college box scores.</p>'
 +'<div class="cb-note">The top witnessed performance is not necessarily a season or school record. We will never infer missing stats from an incomplete scorebook.</div>'
 +(d.rows.length?'<div class="cb-grid">'+defs.map(([label,category,key])=>{
  const list=d.rows.map(r=>({r,val:stat(r[category]?.[key])})).filter(x=>x.val!=null&&d.gameMap.has(x.r.game_id));
  list.sort((a,b)=>b.val-a.val||a.r.player.localeCompare(b.r.player));
  if(!list.length)return '<article class="cb-record"><small>'+esc(label)+'</small><strong>—</strong><p>Not available in verified gamebooks</p></article>';
  const best=list[0],g=d.gameMap.get(best.r.game_id);
  return '<article class="cb-record"><small>'+esc(label+' · single game')+'</small><strong>'+esc(key==="outs"?Math.floor(best.val/3)+"."+(best.val%3)+" IP":fmt(best.val))+'</strong><p><a href="'+playerUrl(best.r)+'" class="cb-link">'+esc(best.r.player)+'</a></p><p>'+gameName(g)+'</p></article>';
 }).join("")+'</div>'
 +defs.map(([label,category,key])=>{
  const list=d.rows.map(r=>({r,val:stat(r[category]?.[key])})).filter(x=>x.val!=null&&d.gameMap.has(x.r.game_id));
  list.sort((a,b)=>b.val-a.val||a.r.player.localeCompare(b.r.player));
  return '<h2>Top '+esc(label.toLowerCase())+' games</h2>'+htmlTable(["#","Player","Performance","Date / matchup"],list.slice(0,10).map(({r,val},i)=>'<tr><td>'+(i+1)+'</td><td><a href="'+playerUrl(r)+'">'+esc(r.player)+'</a></td><td>'+esc(key==="outs"?Math.floor(val/3)+"."+(val%3)+" IP":fmt(val))+'</td><td>'+gameName(d.gameMap.get(r.game_id))+'</td></tr>'));
 }).join("")
 :pending("Individual-game batting and pitching records will appear after your attendance list is matched to official college baseball scorebooks. No records have been fabricated."));
}
function render(){
 const page=document.body.dataset.page||"home",app=$("app");
 $("navigation").innerHTML=nav(page);
 app.innerHTML=pending("Loading college baseball attendance records…");
 load().then(d=>{
  if(page==="games")renderGames(d);
  else if(page==="players")renderPlayers(d);
  else if(page==="records")renderRecords(d);
  else if(page==="player")renderPlayer(d);
  else renderHome(d);
 }).catch(e=>{app.innerHTML=pending("Unable to load college baseball data: "+e.message)});
}
if(document.readyState==="loading")document.addEventListener("DOMContentLoaded",render,{once:true});
else render();
window.CollegeBaseballArchive={load,bat,pitch};
})();