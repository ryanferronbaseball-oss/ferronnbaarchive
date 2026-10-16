document.addEventListener("DOMContentLoaded",async()=>{
"use strict";
const A=window.SoccerArchive,app=document.getElementById("app"),el=id=>document.getElementById(id);
const page=document.body.dataset.page||"home";
const esc=A.esc,dt=A.date,link=A.gameUrl,pl=A.playerLink;
el("navigation").innerHTML=A.nav(page);
const row=(list,empty,colspan=5)=>list.join("")||'<tr><td class="soccer-muted" colspan="'+colspan+'">'+empty+'</td></tr>';
const warn=(m)=>'<p class="soccer-note">'+m+'</p>';
const label=v=>String(v??"—");
let data;
try{data=await A.load()}catch(err){app.innerHTML='<div class="soccer-panel">Unable to load soccer archive: '+esc(err.message)+'</div>';return;}
const {matches,players,byId}=data;
const goals=matches.flatMap(m=>A.scored(m).map(e=>({...e,m})));
const latest=matches.slice().sort((a,b)=>b.date.localeCompare(a.date));
const one=(id)=>byId.get(id)||latest[0];
const homeTeam=g=>g.home,awayTeam=g=>g.away;
const playerByName=name=>players.find(p=>A.slug(p.name)===A.slug(name));
const summary=(m)=>esc(m.home)+' '+m.home_score+'–'+m.away_score+' '+esc(m.away);
const badge=(t)=>'<span class="soccer-micro">'+esc(t)+'</span>';
const initial=n=>String(n).split(/\s+/).map(x=>x[0]).slice(0,2).join("").toUpperCase();
const share=(p)=>'<a href="'+A.playerUrl(p.name)+'">'+esc(p.name)+'</a>';
const eventHtml=(e,g,compact=false)=>{
 const title=A.eventName[e.type]||e.type;
 const detail=e.type==="substitution"?"Replaced "+esc(e.out||"unknown player"):
 (e.assist?'Assist: '+esc(e.assist):"")+(e.secondary_assist?' · Secondary: '+esc(e.secondary_assist):"")+
 (e.type==="own_goal"?" · Credited to opposition":"");
 const score=e.type==="goal"||e.type==="own_goal"||e.type==="penalty_goal"?
 badge(e.type==="own_goal"?"OG":e.type==="penalty_goal"?"Penalty":"Goal"):"";
 return '<div class="soccer-event"><div class="time">'+esc(e.minute)+"'</div><div><b>"+esc(e.team)+' · '+esc(title)+'</b><div><a href="'+A.playerUrl(e.player)+'">'+esc(e.player||"Unattributed")+'</a></div>'+(detail?'<div class="details">'+detail+'</div>':"")+'</div><div class="score-at">'+score+'</div></div>';
};
const bar=(entries)=>{
 const max=Math.max(1,...entries.map(x=>x[1]));
 return entries.map(([name,value])=>'<div class="soccer-bar"><span>'+esc(name)+'</span><div class="bartrack"><div class="barfill" style="width:'+(value/max*100).toFixed(1)+'%"></div></div><strong>'+value+'</strong></div>').join("");
};
const goalsTotal=matches.reduce((n,m)=>n+m.home_score+m.away_score,0);
function metricCards(rows){return '<section class="metrics">'+rows.map(([title,value])=>'<div class="metric"><strong>'+A.fmt(value)+'</strong><small>'+esc(title)+'</small></div>').join("")+'</section>'}
const selectors='<div class="soccer-filters"><label for="query">Find a match<input id="query" type="search" placeholder="Team, venue or date"></label><label for="sort">Sort<select id="sort"><option value="new">Newest first</option><option value="old">Oldest first</option></select></label></div>';
function gamesTable(ms){
 return '<div class="table-wrap"><table class="soccer-stat-table"><thead><tr><th>Date</th><th>Match</th><th>Final</th><th>Competition</th><th>Report</th></tr></thead><tbody>'
 +row(ms.map(m=>'<tr><td>'+dt(m.date)+'</td><td>'+esc(m.home)+' vs '+esc(m.away)+'</td><td class="soccer-stat">'+m.home_score+'–'+m.away_score+'</td><td>'+esc(m.competition)+'</td><td><a href="'+link(m)+'">Match ↗</a></td></tr>'),"No matches found")+'</tbody></table></div>';
}
function history(rootId){
 const render=()=>{const q=(el("query")?.value||"").toLowerCase(),sort=el("sort")?.value||"new";const filtered=matches.filter(m=>[m.home,m.away,m.venue,m.city,m.competition,m.date].join(" ").toLowerCase().includes(q)).sort((a,b)=>sort==="new"?b.date.localeCompare(a.date):a.date.localeCompare(b.date));el(rootId).innerHTML=gamesTable(filtered);};
 for(const id of ["query","sort"])el(id)?.addEventListener("input",render);
 render();
}
function overview(){
 const teams=new Map(),years=new Map();
 for(const m of matches){for(const name of [m.home,m.away])teams.set(name,(teams.get(name)||0)+1);years.set(m.season,(years.get(m.season)||0)+1);}
 const categories=[
  ["Goals in one match","goals"],["Direct assists in one match","assists"],["Goal contributions in one match","contributions"]
 ];
 const per=matches.flatMap(m=>players.flatMap(p=>{const l=p.matchLog.find(x=>x.id===m.id);return l?[{m,p,goals:l.goals,assists:l.assists,contributions:l.goals+l.assists}]:[]}));
 app.innerHTML='<div class="eyebrow">Pro soccer · MLS & FIFA World Cup</div><h1>Your soccer history.</h1>'
 +'<p class="lead">Three matches across MLS and the FIFA World Cup. Explore the same personal game history, players, signature performances and records you know from basketball and football.</p>'
 +metricCards([["Matches",matches.length],["Goals witnessed",goalsTotal],["Players who appeared",players.filter(p=>p.appearances).length],["Competitions",new Set(matches.map(m=>m.competition)).size]])
 +'<div class="section-heading"><h2>Recent matches</h2><a class="action-link secondary" href="./game.html">Explore games ↗</a></div>'
 +'<section class="game-grid">'+latest.map(A.matchCard).join("")+'</section>'
 +'<div class="section-heading"><h2>Signature Performances</h2><a class="action-link secondary" href="./records.html">View all Records ↗</a></div>'
 +'<p class="soccer-info">Single-match performances from matches you attended, not full-season totals.</p><div class="soccer-grid">'
 +categories.map(([title,k])=>{const a=per.slice().sort((a,b)=>b[k]-a[k]||b.assists-a.assists||b.goals-a.goals||a.p.name.localeCompare(b.p.name))[0];
 return '<article class="soccer-tile"><small>'+esc(title)+'</small>'+ (a?'<div class="soccer-feature"><div class="soccer-avatar">'+initial(a.p.name)+'</div><div class="data"><strong>'+a[k]+'</strong><div>'+pl(a.p)+'</div><small>'+dt(a.m.date)+'</small></div></div><a href="'+link(a.m)+'">View performance ↗</a>':"No qualifying player")+'</article>'}).join("")+'</div>'
 +'<div class="soccer-charts"><section class="soccer-chart"><h3>Most Watched Teams</h3>'+bar([...teams].sort((a,b)=>b[1]-a[1]))+'</section><section class="soccer-chart"><h3>Attendance by Year</h3>'+bar([...years].sort((a,b)=>a[0]-b[0]).map(([a,b])=>[String(a),b]))+'</section></div>'
 +'<section class="soccer-panel"><h2>My Game History</h2>'+selectors+'<div id="history"></div></section>'
 +warn('The three-match launch excludes San Diego Loyal vs. Oakland Roots (2021) and Arizona United vs. Sacramento (2016). MLS secondary assists are separated from direct assists.');
 history("history");
}
function matchStats(m){
 const home=m.team_stats?.home||{},away=m.team_stats?.away||{};
 const fields=[["Shots","shots"],["Shots on target","shots_on_target"],["Saves","saves"],["Corners","corners"],["Possession","possession"]];
 const available=fields.filter(([a,k])=>home[k]!=null&&away[k]!=null);
 if(!available.length)return warn('Individual and team shooting metrics are not available from the verified report for this match.');
 return '<div class="table-wrap"><table class="soccer-stat-table"><thead><tr><th>Team statistic</th><th>'+esc(m.home_abbr)+'</th><th>'+esc(m.away_abbr)+'</th></tr></thead><tbody>'
 +available.map(([name,k])=>'<tr><td>'+name+'</td><td>'+home[k]+(k==="possession"?"%":"")+'</td><td>'+away[k]+(k==="possession"?"%":"")+'</td></tr>').join("")+'</tbody></table></div>';
}
function lineup(m,side){
 const team=side==="home"?m.home:m.away,starters=m[side+"_starters"],subs=m[side+"_subs_used"]||[];
 return '<section><h3>'+esc(team)+'</h3><b>Starting XI</b><ol>'+starters.map(n=>'<li><a href="'+A.playerUrl(n)+'">'+esc(n)+'</a></li>').join("")+'</ol>'
 +'<b>Substitutes used</b><ul>'+subs.map(n=>'<li><a href="'+A.playerUrl(n)+'">'+esc(n)+'</a></li>').join("")+'</ul></section>';
}
function gameView(m){
 const statline=(m.home_score+m.away_score)+' total goals · '+m.competition;
 return '<div class="eyebrow">Soccer · Games / Match Reports</div><h1>Match details.</h1><p class="lead">Match reports with starting lineups, scoring plays, verified player events and team statistics.</p>'
 +'<div class="soccer-filters"><label>Select a match<select id="gameSelect">'+matches.map(x=>'<option value="'+esc(x.id)+'"'+(x.id===m.id?" selected":"")+'>'+dt(x.date)+' · '+esc(x.home_abbr)+' vs '+esc(x.away_abbr)+'</option>').join("")+'</select></label></div>'
 +'<div class="soccer-scoreline"><div class="soccer-side">'+esc(m.home)+'</div><div class="soccer-final"><strong>'+m.home_score+'–'+m.away_score+'</strong><small>FULL TIME</small></div><div class="soccer-side">'+esc(m.away)+'</div></div>'
 +'<p class="soccer-info">'+dt(m.date)+' · '+esc(m.competition)+' · '+esc(m.venue)+' · '+esc(m.city)+(m.attendance?' · '+A.fmt(m.attendance)+' announced attendance':'')+'</p>'
 +metricCards([["Goals",m.home_score+m.away_score],["Scorers",new Set(A.scored(m).filter(e=>e.type!=="own_goal").map(e=>e.player)).size],["Events logged",m.events.length],["Players appeared",new Set([...m.home_starters,...m.away_starters,...(m.home_subs_used||[]),...(m.away_subs_used||[])]).size]])
 +'<section class="soccer-panel"><h2>Goals</h2>'+A.scored(m).map(e=>eventHtml(e,m,true)).join("")+'</section>'
 +'<section class="soccer-panel"><h2>Player box score & lineups</h2><div class="soccer-lineup">'+lineup(m,"home")+lineup(m,"away")+'</div></section>'
 +'<section class="soccer-panel"><h2>Team statistics</h2>'+matchStats(m)+'</section>'
 +'<section class="soccer-panel"><h2>Match timeline</h2>'+(m.events||[]).slice().sort((a,b)=>A.eventOrder(a)-A.eventOrder(b)).map(e=>eventHtml(e,m)).join("")+'</section>'
 +warn('Source: <a href="'+esc(m.source_url)+'" target="_blank" rel="noopener">Original match report ↗</a>. Goals, direct assists, secondary MLS assists, cards and lineup participation are separated. Player shots, passing and xG are not inferred.');
}
function gamesView(){
 let id=new URLSearchParams(location.search).get("id");const m=one(id);
 const render=(x)=>{app.innerHTML=gameView(x);el("gameSelect").addEventListener("change",()=>{const next=one(el("gameSelect").value);history.replaceState(null,"",link(next));render(next)});}
 render(m);
}
const columns=[["Appearances","appearances"],["Starts","starts"],["Goals","goals"],["Direct assists","assists"],["Goal contributions","contributions"],["MLS secondary assists","secondary_assists"],["Clean sheets (GK)","clean_sheets"],["Yellow cards","yellow"],["Red cards","red"]];
function statsTable(list,key,isSingle=false){
 return '<div class="table-wrap"><table class="soccer-stat-table"><thead><tr><th>#</th><th>Player</th><th>Teams</th><th>Apps</th><th>'+esc(columns.find(x=>x[1]===key)?.[0]||key)+'</th><th>Profile</th></tr></thead><tbody>'
 +row(list.map((p,i)=>'<tr><td>'+(i+1)+'</td><td>'+pl(p)+'</td><td>'+esc(p.teams.join(", "))+'</td><td>'+p.appearances+'</td><td class="soccer-stat">'+p[key]+'</td><td>'+pl(p)+'</td></tr>'),'No verified player performance for this category',6)
 +'</tbody></table></div>';
}
function leaderboards(){
 app.innerHTML='<div class="eyebrow">Pro soccer · Personal player statistics</div><h1>Player leaderboards.</h1>'
 +'<p class="lead">Rank players across only the matches you witnessed. Goals, direct assists, appearances, clean sheets and cards are grounded in verified match reports.</p>'
 +'<div class="soccer-panel"><div class="soccer-filters"><label>Category<select id="category">'+columns.map(([l,k])=>'<option value="'+k+'">'+l+'</option>').join("")+'</select></label><label>Match<select id="matchFilter"><option value="all">All three matches</option>'+matches.map(x=>'<option value="'+esc(x.id)+'">'+dt(x.date)+' · '+esc(x.home_abbr)+' vs '+esc(x.away_abbr)+'</option>').join("")+'</select></label></div><h2 id="boardHeading"></h2><div id="board"></div></div>'
 +warn('These are personal attendance totals, not full career or season statistics. Advanced individual shooting, defensive and passing metrics are excluded until independently verified; an unavailable value is not a zero.');
 const draw=()=>{let key=el("category").value,match=el("matchFilter").value;
 let scope=players;
 if(match!=="all"){
  scope=players.filter(p=>p.matchLog.some(l=>l.id===match)).map(p=>{
   const l=p.matchLog.find(x=>x.id===match);
   return {...p,appearances:1,starts:Number(l.started),goals:l.goals,assists:l.assists,secondary_assists:l.secondary_assists,yellow:l.yellow,red:l.red,contributions:l.goals+l.assists,clean_sheets:Number(l.started && p.clean_sheets>0 && matches.find(x=>x.id===l.id)?.[l.team===one(l.id).home_abbr?"away_score":"home_score"]===0 && (one(l.id).home_starters[0]===p.name||one(l.id).away_starters[0]===p.name))};
  });
 }
 const v=A.leaderRows(scope,key,100,key!=="appearances"&&key!=="starts");
 el("boardHeading").textContent=columns.find(x=>x[1]===key)[0]+' · '+(match==="all"?"All attended games":"Selected match");
 el("board").innerHTML=statsTable(v,key);
 };
 el("category").addEventListener("change",draw);el("matchFilter").addEventListener("change",draw);draw();
}
function profile(){
 const id=new URLSearchParams(location.search).get("id")||"";
 const p=players.find(p=>p.id===id);if(!p){app.innerHTML='<h1>Player not found.</h1><p><a href="./stats.html">Browse player leaderboards ↗</a></p>';return;}
 document.title=p.name+" · Soccer | Courtside Archive";
 const log=p.matchLog.slice().sort((a,b)=>b.date.localeCompare(a.date));
 const eventRows=log.map(l=>'<tr><td><a href="./game.html?id='+encodeURIComponent(l.id)+'">'+dt(l.date)+'</a></td><td>'+esc(l.team)+'</td><td>'+esc(l.opponent)+'</td><td>'+(l.started?"Starter":"Substitute")+'</td><td>'+l.goals+'</td><td>'+l.assists+'</td><td>'+l.secondary_assists+'</td><td>'+l.yellow+'</td></tr>');
 app.innerHTML='<div class="eyebrow">Pro Soccer · Player profile</div><div class="soccer-profile-head"><div class="soccer-portrait">'+initial(p.name)+'</div><div><h1 style="margin:0">'+esc(p.name)+'</h1><p class="lead">'+esc(p.teams.join(" / "))+' · '+p.appearances+' attended match'+(p.appearances===1?"":"es")+'</p></div></div>'
 +metricCards([["Appearances",p.appearances],["Goals",p.goals],["Direct assists",p.assists],["Goal contributions",p.contributions]])
 +'<div class="section-heading"><h2>Matches you attended</h2><a class="action-link secondary" href="./stats.html">All leaderboards ↗</a></div><div class="game-grid">'+log.map(l=>A.matchCard(one(l.id))).join("")+'</div>'
 +'<section class="soccer-panel"><h2>Player statistics</h2><div class="soccer-grid">'+[["Starts",p.starts],["MLS secondary assists",p.secondary_assists],["Yellow cards",p.yellow],["Red cards",p.red],["Penalties scored",p.penalties],["Clean sheets (starting GK)",p.clean_sheets]].map(([k,v])=>'<div class="soccer-tile"><small>'+esc(k)+'</small><strong>'+v+'</strong></div>').join("")+'</div></section>'
 +'<section class="soccer-panel"><h2>Individual match logs</h2><div class="table-wrap"><table class="soccer-stat-table"><thead><tr><th>Date</th><th>Team</th><th>Opponent</th><th>Role</th><th>Goals</th><th>Ast</th><th>2nd Ast</th><th>YC</th></tr></thead><tbody>'+eventRows.join("")+'</tbody></table></div></section>'
 +warn('Limited to matches attended. Player shots, xG, minutes, and passing metrics are intentionally unavailable rather than estimated. MLS secondary assists are separate from direct assists.');
}
function tile(label,value,body,href){return '<article class="soccer-tile"><small>'+esc(label)+'</small><strong>'+esc(value)+'</strong><p>'+esc(body||"")+'</p>'+(href?'<a href="'+href+'">View match ↗</a>':'')+'</article>'}
function recordTop(list,k,title){const sorted=list.slice().sort((a,b)=>b[k]-a[k]||b.assists-a.assists||a.p.name.localeCompare(b.p.name));return '<div class="table-wrap"><table class="soccer-stat-table"><thead><tr><th>Rank</th><th>Player</th><th>Club / Country</th><th>Date</th><th>'+esc(title)+'</th><th>Match</th></tr></thead><tbody>'+row(sorted.filter(x=>x[k]>0).slice(0,10).map((x,i)=>'<tr><td>'+(i+1)+'</td><td>'+pl(x.p)+'</td><td>'+esc(x.l.team)+'</td><td>'+dt(x.m.date)+'</td><td class="soccer-stat">'+x[k]+'</td><td><a href="'+link(x.m)+'">Match ↗</a></td></tr>'),'No verified qualifying performances',6)+'</tbody></table></div>';}
function records(){
 const performance=matches.flatMap(m=>players.flatMap(p=>{const l=p.matchLog.find(x=>x.id===m.id);if(!l)return[];return[{p,m,l,goals:l.goals,assists:l.assists,contributions:l.goals+l.assists,secondary_assists:l.secondary_assists,yellow:l.yellow,red:l.red,starts:Number(l.started),appearances:1}]}));
 const definitions=[["Goals","goals"],["Direct assists","assists"],["Goal contributions","contributions"],["MLS secondary assists","secondary_assists"],["Yellow cards","yellow"],["Red cards","red"]];
 app.innerHTML='<div class="eyebrow">Pro soccer · Your personal record book</div><h1>The best I\'ve witnessed.</h1><p class="lead">Single-match records, statistical milestones, team and match records, and legendary soccer moments from your three attended matches.</p>'
 +'<div class="soccer-tabs" id="mainTabs" role="tablist" aria-label="Soccer Records sections">'
 +[['records',"Record Book"],["milestones","Milestones"],["teams","Team & Game Records"],["legendary","Legendary Performances"]].map(([k,t],i)=>'<button role="tab" type="button" data-tab="'+k+'" aria-controls="'+k+'Tab" aria-selected="'+(i===0)+'">'+t+'</button>').join("")+'</div>'
 +'<section class="soccer-records-tab" id="recordsTab" role="tabpanel"><h2>Single-game record holders</h2><div class="soccer-grid" id="recordCards"></div><section class="soccer-panel"><h2>Top 10 single-game performances</h2><p class="soccer-info">Every player-match is ranked separately, including repeat appearances.</p><div class="soccer-filters"><label>Statistic<select id="recordStat">'+definitions.map(([l,k])=>'<option value="'+k+'">'+l+'</option>').join("")+'</select></label></div><div id="recordTop"></div></section></section>'
 +'<section class="soccer-records-tab" id="milestonesTab" role="tabpanel" hidden><section class="soccer-panel"><h2>Statistical milestones</h2><p class="soccer-info">Verified player-match achievements, or a player-frequency leaderboard showing repeat accomplishments.</p><div class="soccer-filters"><label>Milestone<select id="milestoneStat"><option value="goals:1">1+ goal</option><option value="goals:2">2+ goals</option><option value="assists:1">1+ direct assist</option><option value="assists:2">2+ direct assists</option><option value="contributions:2">2+ goal contributions</option><option value="yellow:1">Yellow card</option><option value="red:1">Red card</option></select></label><label>View<select id="milestoneMode"><option value="games">Individual performances</option><option value="players">Player frequency</option></select></label></div><div class="soccer-grid" id="milestoneCards"></div><div id="milestoneTable"></div></section></section>'
 +'<section class="soccer-records-tab" id="teamsTab" role="tabpanel" hidden><h2>Team & Game Records</h2><div class="soccer-grid" id="teamCards"></div><section class="soccer-panel"><h2>Every match</h2><div id="allMatches"></div></section></section>'
 +'<section class="soccer-records-tab" id="legendaryTab" role="tabpanel" hidden><section class="soccer-panel"><h2>Statistical Feats</h2><p class="soccer-info">Exceptional verifiable match events, without subjective performance ratings.</p><div id="feats"></div></section><section class="soccer-panel"><h2>Iconic Moments</h2><p class="soccer-info">Match-turning goals, late scoring plays, penalties and own goals, attributed only when sourced.</p><div id="moments"></div></section></section>'
 +warn('Three-match scope: Nashville SC vs. Cincinnati, Nashville SC vs. Sporting KC, Morocco vs. Haiti. Only verifiable performance categories appear. MLS secondary assists are tracked separately.');
 el("mainTabs").addEventListener("click",e=>{const btn=e.target.closest("[data-tab]");if(!btn)return;const name=btn.dataset.tab;el("mainTabs").querySelectorAll("button").forEach(b=>b.setAttribute("aria-selected",String(b===btn)));["records","milestones","teams","legendary"].forEach(k=>el(k+"Tab").hidden=k!==name);});
 const best=k=>performance.slice().sort((a,b)=>b[k]-a[k]||b.contributions-a.contributions||a.p.name.localeCompare(b.p.name))[0];
 el("recordCards").innerHTML=definitions.map(([title,k])=>{const top=best(k);return tile("Most "+title.toLowerCase(),top[k],top.p.name+" · "+dt(top.m.date),link(top.m))}).join("");
 const record=()=>{const key=el("recordStat").value;el("recordTop").innerHTML=recordTop(performance,key,definitions.find(x=>x[1]===key)[0])};el("recordStat").addEventListener("change",record);record();
 function mile(){
  const [k,th]=el("milestoneStat").value.split(":");const threshold=Number(th),qualifying=performance.filter(x=>x[k]>=threshold),unique=new Set(qualifying.map(x=>x.p.id));
  el("milestoneCards").innerHTML=tile("Qualifying performances",qualifying.length,"Player-matches reaching threshold")+tile("Unique players",unique.size,"Players meeting threshold");
  const mode=el("milestoneMode").value;
  if(mode==="games"){el("milestoneTable").innerHTML=recordTop(qualifying,k,k+" (threshold "+th+"+)");return;}
  const by=new Map();for(const x of qualifying){let row=by.get(x.p.id)||{p:x.p,count:0};row.count++;by.set(x.p.id,row)}
  el("milestoneTable").innerHTML='<div class="table-wrap"><table><thead><tr><th>Player</th><th>Times reached</th><th>Profile</th></tr></thead><tbody>'+row([...by.values()].sort((a,b)=>b.count-a.count).map(x=>'<tr><td>'+pl(x.p)+'</td><td>'+x.count+'</td><td>'+pl(x.p)+'</td></tr>'),'No qualifying players',3)+'</tbody></table></div>';
 }
 ["milestoneStat","milestoneMode"].forEach(k=>el(k).addEventListener("change",mile));mile();
 const max=(getter)=>matches.slice().sort((a,b)=>getter(b)-getter(a))[0];
 const maxTeam=matches.flatMap(m=>[{m,value:m.home_score,team:m.home},{m,value:m.away_score,team:m.away}]).sort((a,b)=>b.value-a.value)[0];
 const high=max(m=>m.home_score+m.away_score),margin=max(m=>Math.abs(m.home_score-m.away_score));
 const close=matches.slice().sort((a,b)=>Math.abs(a.home_score-a.away_score)-Math.abs(b.home_score-b.away_score))[0];
 const late=matches.flatMap(m=>A.scored(m).filter(e=>A.eventOrder(e)>=8500).map(e=>({e,m})));
 const clean=matches.filter(m=>m.home_score===0||m.away_score===0);
 el("teamCards").innerHTML=[
  tile("Most team goals",maxTeam.value,maxTeam.team+" · "+dt(maxTeam.m.date),link(maxTeam.m)),
  tile("Most combined goals",high.home_score+high.away_score,high.home+" vs "+high.away,link(high)),
  tile("Largest winning margin",Math.abs(margin.home_score-margin.away_score),margin.home+" vs "+margin.away,link(margin)),
  tile("Closest match",Math.abs(close.home_score-close.away_score),summary(close),link(close)),
  tile("Clean sheets",clean.length,clean.map(x=>x.home_score===0?x.away:x.home).join(", ")),
  tile("Goals in 85th minute or later",late.length,"Across attended matches")
 ].join("");
 el("allMatches").innerHTML=gamesTable(latest);
 const feats=performance.filter(x=>x.contributions>=2||x.goals>=2||x.assists>=2);
 el("feats").innerHTML=feats.map(x=>'<div class="soccer-event"><span class="time">'+x.contributions+' G+A</span><div><b>'+pl(x.p)+'</b><div class="details">'+esc(x.l.team)+' · '+x.goals+' goals, '+x.assists+' direct assists · '+dt(x.m.date)+'</div></div><a href="'+link(x.m)+'">Match ↗</a></div>').join("")||warn("No players yet meet the high-performance thresholds.");
 let moments=[];for(const m of matches){
  let h=0,a=0,prev=0;
  for(const e of A.scored(m)){
   const was=Math.sign(h-a);if(e.team===m.home_abbr)h++;else a++;
   const now=Math.sign(h-a);const tags=[];
   if(e.type==="own_goal")tags.push("Own goal");
   if(e.type==="penalty_goal")tags.push("Penalty goal");
   if(A.eventOrder(e)>=8500)tags.push("Late goal");
   if(was!==now&&now!==0)tags.push("Go-ahead goal");
   if(was!==0&&now===0)tags.push("Equalizer");
   if(tags.length)moments.push({e,m,tags});
  }
 }
 moments.sort((a,b)=>b.m.date.localeCompare(a.m.date)||A.eventOrder(a.e)-A.eventOrder(b.e));
 el("moments").innerHTML=moments.map(({e,m,tags})=>'<div class="soccer-event"><div class="time">'+esc(e.minute)+"'"+'</div><div><b>'+esc(e.player)+'</b><div class="details">'+esc(tags.join(" · "))+' · '+esc(m.home_abbr)+' vs '+esc(m.away_abbr)+'</div></div><a href="'+link(m)+'">Match ↗</a></div>').join("")||warn("No notable scoring events logged.");
 if(location.hash==="#milestones")el('mainTabs').querySelector('[data-tab="milestones"]').click();
}
function goalsView(){
 app.innerHTML='<div class="eyebrow">Pro soccer · Every goal witnessed</div><h1>Goal history.</h1><p class="lead">Every goal from the three professional soccer matches you attended, including the own goal and late penalty.</p>'
 +metricCards([["Total goals",goals.length],["Matches",matches.length],["Individual goal scorers",new Set(goals.filter(x=>x.type!=="own_goal").map(x=>x.player)).size],["Penalties scored",goals.filter(x=>x.type==="penalty_goal").length]])
 +'<div class="soccer-panel"><div class="soccer-filters"><label>Show goals<select id="goalKind"><option value="all">All goals</option><option value="goal">Open-play / regular goals</option><option value="penalty_goal">Penalties</option><option value="own_goal">Own goals</option></select></label></div><div id="goalRows"></div></div>';
 const render=()=>{let k=el("goalKind").value;
 el("goalRows").innerHTML=goals.filter(e=>k==="all"||e.type===k).sort((a,b)=>b.m.date.localeCompare(a.m.date)||A.eventOrder(a)-A.eventOrder(b)).map(e=>'<div class="soccer-event"><span class="time">'+esc(e.minute)+"'"+'</span><div><b>'+A.scorerLabel(e)+'</b><div class="details">'+esc(e.team)+' · '+dt(e.m.date)+' · '+esc(e.m.home)+' vs '+esc(e.m.away)+'</div>'+(e.assist?'<div class="details">Assist: '+esc(e.assist)+'</div>':"")+'</div><a href="'+link(e.m)+'">Match ↗</a></div>').join("")||warn("No goals with this type.")};
 el("goalKind").addEventListener("change",render);render();
}
if(page==="home")overview();
else if(page==="games")gamesView();
else if(page==="stats")leaderboards();
else if(page==="player")profile();
else if(page==="records")records();
else if(page==="goals")goalsView();
});