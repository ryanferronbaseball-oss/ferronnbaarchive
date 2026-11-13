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
 const signed=n=>n>0?'+'+n:String(n);
 const playerRow=p=>[playerAnchor(p),esc(p.team),stat(p.skater?.goals),stat(p.skater?.assists),stat(p.skater?.points),signed(p.skater?.plus_minus??0),stat(p.skater?.penalty_minutes),stat(p.skater?.shots_on_goal),stat(p.skater?.minutes)];
 const coachSlug=name=>name.normalize('NFKD').replace(/[\u0300-\u036f]/g,'').toLowerCase().replace(/[^a-z0-9]+/g,'-').replace(/^-|-$/g,'');
 const headCoachLink=name=>'../coach-history/index.html?coach='+encodeURIComponent(coachSlug(name))+'#profile';
 const numericMax=(items,get)=>items.filter(p=>Number.isFinite(get(p))).sort((a,b)=>get(b)-get(a)||a.name.localeCompare(b.name))[0];
 const ordered=g=>[...g.players].sort((a,b)=>Number(b.goalie?.shutouts||0)-Number(a.goalie?.shutouts||0)||Number(b.skater?.points||0)-Number(a.skater?.points||0));
 const table=(heads,rows)=>'<div class="nhl-table-wrap"><table><thead><tr>'+heads.map(x=>'<th>'+esc(x)+'</th>').join('')+'</tr></thead><tbody>'+rows.map(r=>'<tr>'+r.map(v=>'<td>'+v+'</td>').join('')+'</tr>').join('')+'</tbody></table></div>';
 const scores=g=>'<div class="nhl-scoreline"><div><span>'+esc(g.away_abbr)+'</span><small>'+esc(g.away)+'</small><strong>'+g.away_score+'</strong></div><b>FINAL</b><div><span>'+esc(g.home_abbr)+'</span><small>'+esc(g.home)+'</small><strong>'+g.home_score+'</strong></div></div>';
 const breadcrumb=t=>'<div class="nhl-kicker">NHL ATTENDANCE · '+esc(t)+'</div>';
 const tileGame=g=>'<a class="nhl-match" href="'+linkGame(g)+'"><span class="nhl-match-date">'+fmt(g.date)+' · '+g.venue+'</span><strong>'+esc(g.away)+' '+g.away_score+' — '+g.home_score+' '+esc(g.home)+'</strong><span>Full attended-game exhibit ↗</span></a>';
 const note='<p class="nhl-note">All 36 participating skaters and both goaltenders have official game statistics from NHL Game 1160, March 27, 2008. Backup goaltenders who did not play are excluded from attended-player totals. Career awards are listed separately from witnessed-game performance.</p>';
 function overview(games){
  const g=games[0];
  $('app').innerHTML=breadcrumb('OVERVIEW')+'<section class="nhl-hero"><div class="nhl-kicker">A NEW CHAPTER OF COURTSIDE ARCHIVE</div><h1>Your NHL <em>history.</em></h1><p>One night on the ice begins the ninth sport in your personal attendance collection. From the goaltending to the scoring plays, this archive preserves what you actually witnessed.</p><a class="nhl-primary" href="'+linkGame(g)+'">Explore the first game ↗</a></section>'
  +'<section class="nhl-grid nhl-counts">'+box(games.length,'Game attended')+box(2,'Teams witnessed')+box(1,'Arena visited')+box('2008','First NHL season')+'</section>'
  +'<section class="nhl-panel"><div class="nhl-section-head"><div><span class="nhl-kicker">THE FIRST ENTRY</span><h2>Where hockey began.</h2></div></div>'+tileGame(g)+'</section>'
  +'<section class="nhl-grid nhl-columns"><div class="nhl-panel"><span class="nhl-kicker">SIGNATURE PERFORMANCE</span><h2>The shutout</h2><p><strong>'+playerAnchor(g.players.find(p=>p.goalie&&p.team===g.home))+'</strong> stopped all 38 shots in Los Angeles’s 4–0 victory.</p><a href="./records.html">Explore NHL records ↗</a></div><div class="nhl-panel"><span class="nhl-kicker">PLAYER PROFILES</span><h2>The names behind the night</h2><p>Explore verified performances, separated into skater and goaltender statistics.</p><a href="./stats.html">Explore witnessed players ↗</a></div></section>'+note;
 }
 function gamePage(games){
  const id=new URLSearchParams(location.search).get('id'),g=games.find(x=>x.id===id)||games[0];
  const periods=g.periods,statAway=g.team_stats.away,statHome=g.team_stats.home;
  const per=table(['Team','1st','2nd','3rd','Total','Shots by period'],
    [[esc(g.away),...periods.away.map(String),String(g.away_score),statAway.period_shots.join(' / ')],
     [esc(g.home),...periods.home.map(String),String(g.home_score),statHome.period_shots.join(' / ')]]);
  const skaters=g.players.filter(p=>p.skater),goalies=g.players.filter(p=>p.goalie),
   homeGoalie=goalies.find(p=>p.team===g.home);
  const skaterTable=team=>table(['Player','Team','G','A','PTS','+/−','PIM','SOG','TOI'],
   skaters.filter(p=>p.team===team).sort((a,b)=>(b.skater.points??0)-(a.skater.points??0)||a.name.localeCompare(b.name)).map(playerRow));
  const scorerLink=name=>{const p=g.players.find(x=>x.name===name);return p?playerAnchor(p):esc(name)};
  const scoringTable=table(['Per.','Time','Goal scorer','Assists','Strength','Score'],(g.scoring||[]).map((goal,i)=>[
   String(goal.period),esc(goal.time),scorerLink(goal.scorer),goal.assists.map(scorerLink).join(', ')||'Unassisted',
   goal.strength==='PP'?'Power play':'Even strength','0–'+(i+1)
  ]));
  const penaltyTable=table(['Period','Time','Team','Player','Infraction','PIM'],(g.penalties||[]).map(x=>[
   String(x.period),esc(x.time),esc(x.team),scorerLink(x.player),esc(x.infraction),stat(x.minutes)
  ]));
  const teamCompare=table(['Team','SOG','Power play','PIM','Faceoffs','Hits','Blocks','Takeaways','Giveaways'],[
   [esc(g.away),stat(statAway.shots_on_goal),statAway.power_play_goals+'/'+statAway.power_play_chances,stat(statAway.penalty_minutes),
    stat(statAway.faceoff_wins),stat(statAway.hits),stat(statAway.blocked_shots),stat(statAway.takeaways),stat(statAway.giveaways)],
   [esc(g.home),stat(statHome.shots_on_goal),statHome.power_play_goals+'/'+statHome.power_play_chances,stat(statHome.penalty_minutes),
    stat(statHome.faceoff_wins),stat(statHome.hits),stat(statHome.blocked_shots),stat(statHome.takeaways),stat(statHome.giveaways)]
  ]);
  const goalieTable=table(['Goalie','Team','SA','SV','GA','SV%','TOI','W/L','SO'],
   goalies.map(p=>[playerAnchor(p),esc(p.team),stat(p.goalie.shots_against),stat(p.goalie.saves),
    stat(p.goalie.goals_against),p.goalie.save_pct.toFixed(3),esc(p.goalie.minutes),p.goalie.wins?'W':'L',stat(p.goalie.shutouts)]));
  const stars=(g.official_three_stars||[]).map((name,i)=>'<div class="nhl-star-item"><strong>'+(i+1)+'.</strong>'+scorerLink(name)+'</div>').join('');
  $('app').innerHTML=breadcrumb('GAMES & BOX SCORES')+'<h1>Game details.</h1><p class="nhl-lead">'+fmt(g.date)+' · '+esc(g.venue)+' · '+esc(g.city)+', '+esc(g.state)+' · '+Number(g.attendance).toLocaleString('en-US')+' attendance</p>'+scores(g)
  +'<section class="nhl-panel"><h2>Scoring by period</h2>'+per+'</section>'
  +'<section class="nhl-panel"><h2>Official scoring summary</h2>'+scoringTable+'</section>'
  +'<section class="nhl-panel"><h2>Team comparison</h2>'+teamCompare+'</section>'
  +'<section class="nhl-panel"><h2>Official penalty summary</h2>'+penaltyTable+'</section>'
  +'<section class="nhl-panel nhl-story"><span class="nhl-kicker">EVERY GAME HAS A STORY</span><h2>Three second-period goals. A 38-save shutout.</h2><p>'+esc(g.recap)+'</p></section>'
  +'<section class="nhl-panel"><h2>Player of the Game</h2><div class="nhl-feature"><strong>'+playerAnchor(homeGoalie)+'</strong><span>38 saves · 38 shots against · 1.000 save percentage · Shutout</span></div><p class="nhl-note">Courtside Archive selection: '+esc(homeGoalie.name)+'. The NHL’s official three stars are listed below and use a separate selection process.</p></section>'
  +'<section class="nhl-panel"><h2>Official NHL three stars</h2><div class="nhl-stars">'+stars+'</div></section>'
  +'<section class="nhl-panel"><h2>'+esc(g.away)+' · complete skater box score</h2>'+skaterTable(g.away)+'</section>'
  +'<section class="nhl-panel"><h2>'+esc(g.home)+' · complete skater box score</h2>'+skaterTable(g.home)+'</section>'
  +'<section class="nhl-panel"><h2>Goaltending</h2>'+goalieTable+'</section>'
  +'<section class="nhl-panel"><h2>Head coaches</h2><p><strong><a href="'+headCoachLink(g.coach.away)+'">'+esc(g.coach.away)+'</a></strong> · Phoenix Coyotes &nbsp; | &nbsp; <strong><a href="'+headCoachLink(g.coach.home)+'">'+esc(g.coach.home)+'</a></strong> · Los Angeles Kings</p><a href="./coaches.html">View NHL coaching history ↗</a></section>'
  +'<section class="nhl-panel"><h2>Historical sources & verification</h2><p>'+esc(g.source_status)+'</p><p>'+sourceLinks(g)+'</p></section>';
 }
 function statsPage(games){
  const players=games.flatMap(g=>g.players);
  const skaters=players.filter(p=>p.skater).sort((a,b)=>(b.skater.points??-1)-(a.skater.points??-1)||a.name.localeCompare(b.name)),goalies=players.filter(p=>p.goalie);
  $('app').innerHTML=breadcrumb('PLAYERS')+'<h1>The players you saw.</h1><p class="nhl-lead">Skaters and goaltenders have separate leaderboards. These are witnessed-game totals, never their full NHL career statistics.</p>'
  +'<section class="nhl-panel"><h2>Skaters · verified lines</h2>'+table(['Player','Team','GP','G','A','PTS','+/−','PIM','SOG','TOI'],skaters.map(p=>[playerAnchor(p),esc(p.team),'1',...playerRow(p).slice(2)]))+'</section>'
  +'<section class="nhl-panel"><h2>Goaltenders · verified lines</h2>'+table(['Player','Team','GP','SA','SV','GA','SV%','TOI','W/L','SO'],goalies.map(p=>[playerAnchor(p),esc(p.team),'1',stat(p.goalie.shots_against),stat(p.goalie.saves),stat(p.goalie.goals_against),p.goalie.save_pct.toFixed(3),esc(p.goalie.minutes),p.goalie.wins?'W':'L',stat(p.goalie.shutouts)]))+'</section>'+note;
 }
 function playerPage(games){
  const list=games.flatMap(g=>g.players.map(p=>({...p,game:g})));
  const id=new URLSearchParams(location.search).get('id'),p=list.find(x=>x.id===id)||list[0],g=p.game;
  const b=p.goalie?p.goalie:p.skater;
  const statBoxes=p.goalie?[
   box(1,'Games'),box(b.saves,'Saves'),box(b.shots_against,'Shots against'),
   box(b.goals_against,'Goals against'),box(b.save_pct.toFixed(3),'Save percentage'),
   box(b.minutes,'Ice time'),box(b.shutouts,'Shutouts'),box(b.wins,'Wins')
  ]:[
   box(1,'Games'),box(b.goals,'Goals'),box(b.assists,'Assists'),box(b.points,'Points'),
   box((b.plus_minus>0?'+':'')+b.plus_minus,'Plus / minus'),box(b.penalty_minutes,'Penalty minutes'),
   box(b.shots_on_goal,'Shots on goal'),box(b.minutes,'Ice time')
  ];
  const achievements=p.notables?.length?'<section class="nhl-panel"><h2>Game notes</h2><p>'+esc(p.notables.join(' · '))+'</p></section>':'';
  $('app').innerHTML=breadcrumb('PLAYER PROFILE')+'<p><a href="./stats.html">← Player leaderboards</a></p>'
  +'<section class="nhl-profile-hero"><span class="nhl-kicker">'+esc(p.team)+' · '+esc(p.position)+'</span><h1>'+esc(p.name)+'</h1><p>Performance in your attended NHL game.</p></section>'
  +'<div class="nhl-grid nhl-counts">'+statBoxes.join('')+'</div>'
  +achievements+'<section class="nhl-panel"><h2>Attended games</h2>'+tileGame(g)+'</section>'
  +(p.awards?.length?'<section class="nhl-panel"><h2>Career honors</h2><p class="nhl-note">Lifetime NHL achievements, not awards earned specifically at this attended game.</p><div class="nhl-honors">'+honors(p)+'</div></section>':'')
  +note;
 }
 function recordsPage(games){
  const g=games[0],skaters=g.players.filter(p=>p.skater),goalies=g.players.filter(p=>p.goalie);
  const top=(title,arr,key,format)=>{
   const values=arr.map(p=>({p,value:key(p)})).filter(x=>typeof x.value==='number'&&Number.isFinite(x.value));
   if(!values.length)return [title,'No verified entries'];
   const max=Math.max(...values.map(x=>x.value));
   const names=values.filter(x=>x.value===max).map(x=>x.p.name).sort((a,b)=>a.localeCompare(b));
   return [title,(format?format(max):String(max))+' · '+names.join(', ')];
  };
  const toSeconds=x=>{if(!x)return NaN;const bits=x.split(':').map(Number);return bits[0]*60+bits[1]};
  const records=[
   ['Most goals, team',g.home_score+' · '+g.home],
   top('Most goals, skater',skaters,p=>p.skater.goals),
   top('Most assists, skater',skaters,p=>p.skater.assists),
   top('Most points, skater',skaters,p=>p.skater.points),
   top('Most shots, skater',skaters,p=>p.skater.shots_on_goal),
   top('Most skater ice time',skaters,p=>toSeconds(p.skater.minutes),v=>Math.floor(v/60)+':'+String(v%60).padStart(2,'0')),
   top('Most saves, goalie',goalies,p=>p.goalie.saves),
   top('Shutouts, goalie',goalies,p=>p.goalie.shutouts),
   ['Game-winning goal',(g.scoring||[])[0]?.scorer||'—']
  ];
  $('app').innerHTML=breadcrumb('RECORD BOOK')+'<h1>Your NHL records.</h1><p class="nhl-lead">All-time records within your personally attended NHL games. Tied leaders appear together, and no league-wide career totals are mixed into this table.</p><section class="nhl-grid nhl-record-grid">'+records.map(([label,value])=>'<div class="nhl-record"><small>'+esc(label)+'</small><strong>'+esc(value)+'</strong><a href="'+linkGame(g)+'">View game ↗</a></div>').join('')+'</section>'+note;
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
