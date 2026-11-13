/* Courtside NHL archive: witnessed-game data only. Unverified skater boxes remain unpopulated. */
(()=>{'use strict';
 const $=id=>document.getElementById(id);
 const esc=x=>String(x??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
 const fmt=d=>new Date(d+'T12:00:00Z').toLocaleDateString('en-US',{month:'long',day:'numeric',year:'numeric',timeZone:'UTC'});
 const stat=(x,dash='—')=>x===null||x===undefined?dash:esc(x);
 const page=document.body.dataset.page||'overview';
 const navItems=[['index.html','Overview','overview'],['game.html','Games','game'],['stats.html','Players','stats'],['hall-of-fame.html','★ Hall of Fame','hof'],['records.html','Records','records'],['coaches.html','Coaches','coaches']];
 const nav=navItems.map(([href,name,key])=>'<a href="./'+href+'"'+(page===key?' aria-current="page"':'')+'>'+name+'</a>').join('')+'<a href="../index.html">All archives ↗</a>';
 $('navigation').innerHTML=page==='overview'
  ?'<header class="archive-header nhl-overview-header"><a href="./index.html" class="archive-logo">COURTSIDE ARCHIVE<small>EVERY GAME HAS A STORY · NHL</small></a><nav class="archive-nav" aria-label="NHL navigation">'+navItems.map(([href,name,key])=>'<a href="./'+href+'"'+(page===key?' aria-current="page"':'')+'>'+name+'</a>').join('')+'</nav><a class="back-link" href="../index.html">All archives ↗</a></header>'
  :'<div class="nhl-topbar"><a href="./index.html" class="nhl-logo"><span class="nhl-mark">CA</span><span>COURTSIDE ARCHIVE<small>EVERY GAME HAS A STORY · NHL</small></span></a><nav aria-label="NHL navigation">'+nav+'</nav></div>';
 const sourceLinks=g=>(g.source_urls||[]).map((url,i)=>'<a href="'+esc(url)+'" target="_blank" rel="noopener noreferrer">Source '+(i+1)+' ↗</a>').join(' · ');
 const box=(value,label)=>'<div class="nhl-stat"><strong>'+stat(value)+'</strong><small>'+esc(label)+'</small></div>';
 const linkGame=g=>'./game.html?id='+encodeURIComponent(g.id);
 const linkPlayer=p=>'./player.html?id='+encodeURIComponent(p.id);
 const playerAnchor=p=>'<a href="'+linkPlayer(p)+'">'+esc(p.name)+'</a>';
 const honorTypes=[
  {key:'hall',name:'Hockey Hall of Fame',badge:'★ HALL OF FAME',mark:'★'},
  {key:'otherhall',name:'National & IIHF Hockey Halls',badge:'★ OTHER HOCKEY HALLS',mark:'★'},
  {key:'stanley',name:'Stanley Cup championships',badge:'🏆 STANLEY CUP',mark:'🏆'},
  {key:'award',name:'NHL individual awards',badge:'◆ NHL AWARDS',mark:'◆'},
  {key:'allteam',name:'NHL All-Star & All-Rookie Teams',badge:'◆ ALL-STAR TEAMS',mark:'◆'},
  {key:'allstar',name:'NHL All-Star Game selections',badge:'☆ NHL ALL-STAR',mark:'☆'},
  {key:'retired',name:'Retired numbers',badge:'★ RETIRED NUMBER',mark:'★'},
  {key:'olympic',name:'Olympic medals',badge:'◈ OLYMPIC MEDALS',mark:'◈'},
  {key:'world',name:'IIHF & international honors',badge:'◎ INTERNATIONAL',mark:'◎'},
  {key:'other',name:'Other professional honors',badge:'✦ OTHER PRO',mark:'✦'}
 ];
 const categorizeAward=a=>{
  if(a.category)return a.category;
  if(/Stanley Cup/i.test(a.title))return 'stanley';
  if(a.title==='Hockey Hall of Fame')return 'hall';
  if(/Hall of Fame/i.test(a.title))return 'otherhall';
  if(/retired/i.test(a.title))return 'retired';
  if(/All-Star Game/i.test(a.title))return 'allstar';
  if(/All-Star Team|All-Rookie Team/i.test(a.title))return 'allteam';
  if(/Olympic/i.test(a.title))return 'olympic';
  if(/IIHF|Triple Gold/i.test(a.title))return 'world';
  if(/Trophy|Award/i.test(a.title))return 'award';
  return 'other';
 };
 // Years count events / medals / championship seasons, not the number of
 // data objects. Equivalent to the MLB award-badge and NFL Pro Bowl counts.
 const honorCount=items=>items.reduce((n,a)=>n+(String(a.years||'').match(/\b(?:19|20)\d{2}\b/g)||[]).length,0);
 const careerBadges=p=>{
  if(!p.awards?.length)return '';
  return '<div class="nhl-profile-achievements" aria-label="Career accomplishments">'+honorTypes.map(t=>{
   const awards=p.awards.filter(a=>categorizeAward(a)===t.key);
   if(!awards.length)return '';
   const count=honorCount(awards)||awards.length;
   return '<a class="nhl-profile-badge '+t.key+'" href="#nhl-honor-'+t.key+'" title="Jump to '+esc(t.name)+' career details">'+t.badge+(count>1?' · '+count:'')+'</a>';
  }).join('')+'</div>';
 };
 const careerHonorPanel=p=>{
  if(!p.awards?.length)return '';
  const sections=honorTypes.map((t,i)=>{
   const awards=p.awards.filter(a=>categorizeAward(a)===t.key);
   if(!awards.length)return '';
   return '<section class="nhl-honor-group" id="nhl-honor-'+t.key+'"><h3>'+t.mark+' '+esc(t.name)+'</h3><div class="nhl-honor-tags">'
    +awards.map(a=>'<a class="nhl-honor '+t.key+'" href="'+esc(a.source)+'" target="_blank" rel="noopener noreferrer" title="Open source for this career honor">'
      +esc(a.title)+' <span class="nhl-honor-years">'+esc(a.years)+'</span> ↗</a>').join('')
    +'</div></section>';
  }).join('');
  return '<section class="nhl-panel nhl-career-honors" id="careerHonors"><h2>Career Awards &amp; Honors</h2>'
   +'<p class="nhl-note">These are career honors across every season, not necessarily earned in the attended game. All-Star Game selections and end-of-season All-Star Teams are counted separately. Open a tag for its source.</p>'
   +sections+'</section>';
 };
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
  // Align NHL overview composition with the NBA/NFL/MLB landing pages:
  // clean masthead, metrics, recent games, signature cards, charts, and game history.
  const orderedGames=games.slice().sort((a,b)=>a.date.localeCompare(b.date)||a.id.localeCompare(b.id));
  const newest=orderedGames.slice().reverse();
  const gameCount=orderedGames.length;
  const uniquePlayers=new Map();
  const years=new Map(),teams=new Map();
  orderedGames.forEach(g=>{
    years.set(g.date.slice(0,4),(years.get(g.date.slice(0,4))||0)+1);
    for(const t of [g.away,g.home])teams.set(t,(teams.get(t)||0)+1);
    (g.players||[]).forEach(p=>uniquePlayers.set(p.id,p));
  });
  const players=[...uniquePlayers.values()];
  const countScoring=orderedGames.reduce((n,g)=>n+(g.scoring||[]).length,0);
  const gameCard=g=>'<article class="nhl-overview-game-card">'
    +'<div class="nhl-overview-game-date">'+fmt(g.date)+' · '+esc(g.competition||'NHL regular season')+'</div>'
    +'<h3>'+esc(g.away)+' at '+esc(g.home)+'</h3>'
    +'<div class="nhl-overview-game-score">'+esc(g.away_abbr||g.away)+' '+g.away_score+' <span>—</span> '+esc(g.home_abbr||g.home)+' '+g.home_score+'</div>'
    +'<div class="nhl-overview-caption">'+esc(g.venue)+' · '+esc(g.city)+', '+esc(g.state)+'</div>'
    +'<a class="nhl-overview-action" href="'+linkGame(g)+'">Game box score ↗</a></article>';
  const performances=orderedGames.flatMap(g=>(g.players||[]).map(p=>({...p,game:g})));
  const best=(predicate,value)=>performances.filter(predicate).sort((a,b)=>value(b)-value(a)||a.game.date.localeCompare(b.game.date)||a.name.localeCompare(b.name))[0];
  const bestPoints=best(p=>p.skater&&Number.isFinite(p.skater.points),p=>p.skater.points);
  const bestSaves=best(p=>p.goalie&&Number.isFinite(p.goalie.saves),p=>p.goalie.saves);
  const bestShots=best(p=>p.skater&&Number.isFinite(p.skater.shots_on_goal),p=>p.skater.shots_on_goal);
  const feature=(label,p,value,unit,details)=>p?'<article class="nhl-overview-feature">'
    +'<div class="nhl-overview-feature-label">'+esc(label)+'</div>'
    +'<div class="nhl-overview-feature-number">'+stat(value)+' <small>'+esc(unit)+'</small></div>'
    +'<h3>'+playerAnchor(p)+'</h3>'
    +'<p>'+esc(p.team)+' · '+fmt(p.game.date)+'</p>'
    +'<div class="nhl-overview-caption">'+esc(details)+'</div>'
    +'<a class="nhl-overview-action secondary" href="'+linkGame(p.game)+'">View performance ↗</a></article>':'';
  const bars=entries=>{
    const max=Math.max(1,...entries.map(x=>x[1]));
    return entries.map(([label,n])=>'<div class="nhl-overview-bar-row"><span>'+esc(label)+'</span>'
      +'<div class="nhl-overview-bar-track"><div class="nhl-overview-bar-fill" style="width:'+(100*n/max).toFixed(2)+'%"></div></div>'
      +'<strong>'+n+'</strong></div>').join('');
  };
  const metric=(value,title)=>'<div class="nhl-overview-metric"><strong>'+stat(value)+'</strong><small>'+esc(title)+'</small></div>';
  const content='<div class="nhl-overview">'
    +'<div class="nhl-overview-eyebrow">NATIONAL HOCKEY LEAGUE · PERSONAL ATTENDANCE</div>'
    +'<h1>Your NHL history.</h1>'
    +'<a class="nhl-overview-action secondary nhl-hof-action" href="./hall-of-fame.html">★ NHL Hall of Famers You’ve Seen ↗</a>'
    +'<p class="nhl-overview-lead">Your NHL attendance history, preserved in one place. Explore the games, players, seasons, arenas and standout performances you witnessed.</p>'
    +'<section class="nhl-overview-metrics" aria-label="NHL attendance metrics">'
    +metric(gameCount,'Games attended')+metric(players.length,'Players with recorded stats')
    +metric(countScoring,'Scoring plays witnessed')+metric(years.size,'Calendar years')+'</section>'
    +'<section class="nhl-overview-section" aria-label="Most recent NHL games">'
    +'<div class="nhl-overview-section-heading"><h2>Games attended</h2><a class="nhl-overview-action secondary" href="./game.html">All game box scores ↗</a></div>'
    +'<div class="nhl-overview-game-grid">'+newest.slice(0,3).map(gameCard).join('')+'</div></section>'
    +'<section class="nhl-overview-section" id="signaturePerformances">'
    +'<div class="nhl-overview-section-heading"><h2>Signature Performances</h2><a class="nhl-overview-action secondary" href="./records.html">Explore Records ↗</a></div>'
    +'<p class="nhl-overview-description">The top single-game scoring, goaltending and shooting performances across the NHL games you attended.</p>'
    +'<div class="nhl-overview-feature-grid">'
      +feature('Scoring record',bestPoints,bestPoints?.skater.points,'PTS',bestPoints?bestPoints.skater.goals+' G · '+bestPoints.skater.assists+' A':'')
      +feature('Goaltending record',bestSaves,bestSaves?.goalie.saves,'SAVES',bestSaves&&bestSaves.goalie.shutouts?'Shutout · '+bestSaves.goalie.save_pct.toFixed(3)+' SV%':bestSaves?'Save percentage '+bestSaves.goalie.save_pct.toFixed(3):'')
      +feature('Shots on goal record',bestShots,bestShots?.skater.shots_on_goal,'SOG',bestShots?'Goals '+bestShots.skater.goals+' · Assists '+bestShots.skater.assists:'')
    +'</div></section>'
    +'<div class="nhl-overview-charts" aria-label="NHL attendance charts">'
    +'<section class="nhl-overview-panel"><h2>Most-watched teams</h2>'+bars([...teams.entries()].sort((a,b)=>b[1]-a[1]||a[0].localeCompare(b[0])).slice(0,8))+'</section>'
    +'<section class="nhl-overview-panel"><h2>Attendance by year</h2>'+bars([...years.entries()].sort((a,b)=>a[0].localeCompare(b[0])))+'</section>'
    +'</div>'
    +'<section class="nhl-overview-panel nhl-overview-history" id="gameHistorySection"><h2>My game history</h2>'
    +'<p class="nhl-overview-description">Based on your attendance records. Select a game to open its full box score, scoring timeline and player performances.</p>'
    +'<div class="nhl-overview-filters">'
     +'<input type="search" id="nhl-overview-search" aria-label="Search attended NHL games" placeholder="Search team, matchup, arena…">'
     +'<select id="nhl-overview-year" aria-label="Filter NHL games by year"><option value="">All years</option>'+[...years.keys()].sort().reverse().map(y=>'<option value="'+esc(y)+'">'+esc(y)+'</option>').join('')+'</select>'
     +'<select id="nhl-overview-sort" aria-label="Sort attended NHL games"><option value="asc">Oldest first</option><option value="desc">Newest first</option></select>'
    +'</div><div class="nhl-overview-table-scroll"><table><thead><tr><th>Date</th><th>Away</th><th>Home</th><th>Arena</th><th>Details</th></tr></thead><tbody id="nhl-overview-history-body"></tbody></table></div>'
    +'<div class="nhl-overview-foot" id="nhl-overview-showing"></div></section>'
    +'<section class="nhl-overview-panel nhl-overview-explore"><h2>Explore your NHL stats</h2>'
    +'<p>Every attended-game box score includes all participating skaters, both goalies, goal times and assists, and the official scoring and penalty summaries. Explore individual totals and the records you witnessed.</p>'
    +'<a class="nhl-overview-action" href="./stats.html">Open NHL player leaderboards ↗</a></section>'
    +'<p class="nhl-overview-foot">Courtside Archive · NHL attendance statistics drawn from historical NHL game reports. Only games you attended are counted.</p>'
   +'</div>';
  $('app').innerHTML=content;
  const drawHistory=()=>{
    const query=$('nhl-overview-search').value.trim().toLowerCase();
    const year=$('nhl-overview-year').value,sort=$('nhl-overview-sort').value;
    const matches=orderedGames.filter(g=>(!year||g.date.startsWith(year))
     &&[g.date,g.away,g.home,g.venue,g.city,g.state].join(' ').toLowerCase().includes(query)).sort((a,b)=>sort==='asc'?a.date.localeCompare(b.date)||a.id.localeCompare(b.id):b.date.localeCompare(a.date)||b.id.localeCompare(a.id));
    $('nhl-overview-history-body').innerHTML=matches.map(g=>'<tr><td><a href="'+linkGame(g)+'">'+esc(g.date)+'</a></td>'
     +'<td>'+esc(g.away)+'</td><td><strong>'+esc(g.home)+'</strong></td><td>'+esc(g.venue)+'</td>'
     +'<td><a class="nhl-overview-table-link" href="'+linkGame(g)+'">View game →</a></td></tr>').join('')||'<tr><td colspan="5">No matching NHL games.</td></tr>';
    $('nhl-overview-showing').textContent='Showing '+matches.length+' of '+gameCount+' '+(gameCount===1?'game':'games')+'.';
  };
  for(const id of ['nhl-overview-search','nhl-overview-year','nhl-overview-sort'])$(id).addEventListener('input',drawHistory);
  drawHistory();
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
  +'<section class="nhl-profile-hero"><span class="nhl-kicker">'+esc(p.team)+' · '+esc(p.position)+'</span><h1>'+esc(p.name)+'</h1>'+careerBadges(p)+'<p>Performance in your attended NHL game.</p></section>'
  +'<div class="nhl-grid nhl-counts">'+statBoxes.join('')+'</div>'
  +achievements+'<section class="nhl-panel"><h2>Attended games</h2>'+tileGame(g)+'</section>'
  +careerHonorPanel(p)
  +note;
 }
 function hofPage(games){
  // Mirroring the major-league Hall of Fame pages: only the primary
  // Hockey Hall of Fame is counted as an inductee; IIHF, US and national
  // hockey halls remain separate career profile honors.
  const attended=games.flatMap(g=>g.players.map(p=>({...p,game:g})));
  const hof=attended.filter(p=>(p.awards||[]).some(a=>a.title==='Hockey Hall of Fame'));
  const related=attended.filter(p=>!(p.awards||[]).some(a=>a.title==='Hockey Hall of Fame')
    &&(p.awards||[]).some(a=>/Hall of Fame/i.test(a.title)));
  const article=p=>{
   const member=p.awards.find(a=>a.title==='Hockey Hall of Fame');
   return '<article class="nhl-hof-card"><span class="nhl-kicker">HOCKEY HALL OF FAME · INDUCTED '+esc(member.years)+'</span>'
    +'<h2><a href="'+linkPlayer(p)+'">'+esc(p.name)+'</a></h2><p>'+esc(p.team)+' · '+esc(p.position)+' · '+fmt(p.game.date)+'</p>'
    +'<div class="nhl-profile-achievements">'+(p.awards||[]).filter(a=>['stanley','award','allstar','retired'].includes(categorizeAward(a)))
      .map(a=>'<span class="nhl-hof-mini">'+esc(a.title)+' · '+esc(a.years)+'</span>').join('')+'</div>'
    +'<div class="nhl-hof-links"><a href="'+linkPlayer(p)+'">Player profile ↗</a><a href="'+esc(member.source)+'" target="_blank" rel="noopener noreferrer">Hockey Hall of Fame record ↗</a></div></article>';
  };
  $('app').innerHTML=breadcrumb('HALL OF FAME')+'<section class="nhl-hero nhl-hof-hero"><div class="nhl-kicker">THE LEGENDS YOU SAW</div><h1>Hockey Hall <em>of Fame.</em></h1>'
   +'<p>The NHL players in your attended-game archive who have been inducted into the Hockey Hall of Fame in Toronto. Just like the NBA, MLB and NFL halls, only induction into the sport’s primary Hall of Fame qualifies here.</p></section>'
   +'<section class="nhl-grid nhl-counts">'+box(hof.length,'Hockey Hall of Famers witnessed')+box(games.length,'NHL games attended')+box(games[0].players.length,'Players witnessed')+'</section>'
   +'<section class="nhl-panel"><h2>Inductees you witnessed</h2>'+(hof.length?'<div class="nhl-hof-grid">'+hof.map(article).join('')+'</div>':'<p>No inducted Hockey Hall of Fame players in the recorded games yet.</p>')+'</section>'
   +(related.length?'<section class="nhl-panel"><h2>Other hockey Hall of Fame honors</h2><p class="nhl-note">International and national halls are linked from their player profiles, but do not inflate the primary Hockey Hall of Fame count.</p>'
     +'<div class="nhl-honor-tags">'+related.map(p=>'<a class="nhl-honor" href="'+linkPlayer(p)+'">'+esc(p.name)+' · '+esc(p.awards.filter(a=>/Hall of Fame/i.test(a.title)).map(a=>a.title).join(', '))+' ↗</a>').join('')+'</div></section>':'')+note;
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
  +'<div class="nhl-coach-achievements">'+(career?.honors?.[c.name]||[]).map(h=>'<a class="nhl-honor" href="'+esc(h.source)+'" target="_blank" rel="noopener noreferrer">'+esc(h.title)+' · '+esc(h.years)+' ↗</a>').join('')+'</div>'
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
  else if(page==='player')playerPage(games);else if(page==='hof')hofPage(games);else if(page==='records')recordsPage(games);else if(page==='coaches')coachesPage(games,career);
 }).catch(err=>{$('app').innerHTML='<section class="nhl-panel">Unable to load NHL archive: '+esc(err.message)+'</section>';});
})();
