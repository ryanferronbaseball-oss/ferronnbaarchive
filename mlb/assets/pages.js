document.addEventListener("DOMContentLoaded",async()=>{
"use strict";
const A=window.MLBArchive,app=document.getElementById("app"),el=id=>document.getElementById(id),page=document.body.dataset.page||"home";
const {esc,fmt,date,playerUrl,gameUrl,table,bar,tiles,record,mlbRow}=A;
el("navigation").innerHTML=A.nav(page);
let d;try{d=await A.load()}catch(err){app.innerHTML='<div class="empty">Unable to load attendance data: '+esc(err.message)+'</div>';return}
const {games,rows,players,scores,decisions}=d;
let careerHonors=null;
if(page==="hof"||page==="player"){
 try{const r=await fetch("./data/career_awards.json",{cache:"no-store"});
  if(!r.ok)throw Error("Career awards HTTP "+r.status);
  careerHonors=await r.json();
 }catch(error){console.warn("Career honors unavailable",error);}
}
const awardsById=careerHonors?.players||{};

const verified=games.filter(g=>g.game_pk!=null);
const sorted=games.slice().sort((a,b)=>b.date.localeCompare(a.date)||b.attendance_id-a.attendance_id);
const counts=(items)=>{let m=new Map();for(let s of items)m.set(s,(m.get(s)||0)+1);return [...m].sort((a,b)=>b[1]-a[1]||a[0].localeCompare(b[0]))};
const short=(s)=>esc(s||"—");
const linkPlayer=(p)=>'<a href="'+playerUrl(p)+'">'+esc(p.name)+'</a>';
const batting=(r)=>A.addStats(r,"batting"),pitching=(r)=>A.addStats(r,"pitching");
const playerRows=p=>[...p.batting,...p.pitching];
const bStats=players.map(p=>({p,stats:batting(p.batting)})).filter(x=>x.stats.games);
const pStats=players.map(p=>({p,stats:pitching(p.pitching)})).filter(x=>x.stats.games);
const sig=[
 ["Hits in a game","batting","hits","H"],
 ["Home runs in a game","batting","homeRuns","HR"],
 ["Strikeouts in a game","pitching","strikeOuts","SO"]
];
function perCategory(type,key){
 return rows.filter(r=>r[type]&&A.oneStat(r,type,key)>0).map(r=>({...r,value:A.oneStat(r,type,key)})).sort((a,b)=>b.value-a.value||a.date.localeCompare(b.date)||a.name.localeCompare(b.name));
}
function signature(){
 const cards=sig.map(([title,type,k,unit])=>{
  const list=perCategory(type,k),r=list[0],g=r?games.find(x=>x.game_pk===r.game_pk):null;
  if(!r)return record(title,"—","Waiting for official player game box scores");
  return '<article class="mlb-record"><small>'+title+'</small><div class="mlb-feature"><div class="mlb-avatar">'+esc(r.name.split(" ").map(x=>x[0]).slice(0,2).join(""))+'</div><div><strong>'+r.value+' '+unit+'</strong><div class="person"><a href="'+playerUrl(r)+'">'+esc(r.name)+'</a></div><p>'+date(r.date)+' · '+esc(r.team)+'</p></div></div>'+(g?'<a href="'+gameUrl(g)+'">View performance ↗</a>':'')+'</article>';
 });
 return cards.join("");
}
function cardStats(){
 const countPlayers=new Set(rows.map(r=>r.player_id)).size;
 return tiles([["Games attended",games.length],["Officially matched",verified.length],["Players imported",countPlayers],["Seasons represented",new Set(games.map(g=>g.date.slice(0,4))).size]]);
}
function searchWidget(id,historyOnly=false){
 const years=[...new Set(games.map(g=>g.date.slice(0,4)))].sort().reverse();
 const teams=[...new Set(games.flatMap(g=>[g.home,g.away]))].sort();
 return '<div class="mlb-filters"><label for="search">Find a game<input id="search" type="search" placeholder="Team, venue or year"></label>'
 +'<label for="yearFilter">Season<select id="yearFilter"><option value="">All seasons</option>'+years.map(y=>'<option>'+y+'</option>').join("")+'</select></label>'
 +'<label for="teamFilter">Team<select id="teamFilter"><option value="">All teams</option>'+teams.map(t=>'<option value="'+esc(t)+'">'+esc(t)+'</option>').join("")+'</select></label>'
 +'<label for="sort">Order<select id="sort"><option value="desc">Newest first</option><option value="asc">Oldest first</option></select></label></div>'
 +'<p id="showing" class="mlb-note"></p><div id="'+id+'"></div>';
}
function renderHistory(id){
 const draw=()=>{
 const text=el("search").value.trim().toLowerCase(),year=el("yearFilter").value,team=el("teamFilter").value,order=el("sort").value;
 const subset=games.filter(g=>(!year||g.date.startsWith(year))&&(!team||g.away===team||g.home===team)&&[g.date,g.away,g.home,g.ballpark].join(" ").toLowerCase().includes(text)).sort((a,b)=>order==="desc"?b.date.localeCompare(a.date)||b.attendance_id-a.attendance_id:a.date.localeCompare(b.date)||a.attendance_id-b.attendance_id);
 el("showing").textContent="Showing "+subset.length+" of "+games.length+" attended games.";
 el(id).innerHTML=table(["Date","Matchup","Ballpark","Final","Status","Game"],subset.map(mlbRow),"No attended games match these filters.");
 };
 for(const k of ["search","yearFilter","teamFilter","sort"])el(k).addEventListener("input",draw);draw();
}
function overview(){
 app.innerHTML='<div class="eyebrow">Major League Baseball · Personal attendance</div><h1>Your MLB history.</h1>'
 +'<p class="lead">A personal archive of every MLB game you witnessed, from 2003 through 2026. Explore box scores, player game logs, personal leaderboards and record-setting performances from those games.</p>'
 +cardStats()
 +'<div class="section-heading"><h2>Recently attended</h2><a class="action-link secondary" href="./game.html">All game box scores ↗</a></div><div class="game-grid">'+sorted.slice(0,3).map(A.gameCard).join("")+'</div>'
 +'<div class="section-heading"><h2>Signature Performances</h2><a class="action-link secondary" href="./records.html">View Records ↗</a></div>'
 +'<p class="mlb-note">Your strongest verified single-game performances—one game per record, not whole-season statistics.</p><div class="mlb-feature-grid">'+signature()+'</div>'
 +'<div class="mlb-charts"><section class="panel"><h2>Most Watched Teams</h2>'+bar(counts(games.flatMap(g=>[g.away,g.home])).slice(0,9))+'</section>'
 +'<section class="panel"><h2>Attendance by Year</h2>'+bar([...counts(games.map(g=>g.date.slice(0,4)))].sort((a,b)=>a[0].localeCompare(b[0])))+'</section></div>'
 +'<section class="panel"><h2>Ballpark history</h2>'+bar(counts(games.map(g=>g.ballpark)).slice(0,10))+'</section>'
 +'<section class="panel" id="gameHistorySection"><h2>My Game History</h2><p class="mlb-note">All '+games.length+' entries from your original attendance tracker. Official game IDs and box-score coverage are identified individually.</p>'+searchWidget("history")+'</section>';
 renderHistory("history");
}
function gamePage(){
 const id=new URLSearchParams(location.search).get("id");let selected=games.find(g=>String(g.attendance_id)===String(id))||sorted[0];
 app.innerHTML='<div class="eyebrow">MLB · Games & box scores</div><h1>Game details.</h1>'
 +'<p class="lead">Official MLB game results, inning scoring, batting, pitching, fielding, and scoring-play history where recorded.</p>'
 +'<div class="toolbar"><label class="filter-label" for="gameSelect">Attended game</label><select id="gameSelect">'+sorted.map(g=>'<option value="'+g.attendance_id+'">'+date(g.date)+' · '+esc(g.away)+' @ '+esc(g.home)+(g.game_pk!=null?" · "+g.away_score+"–"+g.home_score:" · Pending")+'</option>').join("")+'</select></div>'
 +'<section id="scoreboard"></section><div id="gameStats"></div>';
 const select=el("gameSelect");
 function render(g){
 selected=g;select.value=g.attendance_id;
 const confirmed=g.game_pk!=null;
 const gameStats=rows.filter(x=>x.game_pk===g.game_pk && g.game_pk!=null);
 let actual=confirmed&&A.yes(g.away_score)&&A.yes(g.home_score);
 const board='<div class="mlb-score"><div class="side">'+esc(g.away)+'</div><div class="final">'+(actual?g.away_score+' – '+g.home_score:'—')+'</div><div class="side">'+esc(g.home)+'</div></div>'
 +'<p class="mlb-note">'+date(g.date)+' · '+esc(g.ballpark)+(g.venue_official&&g.venue_official!==g.ballpark?' (official: '+esc(g.venue_official)+')':'')+' · '+(g.game_pk?'MLB game #'+g.game_pk:'Awaiting official game match')+'</p>';
 let innings="";
 if(g.innings?.length){
 const list=g.innings,th=list.map(i=>'<th>'+esc(i.inning)+'</th>').join("");
 const line=(team,label,total)=>'<tr><td>'+esc(label)+'</td>'+list.map(i=>'<td>'+A.disp(i[team]??"—",team)+'</td>').join("")+'<td><strong>'+esc(total)+'</strong></td></tr>';
 innings='<section class="panel"><h2>Line score by inning</h2><div class="table-wrap"><table class="mlb-innings"><thead><tr><th>Club</th>'+th+'<th>R</th></tr></thead><tbody>'+line("away",g.away,g.away_score)+line("home",g.home,g.home_score)+'</tbody></table></div></section>';
 }
 const officialDecision=decisions?.[String(g.game_pk)]||null;
 const decisionVerified=officialDecision?.status==="verified";
 const decisionPerson=(person,role)=>{
  if(!decisionVerified)return '<span class="mlb-decision-unavailable">Not verified</span>';
  if(!person)return '<span class="mlb-decision-unavailable">'+(role==="Save"?"No save":"Unavailable")+'</span>';
  return '<a class="mlb-decision-name" href="./player.html?id='+encodeURIComponent(person.id)+'">'+esc(person.name||"Player #"+person.id)+'</a>';
 };
 const decisionsPanel='<section class="panel mlb-decisions-panel" id="pitchingDecisions">'
  +'<div class="mlb-pregame-eyebrow">OFFICIAL MLB GAME DECISIONS</div><h2>Win, Loss & Save</h2>'
  +'<div class="mlb-decision-grid">'
  +[["WIN","Winner","winner"],["LOSS","Loser","loser"],["SAVE","Save","save"]].map(([short,label,key])=>
    '<div class="mlb-decision-card" data-decision="'+key+'"><span class="mlb-decision-type">'+short+'</span>'
    +'<div class="mlb-decision-role">'+label+'</div>'
    +decisionPerson(officialDecision?.[key],label)+'</div>').join("")
  +'</div><p class="mlb-note">Pitching decisions are the official win, loss and save credits, not selections from the impact ranking.</p></section>';
 const standout=A.playerOfGame(gameStats);
 const playerCard=standout?(()=>{
  const r=standout.row,photoId=encodeURIComponent(r.player_id);
  const fallback=esc(String(r.name||"").split(/\s+/).map(x=>x[0]).slice(0,2).join("").toUpperCase());
  const image='<img alt="" src="https://img.mlbstatic.com/mlb-photos/image/upload/w_213,q_85/v1/people/'+photoId+'/headshot/67/current"'
    +' onerror="this.style.display=\'none\';this.parentElement.textContent=\''+fallback+'\'">';
  return '<div class="mlb-potg-body"><div class="mlb-potg-portrait">'+image+'</div><div class="mlb-potg-info">'
    +'<div class="mlb-potg-category">'+esc(standout.role)+' · '+esc(r.team)+'</div>'
    +'<h3><a href="'+playerUrl(r)+'">'+esc(r.name)+'</a></h3>'
    +'<div class="mlb-potg-statline">'+esc(standout.line)+'</div>'
    +'<div class="mlb-potg-impact"><strong>'+standout.score.toFixed(1)+'</strong><span>Impact Score</span></div>'
    +'<a href="'+playerUrl(r)+'" class="mlb-potg-profile">View player profile ↗</a></div></div>';
 })():'<div class="empty">No verified player statistics are available for this game.</div>';
 const potgPanel='<section class="panel mlb-potg-panel" id="playerOfGame">'
  +'<div class="mlb-pregame-eyebrow">SIGNATURE PERFORMANCE</div><h2>Player of the Game</h2>'
  +playerCard
  +'<p class="mlb-note">Custom, unofficial one-player impact rating. Hitting rewards total bases, runs, RBI, walks and steals; pitching rewards innings and strikeouts while penalizing runs, hits and walks. Both are compared on one scale, regardless of winning team.</p></section>';
 el("scoreboard").innerHTML=board+decisionsPanel+potgPanel+innings;
 const order=[["batting","Batting"],["pitching","Pitching"],["fielding","Fielding"]];
 el("gameStats").innerHTML='<div class="mlb-nav-tabs" role="tablist">'+order.map(([c,title],i)=>'<button type="button" role="tab" aria-selected="'+(i===0)+'" data-cat="'+c+'">'+title+'</button>').join("")+'</div><section class="panel"><h2 id="statTitle">Batting box score</h2><div id="box"></div></section><section class="panel"><h2>Scoring plays</h2><div id="scoring"></div></section>'
 +'<p class="mlb-note">Official data: '+(confirmed?'<a target="_blank" rel="noopener" href="'+esc(g.source_url||"https://www.mlb.com/gameday/"+g.game_pk)+'">MLB game record ↗</a>':'Unmatched attendance entry. No player statistics are invented.')+'</p>';
 const panels=el("gameStats"),box=el("box");
 function show(category){
 panels.querySelectorAll("[data-cat]").forEach(b=>b.setAttribute("aria-selected",String(b.dataset.cat===category)));
 el("statTitle").textContent=category.charAt(0).toUpperCase()+category.slice(1)+" box score";
 const fields=category==="batting"?["atBats","runs","hits","doubles","triples","homeRuns","rbi","baseOnBalls","strikeOuts"]:category==="pitching"?["inningsPitched","hits","earnedRuns","baseOnBalls","strikeOuts","homeRuns","numberOfPitches"]:["putOuts","assists","errors"];
 const data=gameStats.filter(r=>category==="batting"?(r.batting_slot!=null||(r.batting&&A.num(r.batting.plateAppearances)+A.num(r.batting.atBats)>0)):(r[category]&&Object.keys(r[category]).length));
 const sortTeam=(a,b)=>{
  if(category==="pitching"){
   return (a.pitching_appearance_index??999)-(b.pitching_appearance_index??999)||a.name.localeCompare(b.name);
  }
  return (a.batting_slot??999)-(b.batting_slot??999)
    ||(a.batting_sub_index??999)-(b.batting_sub_index??999)
    ||(a.batter_appearance_index??999)-(b.batter_appearance_index??999)
    ||a.name.localeCompare(b.name);
 };
 const sideTable=(side,teamName)=>{
  const members=data.filter(r=>r.side===side||(!r.side&&r.team===teamName)).slice().sort(sortTeam);
  const numbered=category==="batting"||category==="pitching";
  const rowsByTeam=members.map(r=>{
   const isSub=category==="batting"&&r.batting_sub_index!=null&&r.batting_sub_index>0;
   const spot=category==="batting"?(r.batting_slot??"—"):null;
   // Official lineup slots run 1–9. Pitchers use the MLB gamebook's
   // appearance array: starting pitcher #1, relievers #2, #3, etc.
   const orderNumber=category==="batting"?(spot==="—"?"—":isSub?"↳":String(spot))
     :category==="pitching"?(r.pitching_appearance_index==null?"—":String(r.pitching_appearance_index+1)):null;
   const subtitle=esc(r.position||"")+(isSub?" · entered batting slot "+spot:"");
   return '<tr class="mlb-lineup-row'+(isSub?' mlb-substitute':'')+'" data-player-id="'+esc(r.player_id)+'"'
    +(category==="batting"?' data-slot="'+esc(spot)+'" data-sub="'+(r.batting_sub_index??0)+'"':'')
    +(category==="pitching"?' data-pitcher-index="'+(r.pitching_appearance_index??"")+'"':'')+'>'
    +(numbered?'<td class="mlb-order" data-order="'+esc(orderNumber)+'">'+esc(orderNumber)+'</td>':"")
    +'<td><a href="'+playerUrl(r)+'">'+esc(r.name)+'</a><small>'+subtitle+'</small></td>'
    +fields.map(k=>'<td>'+esc(A.disp(r[category]?.[k],k))+'</td>').join("")+'</tr>';
  });
  const note=category==="batting"?"Official batting order · ↳ denotes a replacement in that lineup spot"
    :category==="pitching"?"Official appearance order · #1 starting pitcher, followed by relief pitchers":"Fielders grouped by lineup spot where applicable";
  return '<section class="mlb-team-box" data-side="'+side+'" data-category="'+category+'"><div class="mlb-team-heading"><h3>'+esc(teamName)+'</h3><span>'+esc(side==="away"?"AWAY":"HOME")+'</span></div>'
    +'<p class="mlb-team-caption">'+note+'</p>'
    +table([...(numbered?["Order"]:[]),"Player",...fields.map(k=>A.abbr[k]||k)],rowsByTeam,
       "No verified "+category+" entries for "+teamName+".")+'</section>';
 };
 box.innerHTML=sideTable("away",g.away)+sideTable("home",g.home);
 }
 panels.querySelectorAll("[data-cat]").forEach(b=>b.addEventListener("click",()=>show(b.dataset.cat)));show("batting");
 const scoring=scores[String(g.game_pk)]||[];
 el("scoring").innerHTML=scoring.length?'<div class="scoring-list">'+scoring.map(p=>'<div class="play"><div class="play-time">'+esc(p.half==="top"?"Top":"Bot")+' '+esc(p.inning)+'</div><div><div class="play-label">'+esc(p.event||"Scoring play")+'</div><div class="play-description">'+esc(p.description)+'</div></div></div>').join("")+'</div>':'<div class="empty">Full scoring-play chronology is not available for this game yet. See the inning line score and official box score.</div>';
 document.title=esc(g.away)+" at "+esc(g.home)+" · "+g.date+" | MLB Archive";
 }
 select.addEventListener("change",()=>{const g=games.find(x=>String(x.attendance_id)===select.value);if(g){history.replaceState(null,"",gameUrl(g));render(g)}});
 render(selected);
}
const bKeys=[["Games","games"],["Plate appearances","plateAppearances"],["At-bats","atBats"],["Hits","hits"],["Home runs","homeRuns"],["RBI","rbi"],["Runs","runs"],["Doubles","doubles"],["Triples","triples"],["Walks","baseOnBalls"],["Strikeouts","strikeOuts"],["Stolen bases","stolenBases"],["Average","average"],["OBP","onBasePercentage"],["SLG","sluggingPercentage"],["OPS","ops"]];
const pKeys=[["Games","games"],["Outs recorded","outs"],["Strikeouts","strikeOuts"],["Innings pitched","inningsPitched"],["ERA","era"],["WHIP","whip"],["K/9","k9"],["Earned runs","earnedRuns"],["Walks","baseOnBalls"],["Hits allowed","hits"],["Wins","wins"],["Saves","saves"]];
function leaderTable(type,key,scope,search){
 const source=(type==="batting"?bStats:pStats).filter(x=>!search||x.p.name.toLowerCase().includes(search));
 const active=source.filter(x=>x.stats[key]!=null&&(typeof x.stats[key]!=="number"||x.stats[key]>0));
 const asc=["era","whip"].includes(key),rank=active.slice().sort((a,b)=>{const n=a.stats[key],m=b.stats[key];return (asc?Number(n)-Number(m):Number(m)-Number(n))||a.p.name.localeCompare(b.p.name)});
 return table(["Rank","Player","Club(s)","Games",type==="batting"?"H":"SO",type==="batting"?"HR":"IP",key],rank.slice(0,scope).map((x,i)=>'<tr><td>'+(i+1)+'</td><td>'+linkPlayer(x.p)+'</td><td>'+esc(x.p.teams.join(", "))+'</td><td>'+x.stats.games+'</td><td>'+x.stats[type==="batting"?"hits":"strikeOuts"]+'</td><td>'+esc(A.disp(x.stats[type==="batting"?"homeRuns":"inningsPitched"],""))+'</td><td><strong>'+esc(A.disp(x.stats[key],key))+'</strong></td></tr>'),"No verified player statistics currently qualify.");
}
function statsPage(){
 app.innerHTML='<div class="eyebrow">MLB · Player statistics</div><h1>Players & leaderboards.</h1><p class="lead">Find the major-league players you have watched, with statistics aggregated only from games you personally attended.</p>'
 +tiles([["Unique MLB players",players.length],["Matched games",verified.length],["Batter records",bStats.length],["Pitcher records",pStats.length]])
 +'<div class="mlb-filters"><label for="category">Statistical group<select id="category"><option value="batting">Batting</option><option value="pitching">Pitching</option></select></label><label for="stat">Leaderboard statistic<select id="stat"></select></label><label for="query">Find a player<input type="search" id="query" placeholder="Search a player name"></label><label for="limit">Show<select id="limit"><option>25</option><option>50</option><option>100</option><option>1000</option></select></label></div>'
 +'<section class="panel"><h2 id="boardHeading"></h2><p class="mlb-note">Aggregate counting statistics include only imported attended games. Rate statistics are recomputed from underlying totals.</p><div id="board"></div></section>';
 const cat=el("category"),stat=el("stat");
 const change=()=>{const keys=cat.value==="batting"?bKeys:pKeys;stat.innerHTML=keys.map(([label,k])=>'<option value="'+k+'">'+label+'</option>').join("");stat.value=cat.value==="batting"?"hits":"strikeOuts";draw()};
 const draw=()=>{let k=stat.value,label=(cat.value==="batting"?bKeys:pKeys).find(x=>x[1]===k)?.[0];el("boardHeading").textContent=label+" · "+(cat.value==="batting"?"Batting":"Pitching");el("board").innerHTML=leaderTable(cat.value,k,Number(el("limit").value),el("query").value.trim().toLowerCase())};
 cat.addEventListener("change",change);["stat","query","limit"].forEach(x=>el(x).addEventListener("input",draw));change();
}
function profilePage(){
 const id=new URLSearchParams(location.search).get("id"),p=players.find(x=>String(x.player_id)===String(id));
 if(!p){app.innerHTML='<div class="eyebrow">MLB · Player profile</div><h1>Player not found.</h1><p class="lead">This player has not yet appeared in an officially imported attendance-game box score.</p><a class="action-link" href="./stats.html">All players ↗</a>';return}
 const bs=batting(p.batting),ps=pitching.length?pitching(p.pitching):null;
 const career=awardsById[String(p.player_id)]||null;
 const hof=career?.hall_of_fame||null;
 const honorCategories=[["mvp","MVP","mvp"],["cy_young","Cy Young","cy"],["gold_glove","Gold Glove","gg"],["silver_slugger","Silver Slugger","ss"]];
 const hasHonors=!!(hof||honorCategories.some(([key])=>career?.[key]?.length));
 const honorBadges=hasHonors?'<div class="mlb-accolades" aria-label="Career honors">'
   +(hof?'<a class="mlb-accolade hof" href="./hall-of-fame.html">★ Hall of Fame · '+hof.year+'</a>':"")
   +honorCategories.filter(([key])=>career?.[key]?.length).map(([key,label,theme])=>'<a href="#careerHonors" class="mlb-accolade '+theme+'" data-honor-link="'+key+'">'+esc(label)+' · '+career[key].length+'</a>').join("")
   +'</div>':"";
 const honorTabs=[...(hof?[["hall_of_fame","Hall of Fame"]]:[]),...honorCategories.map(([k,name])=>[k,name])];
 const firstHonor=honorTabs.find(([k])=>k==="hall_of_fame"?!!hof:!!career?.[k]?.length)?.[0]||"mvp";
 const honorPanel=hasHonors?'<section class="panel mlb-honors-panel" id="careerHonors">'
  +'<h2>Career Awards & Honors</h2><p class="mlb-note">Career honors, including awards won outside seasons or games you personally attended. Official MLB award recipients only.</p>'
  +'<div class="mlb-nav-tabs" id="honorTabs" role="tablist" aria-label="Career award categories">'
  +honorTabs.map(([k,label])=>'<button type="button" role="tab" data-honor="'+k+'" aria-controls="honor-'+k+'" aria-selected="'+(k===firstHonor)+'">'+esc(label)+(k==="hall_of_fame"?"":' ('+(career?.[k]?.length||0)+')')+'</button>').join("")+'</div>'
  +honorTabs.map(([k,label])=>{
   const inducted=k==="hall_of_fame",entries=inducted?(hof?[{year:hof.year}]:[]):career?.[k]||[];
   const detail=entries.length?(inducted?
    '<p>Inducted into the National Baseball Hall of Fame in '+hof.year+'. <a href="./hall-of-fame.html">Other Hall of Famers you have seen ↗</a></p>':
    '<p>'+entries.length+' verified career '+esc(label)+' '+(entries.length===1?"award":"awards")+'.</p>'):
    '<p>No verified career '+esc(label)+' awards.</p>';
   return '<div class="mlb-honor-detail" role="tabpanel" id="honor-'+k+'"'+(k===firstHonor?"":" hidden")+'><strong>'+esc(label)+'</strong>'+detail
    +(entries.length?'<div class="mlb-honor-tags">'+entries.map(a=>'<span class="mlb-honor-year">'+(a.league?esc(a.league)+" ":"")+a.year+(a.notes?" · "+esc(a.notes):"")+'</span>').join("")+'</div>':"")
    +'</div>';
  }).join("")
  +'<p class="mlb-note"><a target="_blank" rel="noopener" href="https://statsapi.mlb.com/api/v1/awards">Source: MLB official awards history ↗</a></p></section>':"";
 app.innerHTML='<div class="eyebrow">MLB · Player profile</div><div class="mlb-profile-head"><div class="mlb-portrait"><img alt="" src="https://img.mlbstatic.com/mlb-photos/image/upload/w_213,q_85/v1/people/'+esc(p.player_id)+'/headshot/67/current" onerror="this.style.display=\'none\';this.parentElement.textContent=\''+esc(p.name.split(" ").map(x=>x[0]).slice(0,2).join(""))+'\'"></div><div><h1>'+esc(p.name)+'</h1>'+honorBadges+'<p class="lead">'+esc(p.teams.join(" / "))+' · '+p.game_count+' attended games with player statistics</p></div></div>'
 +tiles([["Games",p.game_count],["Hits",bs.hits],["Home runs",bs.homeRuns],["Pitching SO",ps?.strikeOuts||0]])+honorPanel
 +'<section class="panel"><h2>Batting from games you attended</h2><div class="mlb-records-grid">'+["atBats","hits","homeRuns","rbi","baseOnBalls","strikeOuts","average","onBasePercentage","sluggingPercentage","ops"].map(k=>record(A.abbr[k]||k,A.disp(bs[k],k),"")).join("")+'</div></section>'
 +(ps?'<section class="panel"><h2>Pitching from games you attended</h2><div class="mlb-records-grid">'+["inningsPitched","strikeOuts","era","whip","wins","losses"].map(k=>record(A.abbr[k]||k,A.disp(ps[k],k),"")).join("")+'</div></section>':'')
 +'<section class="panel"><h2>Individual game logs</h2><div class="mlb-nav-tabs"><button type="button" role="tab" data-side="batting" aria-selected="true">Batting</button><button type="button" role="tab" data-side="pitching" aria-selected="false">Pitching</button></div><div id="logs"></div></section>';
 function logs(type){
 el("app").querySelectorAll("[data-side]").forEach(b=>b.setAttribute("aria-selected",String(b.dataset.side===type)));
 let entries=p[type].slice().sort((a,b)=>b.date.localeCompare(a.date));
 const keys=type==="batting"?["atBats","runs","hits","homeRuns","rbi","baseOnBalls","strikeOuts"]:["inningsPitched","hits","earnedRuns","baseOnBalls","strikeOuts"];
 el("logs").innerHTML=table(["Date","Team","Opponent",...keys.map(k=>A.abbr[k]||k)],entries.map(r=>{let g=games.find(x=>x.game_pk===r.game_pk);let opponent=g?(r.team_id===(g.mlb_home_team_id??-1)?g.away:g.home):"";return '<tr><td><a href="'+gameUrl(g||{attendance_id:r.attendance_id})+'">'+date(r.date)+'</a></td><td>'+esc(r.team)+'</td><td>'+esc(g?g.away+" @ "+g.home:"")+'</td>'+keys.map(k=>'<td>'+esc(A.disp(r[type][k],k))+'</td>').join("")+'</tr>'}),"No verified "+type+" game lines.");
 }
 if(hasHonors){
  const showHonor=key=>{
   app.querySelectorAll("#honorTabs [data-honor]").forEach(btn=>btn.setAttribute("aria-selected",String(btn.dataset.honor===key)));
   app.querySelectorAll(".mlb-honor-detail").forEach(panel=>panel.hidden=panel.id!=="honor-"+key);
  };
  app.querySelectorAll("#honorTabs [data-honor]").forEach(btn=>btn.addEventListener("click",()=>showHonor(btn.dataset.honor)));
  app.querySelectorAll("[data-honor-link]").forEach(a=>a.addEventListener("click",()=>showHonor(a.dataset.honorLink)));
 }
 app.querySelectorAll("[data-side]").forEach(b=>b.addEventListener("click",()=>logs(b.dataset.side)));logs("batting");document.title=p.name+" | MLB Courtside Archive";
}

function hofPage(){
 const hall=players.filter(p=>awardsById[String(p.player_id)]?.hall_of_fame).map(p=>{
  const induction=awardsById[String(p.player_id)].hall_of_fame;
  const seasonStats=batting(p.batting),pitchStats=pitching(p.pitching);
  const seen=games.filter(g=>p.games.has(g.game_pk)).sort((a,b)=>b.date.localeCompare(a.date));
  return {p,induction,seen,seasonStats,pitchStats};
 }).sort((a,b)=>b.seen.length-a.seen.length||a.p.name.localeCompare(b.p.name));
 const totals=hall.reduce((acc,x)=>acc+x.seen.length,0);
 const uniqueGames=new Set(hall.flatMap(x=>x.seen.map(g=>g.game_pk))).size;
 const teams=[...new Set(hall.flatMap(x=>x.p.teams))].sort();
 app.innerHTML='<div class="eyebrow">MLB · Legacy and recognition</div>'
  +'<h1>Hall of Famers you\'ve seen.</h1>'
  +'<p class="lead">Every inducted National Baseball Hall of Fame player who appeared in the '+games.length+' MLB games you attended. Career induction honors; all batting, pitching and game counts below reflect only your personally witnessed games.</p>'
  +'<div class="mlb-hof-summary">'
  +[['Hall of Famers seen',hall.length],['Combined appearances',totals],['Games featuring inductees',uniqueGames]]
    .map(([label,value])=>'<div class="metric"><strong>'+value+'</strong><small>'+esc(label)+'</small></div>').join("")+'</div>'
  +'<div class="mlb-hof-toolbar"><input id="hofSearch" type="search" placeholder="Search Hall of Famers or clubs…" aria-label="Search Hall of Famers">'
  +'<select id="hofSort" aria-label="Sort Hall of Fame cards"><option value="games">Most games seen</option><option value="year">Induction year</option><option value="name">Player name</option></select>'
  +'<select id="hofTeam" aria-label="Filter Hall of Famers by team"><option value="">All teams</option>'
  +teams.map(t=>'<option value="'+esc(t)+'">'+esc(t)+'</option>').join("")+'</select></div>'
  +'<p class="mlb-hof-count" id="hofShowing"></p><section class="mlb-hof-grid" id="hofGrid"></section>'
  +'<p class="mlb-note">Hall of Fame classes are matched by exact MLB player ID to official Hall Of Fame induction records. A player can have been inducted after you saw them. Only actual National Baseball Hall of Fame inductees are counted, not nominees or future candidates. '
  +'<a href="https://www.mlb.com/news/hall-of-fame-inductions-by-year" target="_blank" rel="noopener">Official induction history ↗</a></p>';
 const card=m=>{
  const p=m.p,record=m.induction;
  const portrait='<div class="mlb-hof-portrait"><img loading="lazy" alt="" src="https://img.mlbstatic.com/mlb-photos/image/upload/w_213,q_85/v1/people/'+encodeURIComponent(p.player_id)+'/headshot/67/current" onerror="this.style.display=\'none\';this.parentNode.textContent=\''+esc(p.name.split(" ").map(s=>s[0]).slice(0,2).join(""))+'\'"></div>';
  const lastStat=p.pitching.length>p.batting.length?
    ['Ks witnessed',m.pitchStats.strikeOuts]:['Hits witnessed',m.seasonStats.hits];
  return '<article class="mlb-hof-card" data-player-id="'+p.player_id+'">'
   +'<div class="mlb-hof-head">'+portrait+'<div class="mlb-hof-title">'
   +'<span class="mlb-hof-badge">★ HALL OF FAME</span>'
   +'<h2><a href="'+playerUrl(p)+'">'+esc(p.name)+'</a></h2>'
   +'<div class="mlb-hof-meta">Class of '+record.year+' · '+esc(p.teams.join(" / "))+'</div></div></div>'
   +'<div class="mlb-hof-figures">'
   +[['Games you attended',m.seen.length],['Hall of Fame class',record.year],lastStat]
   .map(([label,value])=>'<div class="mlb-hof-figure"><strong>'+esc(value)+'</strong><small>'+esc(label)+'</small></div>').join("")+'</div>'
   +'<div class="mlb-hof-games"><strong>Games you witnessed</strong>'
   +m.seen.slice(0,7).map(g=>'<a href="'+gameUrl(g)+'">'+date(g.date)+' · '+esc(g.away)+' at '+esc(g.home)+'</a>').join("")
   +(m.seen.length>7?'<span class="mlb-hof-meta">And '+(m.seen.length-7)+' more on the player profile</span>':"")+'</div>'
   +'<div class="mlb-hof-links"><a href="'+playerUrl(p)+'">Player profile ↗</a><a target="_blank" rel="noopener" href="https://baseballhall.org/hall-of-fame">Cooperstown ↗</a></div></article>';
 };
 const render=()=>{
  const q=el("hofSearch").value.trim().toLowerCase(),sort=el("hofSort").value,team=el("hofTeam").value;
  const matched=hall.filter(x=>(!team||x.p.teams.includes(team))&&
   (!q||x.p.name.toLowerCase().includes(q)||x.p.teams.join(" ").toLowerCase().includes(q)));
  matched.sort((a,b)=>sort==="name"?a.p.name.localeCompare(b.p.name):
   sort==="year"?a.induction.year-b.induction.year||a.p.name.localeCompare(b.p.name):
   b.seen.length-a.seen.length||a.p.name.localeCompare(b.p.name));
  el("hofShowing").textContent="Showing "+matched.length+" of "+hall.length+" inducted players from your game history.";
  el("hofGrid").innerHTML=matched.length?matched.map(card).join(""):'<div class="mlb-hof-empty">No Hall of Famers match these filters.</div>';
 };
 for(const id of ["hofSearch","hofSort","hofTeam"])el(id).addEventListener("input",render);
 render();
}

const recDefs=[
 ["Hits","batting","hits"],["Home runs","batting","homeRuns"],["RBI","batting","rbi"],
 ["Stolen bases","batting","stolenBases"],["Pitching strikeouts","pitching","strikeOuts"],["Pitching outs","pitching","outs"],
 ["Doubles","batting","doubles"],["Walks","batting","baseOnBalls"],["Runs","batting","runs"]
];
function ranking(type,key,top=10,filter=0){
 return rows.filter(r=>r[type]&&A.oneStat(r,type,key)>=filter&&(A.oneStat(r,type,key)>0)).map(r=>({...r,value:A.oneStat(r,type,key)})).sort((a,b)=>b.value-a.value||a.date.localeCompare(b.date)||a.name.localeCompare(b.name)).slice(0,top);
}
function rankingTable(list,title){
 return table(["Rank","Player","Club","Date",title,"Game"],list.map((r,i)=>{const g=games.find(x=>x.game_pk===r.game_pk);return '<tr><td>'+(i+1)+'</td><td><a href="'+playerUrl(r)+'">'+esc(r.name)+'</a></td><td>'+esc(r.team)+'</td><td>'+date(r.date)+'</td><td><strong>'+r.value+'</strong></td><td>'+(g?'<a href="'+gameUrl(g)+'">Game ↗</a>':'—')+'</td></tr>'}),"No verified qualifying single-game performances.");
}
function recordsPage(){
 app.innerHTML='<div class="eyebrow">MLB · Your personal record book</div><h1>The best I\'ve witnessed.</h1><p class="lead">Official game-level records, milestones, team achievements and legendary performances from your attended MLB history.</p>'
 +'<div class="mlb-nav-tabs" id="mainTabs" role="tablist">'+[["records","Record Book"],["milestones","Milestones"],["teams","Team & Game Records"],["legendary","Legendary Performances"]].map(([k,l],i)=>'<button type="button" role="tab" data-tab="'+k+'" aria-selected="'+(i===0)+'">'+l+'</button>').join("")+'</div>'
 +'<section class="mlb-tab" id="recordsTab"><h2>Single-game record holders</h2><div id="recordCards" class="mlb-records-grid"></div><section class="panel"><h2>Top 10 single-game performances</h2><div class="mlb-filters"><label for="recordCategory">Statistic<select id="recordCategory">'+recDefs.map(([l,t,k])=>'<option value="'+t+":"+k+'">'+l+'</option>').join("")+'</select></label></div><div id="recordTop"></div></section></section>'
 +'<section class="mlb-tab" id="milestonesTab" hidden><section class="panel"><h2>Statistical milestones</h2><p class="mlb-note">Each threshold includes every qualifying individual game. Switch to player frequency for repeats.</p><div class="mlb-filters"><label>Milestone<select id="milestoneStat">'+[["3+ hits","batting:hits:3"],["4+ hits","batting:hits:4"],["2+ home runs","batting:homeRuns:2"],["3+ RBI","batting:rbi:3"],["2+ stolen bases","batting:stolenBases:2"],["8+ pitcher Ks","pitching:strikeOuts:8"],["10+ pitcher Ks","pitching:strikeOuts:10"],["7+ innings (21 outs)","pitching:outs:21"]].map(([name,v])=>'<option value="'+v+'">'+name+'</option>').join("")+'</select></label><label>View<select id="milestoneView"><option value="games">Player-games</option><option value="players">Player frequency</option></select></label></div><div id="milestoneMetrics"></div><div id="milestoneTable"></div></section></section>'
 +'<section class="mlb-tab" id="teamsTab" hidden><h2>Team & Game Records</h2><div class="mlb-records-grid" id="teamCards"></div><section class="panel"><h2>Every officially matched game</h2><div id="teamGameTable"></div></section></section>'
 +'<section class="mlb-tab" id="legendaryTab" hidden><section class="panel"><h2>Statistical Feats</h2><p class="mlb-note">Achievements grounded in official individual game lines, not subjective awards.</p><div id="feats"></div></section><section class="panel"><h2>Iconic Moments</h2><p class="mlb-note">High-scoring games, extra innings, complete games and memorable confirmed achievements.</p><div id="moments"></div></section></section>'
 +'<p class="mlb-note">Coverage: '+verified.length+' of '+games.length+' attended games matched to official MLB IDs. Rankings expand as historical box scores are verified; missing player statistics are never counted as zero.</p>';
 el("mainTabs").addEventListener("click",e=>{let button=e.target.closest("[data-tab]");if(!button)return;el("mainTabs").querySelectorAll("button").forEach(b=>b.setAttribute("aria-selected",String(b===button)));["records","milestones","teams","legendary"].forEach(k=>el(k+"Tab").hidden=k!==button.dataset.tab)});
 const first=recDefs.slice(0,6);
 el("recordCards").innerHTML=first.map(([label,type,k])=>{let r=ranking(type,k,1)[0];const g=r?games.find(x=>x.game_pk===r.game_pk):null;return record("Most "+label.toLowerCase(),r?r.value:"—",r?r.name+" · "+date(r.date):"Awaiting verified player box scores",g?gameUrl(g):null)}).join("");
 function rec(){const [type,k]=el("recordCategory").value.split(":");el("recordTop").innerHTML=rankingTable(ranking(type,k),recDefs.find(x=>x[1]===type&&x[2]===k)?.[0]||k)}
 el("recordCategory").addEventListener("change",rec);rec();
 function milestone(){let [type,k,threshold]=el("milestoneStat").value.split(":"),all=ranking(type,k,10000,Number(threshold));
 el("milestoneMetrics").innerHTML=tiles([["Qualifying player-games",all.length],["Unique players",new Set(all.map(r=>r.player_id)).size],["Covered games",new Set(rows.map(x=>x.game_pk)).size],["Games attended",games.length]]);
 if(el("milestoneView").value==="games"){el("milestoneTable").innerHTML=rankingTable(all,k);return}
 let group=new Map();for(const r of all){let id=String(r.player_id),item=group.get(id)||{r,count:0};item.count++;group.set(id,item)}
 const g=[...group.values()].sort((a,b)=>b.count-a.count||a.r.name.localeCompare(b.r.name));
 el("milestoneTable").innerHTML=table(["Player","Times reached","Profile"],g.map(x=>'<tr><td><a href="'+playerUrl(x.r)+'">'+esc(x.r.name)+'</a></td><td>'+x.count+'</td><td><a href="'+playerUrl(x.r)+'">View ↗</a></td></tr>'),"No players meet this threshold.");
 }
 ["milestoneStat","milestoneView"].forEach(x=>el(x).addEventListener("change",milestone));milestone();
 const complete=verified.filter(g=>A.yes(g.away_score)&&A.yes(g.home_score));
 const byRuns=complete.slice().sort((a,b)=>(b.away_score+b.home_score)-(a.away_score+a.home_score));
 const byDiff=complete.slice().sort((a,b)=>Math.abs(b.away_score-b.home_score)-Math.abs(a.away_score-a.home_score));
 const extra=complete.filter(g=>g.innings?.length>9);
 const bestRuns=byRuns[0],bestDiff=byDiff[0];
 el("teamCards").innerHTML=[
  record("Most combined runs",bestRuns?bestRuns.away_score+bestRuns.home_score:"—",bestRuns?bestRuns.away+" vs "+bestRuns.home:"No official scores verified",bestRuns?gameUrl(bestRuns):null),
  record("Largest final run margin",bestDiff?Math.abs(bestDiff.away_score-bestDiff.home_score):"—",bestDiff?bestDiff.away+" vs "+bestDiff.home:"Pending",bestDiff?gameUrl(bestDiff):null),
  record("Extra-inning games",extra.length,"Among officially verified scores"),
  record("Longest attended game",extra.length?Math.max(...extra.map(g=>g.innings.length))+" innings":"—","Official line scores only"),
  record("One-run games",complete.filter(g=>Math.abs(g.home_score-g.away_score)===1).length,"Completed matched games"),
  record("Shutout games",complete.filter(g=>g.home_score===0||g.away_score===0).length,"Completed matched games")
 ].join("");
 el("teamGameTable").innerHTML=table(["Date","Matchup","Ballpark","Final","Status","Game"],complete.slice().sort((a,b)=>b.date.localeCompare(a.date)).map(mlbRow));
 const feats=[];
 for(const [type,k,threshold,label] of [["batting","hits",4,"Four-hit game"],["batting","homeRuns",2,"Multi-home-run game"],["batting","rbi",5,"Five-RBI game"],["pitching","strikeOuts",10,"Double-digit Ks"],["pitching","outs",27,"Nine full innings pitched"]]){
 for(const r of ranking(type,k,10000,threshold)){feats.push({label,r})}
 }
 feats.sort((a,b)=>b.r.date.localeCompare(a.r.date));
 el("feats").innerHTML=feats.length?table(["Achievement","Player","Date","Value","Game"],feats.map(({label,r})=>{let g=games.find(x=>x.game_pk===r.game_pk);return '<tr><td>'+esc(label)+'</td><td><a href="'+playerUrl(r)+'">'+esc(r.name)+'</a></td><td>'+date(r.date)+'</td><td>'+r.value+'</td><td>'+(g?'<a href="'+gameUrl(g)+'">Game ↗</a>':'—')+'</td></tr>'}),"No achievements recorded yet."):'<div class="empty">No verified qualifying statistical feats yet.</div>';
 el("moments").innerHTML=table(["Date","Match","Highlight","Score","Game"],complete.slice().sort((a,b)=>(b.away_score+b.home_score)-(a.away_score+a.home_score)).slice(0,25).map(g=>'<tr><td>'+date(g.date)+'</td><td>'+esc(g.away)+' @ '+esc(g.home)+'</td><td>'+esc((g.innings?.length||9)>9?"Extra innings":g.home_score===0||g.away_score===0?"Shutout":"High-scoring / attended game")+'</td><td>'+g.away_score+'–'+g.home_score+'</td><td><a href="'+gameUrl(g)+'">Game ↗</a></td></tr>'));
 if(location.hash==="#milestones")app.querySelector('[data-tab="milestones"]').click();
}
if(page==="home")overview();else if(page==="games")gamePage();else if(page==="players")statsPage();else if(page==="player")profilePage();else if(page==="records")recordsPage();else if(page==="hof")hofPage();
});