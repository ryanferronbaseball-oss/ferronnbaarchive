/* Courtside NHL archive: witnessed-game data only. Unverified skater boxes remain unpopulated. */
(()=>{'use strict';
 const $=id=>document.getElementById(id);
 const esc=x=>String(x??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
 const fmt=d=>new Date(d+'T12:00:00Z').toLocaleDateString('en-US',{month:'long',day:'numeric',year:'numeric',timeZone:'UTC'});
 const stat=(x,dash='—')=>x===null||x===undefined?dash:esc(x);
 const page=document.body.dataset.page||'overview';
 const navItems=[['index.html','Overview','overview'],['game.html','Games','game'],['stats.html','Players','stats'],['records.html','Records','records'],['coaches.html','Coaches','coaches']];
 const nav=navItems.map(([href,name,key])=>'<a href="./'+href+'"'+(page===key?' aria-current="page"':'')+'>'+name+'</a>').join('')+'<a href="../index.html">All archives ↗</a>';
 $('navigation').innerHTML='<div class="nhl-topbar"><a href="./index.html" class="nhl-logo"><span class="nhl-mark">CA</span><span>COURTSIDE ARCHIVE<small>EVERY GAME HAS A STORY · NHL</small></span></a><nav aria-label="NHL navigation">'+nav+'</nav></div>';
 const sourceLinks=g=>(g.source_urls||[]).map((url,i)=>'<a href="'+esc(url)+'" target="_blank" rel="noopener noreferrer">Source '+(i+1)+' ↗</a>').join(' · ');
 const box=(value,label)=>'<div class="nhl-stat"><strong>'+stat(value)+'</strong><small>'+esc(label)+'</small></div>';
 const linkGame=g=>'./game.html?id='+encodeURIComponent(g.id);
 const linkPlayer=p=>'./player.html?id='+encodeURIComponent(p.id);
 const playerAnchor=p=>'<a href="'+linkPlayer(p)+'">'+esc(p.name)+'</a>';
 const honors=p=>(p.awards||[]).map(a=>'<a class="nhl-honor" href="'+esc(a.source)+'" target="_blank" rel="noopener noreferrer" title="Career achievement, not necessarily awarded during the attended game">'+esc(a.title)+' · '+esc(a.years)+'</a>').join('');
 const playerRow=p=>[playerAnchor(p),esc(p.team),stat(p.skater?.goals),stat(p.skater?.assists),stat(p.skater?.points),stat(p.skater?.shots_on_goal),stat(p.skater?.minutes)];
 const coachSlug=name=>name.normalize('NFKD').replace(/[\u0300-\u036f]/g,'').toLowerCase().replace(/[^a-z0-9]+/g,'-').replace(/^-|-$/g,'');
 const headCoachLink=name=>'../coach-history/index.html?coach='+encodeURIComponent(coachSlug(name))+'#profile';
 const numericMax=(items,get)=>items.filter(p=>Number.isFinite(get(p))).sort((a,b)=>get(b)-get(a)||a.name.localeCompare(b.name))[0];
 const ordered=g=>[...g.players].sort((a,b)=>Number(b.goalie?.shutouts||0)-Number(a.goalie?.shutouts||0)||Number(b.skater?.points||0)-Number(a.skater?.points||0));
 const table=(heads,rows)=>'<div class="nhl-table-wrap"><table><thead><tr>'+heads.map(x=>'<th>'+esc(x)+'</th>').join('')+'</tr></thead><tbody>'+rows.map(r=>'<tr>'+r.map(v=>'<td>'+v+'</td>').join('')+'</tr>').join('')+'</tbody></table></div>';
 const scores=g=>'<div class="nhl-scoreline"><div><span>'+esc(g.away_abbr)+'</span><small>'+esc(g.away)+'</small><strong>'+g.away_score+'</strong></div><b>FINAL</b><div><span>'+esc(g.home_abbr)+'</span><small>'+esc(g.home)+'</small><strong>'+g.home_score+'</strong></div></div>';
 const breadcrumb=t=>'<div class="nhl-kicker">NHL ATTENDANCE · '+esc(t)+'</div>';
 const tileGame=g=>'<a class="nhl-match" href="'+linkGame(g)+'"><span class="nhl-match-date">'+fmt(g.date)+' · '+g.venue+'</span><strong>'+esc(g.away)+' '+g.away_score+' — '+g.home_score+' '+esc(g.home)+'</strong><span>Full attended-game exhibit ↗</span></a>';
 const note='<p class="nhl-note">Stats in this archive reflect personally attended NHL games only. Individual lines are displayed only when supported by historical sources. Additional skater and goalie box-score research is ongoing.</p>';
 function overview(games){
  const g=games[0];
  $('app').innerHTML=breadcrumb('OVERVIEW')+'<section class="nhl-hero"><div class="nhl-kicker">A NEW CHAPTER OF COURTSIDE ARCHIVE</div><h1>Your NHL <em>history.</em></h1><p>One night on the ice begins the ninth sport in your personal attendance collection. From the goaltending to the scoring plays, this archive preserves what you actually witnessed.</p><a class="nhl-primary" href="'+linkGame(g)+'">Explore the first game ↗</a></section>'
  +'<section class="nhl-grid nhl-counts">'+box(games.length,'Game attended')+box(2,'Teams witnessed')+box(1,'Arena visited')+box('2008','First NHL season')+'</section>'
  +'<section class="nhl-panel"><div class="nhl-section-head"><div><span class="nhl-kicker">THE FIRST ENTRY</span><h2>Where hockey began.</h2></div></div>'+tileGame(g)+'</section>'
  +'<section class="nhl-grid nhl-columns"><div class="nhl-panel"><span class="nhl-kicker">SIGNATURE PERFORMANCE</span><h2>The shutout</h2><p><strong>'+playerAnchor(g.players.find(p=>p.goalie))+'</strong> stopped all 38 shots in Los Angeles’s 4–0 victory.</p><a href="./records.html">Explore NHL records ↗</a></div><div class="nhl-panel"><span class="nhl-kicker">PLAYER PROFILES</span><h2>The names behind the night</h2><p>Explore verified performances, separated into skater and goaltender statistics.</p><a href="./stats.html">Explore witnessed players ↗</a></div></section>'+note;
 }
 function gamePage(games){
  const id=new URLSearchParams(location.search).get('id'),g=games.find(x=>x.id===id)||games[0];
  const periods=g.periods;
  const per=table(['Team','1st','2nd','3rd','Final'],[[esc(g.away),...periods.away.map(String),String(g.away_score)].map(esc),[esc(g.home),...periods.home.map(String),String(g.home_score)].map(esc)]);
  const skaters=g.players.filter(p=>p.skater).sort((a,b)=>(b.skater.points??-1)-(a.skater.points??-1)||a.name.localeCompare(b.name));
  const goalies=g.players.filter(p=>p.goalie);
  $('app').innerHTML=breadcrumb('GAMES & BOX SCORES')+'<h1>Game details.</h1><p class="nhl-lead">'+fmt(g.date)+' · '+esc(g.venue)+' · '+esc(g.city)+', '+esc(g.state)+'</p>'+scores(g)
  +'<section class="nhl-panel"><h2>Scoring by period</h2>'+per+'</section>'
  +'<section class="nhl-panel"><h2>Team comparison</h2>'+table(['Team','Shots','Penalty min.','Power-play goals','Faceoffs won'],[
   [esc(g.away),stat(g.team_stats?.away.shots_on_goal),stat(g.team_stats?.away.penalty_minutes),stat(g.team_stats?.away.power_play_goals),stat(g.team_stats?.away.faceoff_wins)],
   [esc(g.home),stat(g.team_stats?.home.shots_on_goal),stat(g.team_stats?.home.penalty_minutes),stat(g.team_stats?.home.power_play_goals),stat(g.team_stats?.home.faceoff_wins)]
  ])+'<p class="nhl-note">Confirmed team totals; power-play opportunities have not been verified.</p></section>'
  +'<section class="nhl-panel"><h2>Identified goal scorers</h2>'+table(['Scorer','Team','Period'],(g.goals_identified||[]).map(x=>[esc(x.player),esc(x.team),stat(x.period)]))+
  '<p class="nhl-note">Not a complete goal-by-goal play log. Exact times and the remaining scorers are not yet verified.</p></section>'
  +'<section class="nhl-panel nhl-story"><span class="nhl-kicker">EVERY GAME HAS A STORY</span><h2>Three goals in six minutes. A 38-save shutout.</h2><p>'+esc(g.recap)+'</p></section>'
  +'<section class="nhl-panel"><h2>Player of the Game</h2><div class="nhl-feature"><strong>'+playerAnchor(goalies[0])+'</strong><span>38 saves · 38 shots against · 1.000 save percentage · Shutout</span></div><p class="nhl-note">Selected for his game-preserving 38-save shutout. This is a Courtside Archive editorial distinction, not the NHL’s official three-star selection.</p></section>'
  +'<section class="nhl-panel"><h2>Verified skater lines</h2>'+table(['Player','Team','G','A','PTS','SOG','TOI'],skaters.map(playerRow))+
  '<p class="nhl-note">Only verified player lines are shown. This is not yet a complete skater box score.</p></section>'
  +'<section class="nhl-panel"><h2>Verified goaltending</h2>'+table(['Goalie','Team','SA','SV','GA','SV%','SO'],goalies.map(p=>[playerAnchor(p),esc(p.team),String(p.goalie.shots_against),String(p.goalie.saves),String(p.goalie.goals_against),p.goalie.save_pct.toFixed(3),String(p.goalie.shutouts)]))+'</section>'
  +'<section class="nhl-panel"><h2>Head coaches</h2><p><strong><a href="'+headCoachLink(g.coach.away)+'">'+esc(g.coach.away)+'</a></strong> · Phoenix Coyotes &nbsp; | &nbsp; <strong><a href="'+headCoachLink(g.coach.home)+'">'+esc(g.coach.home)+'</a></strong> · Los Angeles Kings</p><a href="./coaches.html">View NHL coaching history ↗</a></section>'
  +'<section class="nhl-panel"><h2>Historical sources & verification</h2><p>'+esc(g.source_status)+'</p><p>'+sourceLinks(g)+'</p></section>';
 }
 function statsPage(games){
  const players=games.flatMap(g=>g.players);
  const skaters=players.filter(p=>p.skater).sort((a,b)=>(b.skater.points??-1)-(a.skater.points??-1)||a.name.localeCompare(b.name)),goalies=players.filter(p=>p.goalie);
  $('app').innerHTML=breadcrumb('PLAYERS')+'<h1>The players you saw.</h1><p class="nhl-lead">Skaters and goaltenders have separate leaderboards. These are witnessed-game totals, never their full NHL career statistics.</p>'
  +'<section class="nhl-panel"><h2>Skaters · verified lines</h2>'+table(['Player','Team','GP','G','A','PTS','SOG','TOI'],skaters.map(p=>[playerAnchor(p),esc(p.team),'1',...playerRow(p).slice(2)]))+'</section>'
  +'<section class="nhl-panel"><h2>Goaltenders · verified lines</h2>'+table(['Player','Team','GP','SV','GA','SV%','SO'],goalies.map(p=>[playerAnchor(p),esc(p.team),'1',String(p.goalie.saves),String(p.goalie.goals_against),p.goalie.save_pct.toFixed(3),String(p.goalie.shutouts)]))+'</section>'+note;
 }
 function playerPage(games){
  const list=games.flatMap(g=>g.players.map(p=>({...p,game:g})));
  const id=new URLSearchParams(location.search).get('id'),p=list.find(x=>x.id===id)||list[0],g=p.game;
  const statBoxes=p.goalie?[box(1,'Games'),box(p.goalie.saves,'Saves'),box(p.goalie.goals_against,'Goals against'),box(p.goalie.save_pct.toFixed(3),'Save percentage'),box(p.goalie.shutouts,'Shutouts'),box(p.goalie.wins,'Wins')]:[box(1,'Games'),box(p.skater.goals,'Goals'),box(p.skater.assists,'Assists'),box(p.skater.points,'Points')];
  $('app').innerHTML=breadcrumb('PLAYER PROFILE')+'<p><a href="./stats.html">← Player leaderboards</a></p><section class="nhl-profile-hero"><span class="nhl-kicker">'+esc(p.team)+' · '+esc(p.position)+'</span><h1>'+esc(p.name)+'</h1><p>Performance in your attended NHL game.</p></section><div class="nhl-grid nhl-counts">'+statBoxes.join('')+'</div>'
  +'<section class="nhl-panel"><h2>Signature performance</h2><p>'+esc(p.notables.join(' · '))+'</p>'+tileGame(g)+'</section>'+(p.awards?.length?'<section class="nhl-panel"><h2>Career honors</h2><p class="nhl-note">Lifetime NHL achievements, not awards earned specifically at this attended game.</p><div class="nhl-honors">'+honors(p)+'</div></section>':'')+note;
 }
 function recordsPage(games){
  const g=games[0],skaters=g.players.filter(p=>p.skater),goalies=g.players.filter(p=>p.goalie);
  const goals=numericMax(skaters,p=>p.skater.goals);
  const assists=numericMax(skaters,p=>p.skater.assists);
  const points=numericMax(skaters,p=>p.skater.points);
  const shots=numericMax(skaters,p=>p.skater.shots_on_goal);
  const saves=numericMax(goalies,p=>p.goalie.saves);
  const shutout=numericMax(goalies,p=>p.goalie.shutouts);
  const record=(category,player,value)=>[category,value===null||value===undefined?'Not yet verified':stat(value)+' · '+(player?.name||'Unverified')];
  const records=[
   ['Most goals, team',g.home_score+' · '+g.home],
   record('Most goals, skater (verified)',goals,goals?.skater.goals),
   record('Most assists, skater (verified)',assists,assists?.skater.assists),
   record('Most points, skater (verified)',points,points?.skater.points),
   record('Most shots, skater (verified)',shots,shots?.skater.shots_on_goal),
   record('Most saves, goalie',saves,saves?.goalie.saves),
   record('Most shutouts, goalie',shutout,shutout?.goalie.shutouts)
  ];
  $('app').innerHTML=breadcrumb('RECORD BOOK')+'<h1>Your NHL records.</h1><p class="nhl-lead">Personal attendance records from the NHL games you saw. Skater leaderboards exclude missing player statistics, rather than treating them as zero.</p><section class="nhl-grid nhl-record-grid">'+records.map(([label,value])=>'<div class="nhl-record"><small>'+esc(label)+'</small><strong>'+esc(value)+'</strong><a href="'+linkGame(g)+'">View game ↗</a></div>').join('')+'</section>'+note;
 }
 function coachesPage(games,career){
  const g=games[0],catalog=career?.stops||{};
  const rows=[{name:g.coach.away,team:g.away,w:0,l:1},{name:g.coach.home,team:g.home,w:1,l:0}];
  const careerTags=c=>(catalog[c.name]||[]).map(([team,years])=>{
    const witnessed=team===c.team;
    return '<span class="nhl-coach-stop '+(witnessed?'witnessed':'unseen')+'" title="'+(witnessed?'Witnessed in Courtside Archive':'Not witnessed in Courtside Archive')+'">'+esc(team)+' · '+esc(years)+'</span>';
  }).join('');
  $('app').innerHTML=breadcrumb('COACH HISTORY')+'<h1>Behind the benches.</h1><p class="nhl-lead">Every recorded head-coaching stop for the coaches you witnessed, with your own attended-game record tracked separately from their full careers.</p>'
  +'<div class="nhl-grid nhl-columns">'+rows.map(c=>'<article class="nhl-panel"><span class="nhl-kicker">'+esc(c.team)+'</span><h2>'+esc(c.name)+'</h2><div class="nhl-grid nhl-coach-stats">'+box(1,'Game coached')+box(c.w,'Wins')+box(c.l,'Losses')+'</div>'
  +(c.name==='Marc Crawford'?'<p><span class="nhl-honor">Jack Adams Award · 1994–95</span></p>':'')
  +'<h3>Head coaching stops</h3><p class="nhl-note">Burgundy: seen coaching · Ice blue: not seen coaching</p><div class="nhl-coach-stops">'+(careerTags(c)||'<span>Career history unavailable</span>')+'</div>'
  +'<p><a href="'+headCoachLink(c.name)+'">Open full Coach History profile ↗</a></p><a href="'+linkGame(g)+'">March 27, 2008 · View game ↗</a></article>').join('')+'</div>'
  +'<p class="nhl-note">Career stops include verified junior, AHL and Swiss league head-coaching jobs where applicable; assistant positions are not shown. Career honors are not necessarily from games attended.</p>';
 }

 Promise.all([
  fetch('./data/games.json',{cache:'no-store'}).then(r=>{if(!r.ok)throw Error('NHL game records unavailable');return r.json()}),
  fetch('../coach-history/data/nhl-head-coaching-stops.json',{cache:'no-store'}).then(r=>r.ok?r.json():{stops:{}}).catch(()=>({stops:{}}))
 ]).then(([games,career])=>{
  if(!Array.isArray(games)||!games.length)throw Error('No NHL games in the archive');
  if(page==='overview')overview(games);else if(page==='game')gamePage(games);else if(page==='stats')statsPage(games);
  else if(page==='player')playerPage(games);else if(page==='records')recordsPage(games);else if(page==='coaches')coachesPage(games,career);
 }).catch(err=>{$('app').innerHTML='<section class="nhl-panel">Unable to load NHL archive: '+esc(err.message)+'</section>';});
})();
