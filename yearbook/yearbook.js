/* Courtside Archive Yearbook — annual game attendance across all nine sports.
   Counts use the same college-baseball attendance-only exclusion as homepage milestones.
   Great Games nominations are editorial; closest finishes are statistical, not personal ratings. */
(()=>{'use strict';
const byId=id=>document.getElementById(id);
const esc=v=>String(v??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const fmtDate=v=>new Date(v+'T12:00:00Z').toLocaleDateString('en-US',{month:'short',day:'numeric',year:'numeric',timeZone:'UTC'});
const monthNames=['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec'];
const plural=(n,label)=>n+' '+label+(n===1?'':'s');
const json=async path=>{const r=await fetch(path);if(!r.ok)throw Error('Could not load '+path);return r.json()};
const csv=async path=>{
 const r=await fetch(path);if(!r.ok)throw Error('Could not load '+path);
 const text=(await r.text()).replace(/\r/g,'').trim();
 const lines=text.split('\n').filter(Boolean);
 const parse=line=>{const out=[];let field='',quoted=false;
  for(let i=0;i<line.length;i++){const ch=line[i];
   if(ch==='"'){if(quoted&&line[i+1]==='"'){field+='"';i++}else quoted=!quoted}
   else if(ch===','&&!quoted){out.push(field);field=''}else field+=ch}
  out.push(field);return out;
 };
 const fields=parse(lines.shift()||'');
 return lines.map(line=>Object.fromEntries(parse(line).map((value,index)=>[fields[index],value])));
};
const sources=[
 ['NBA','../data/games.csv',csv,'../nba/game.html?id='],
 ['College Basketball','../college/data/games.csv',csv,'../college/game.html?id='],
 ['NFL','../nfl/data/games.json',json,'../nfl/game.html?id='],
 ['College Football','../cfb/data/games.json',json,'../cfb/game.html?id='],
 ['Soccer','../soccer/data/matches.json',json,'../soccer/game.html?id='],
 ['MLB','../mlb/data/games.json',json,'../mlb/game.html?id='],
 ['MiLB','../milb/data/games.json',json,'../milb/game.html?id='],
 ['College Baseball','../college-baseball/data/games.json',json,'../college-baseball/game.html?id='],
 ['NHL','../nhl/data/games.json',json,'../nhl/game.html?id=']
];
/* Nominated matches in the Museum Greatest Games directory (not rankings). */
const nominated=[
 ['2006-02-26','NBA'],['2021-02-20','College Baseball'],['2026-06-24','Soccer'],
 ['2007-03-18','NBA'],['2008-01-27','NBA'],['2008-12-06','NBA'],['2010-11-22','NBA'],
 ['2018-02-03','College Basketball'],['2019-02-20','College Basketball'],['2019-11-30','College Basketball'],
 ['2022-11-17','College Basketball'],['2007-11-25','NFL'],['2018-11-10','College Football'],
 ['2003-07-24','MLB'],['2006-06-28','MLB'],['2012-04-06','MLB'],['2013-08-09','MLB'],
 ['2018-09-28','MLB'],['2022-10-18','MLB'],['2018-02-17','College Baseball'],
 ['2019-02-22','College Baseball'],['2020-02-28','College Baseball'],['2022-03-05','College Baseball'],
 ['2022-05-28','College Baseball'],['2022-06-03','College Baseball'],['2024-02-23','College Baseball'],
 ['2025-05-16','College Baseball'],['2025-05-23','College Baseball'],
 ['2026-04-05','College Baseball'],['2026-05-16','College Baseball']
];
const nominationKeys=new Set(nominated.map(([date,sport])=>date+'|'+sport));
const scoreNumber=v=>v!==null&&v!==undefined&&v!==''&&Number.isFinite(Number(v))?Number(v):null;
const canonicalName=v=>String(v??'').trim().replace(/\s+/g,' ');
const venueOf=g=>canonicalName(g.arena||g.ballpark||g.stadium||g.venue||g.venue_official||'');
const memo=(game)=>game.date+'|'+game.sport;
const matchup=g=>g.away+' '+(g.neutral?'vs.':'at')+' '+g.home;
const scoreLine=g=>g.awayScore===null||g.homeScore===null?'Score unavailable':g.away+' '+g.awayScore+' · '+g.home+' '+g.homeScore;
const numFmt=n=>Number(n).toLocaleString('en-US');
let games=[],years=[],byYear=new Map(),current=null;
const monthKey=g=>g.date.slice(0,7);
const page=byId('year-detail');
function groups(rows,key,category){
 const map=new Map();
 rows.forEach(g=>{let entries=key(g);
  if(!Array.isArray(entries))entries=[entries];
  entries.forEach(entry=>{if(!entry)return;const k=(category==='teams'?g.sport+'|':'')+entry.toLowerCase();
   const record=map.get(k)||{name:entry,sport:g.sport,count:0};record.count++;map.set(k,record);
  });
 });
 return [...map.values()].sort((a,b)=>b.count-a.count||a.name.localeCompare(b.name));
}
function tilesForYear(){
 byId('year-shelf-grid').innerHTML=years.map(y=>{
  const data=byYear.get(y),sportCount=new Set(data.map(g=>g.sport)).size;
  return '<button type="button" class="year-tile" data-year="'+esc(y)+'" aria-pressed="'+(y===current)+'" aria-label="Open '+y+', '+plural(data.length,'game')+'">'
   +'<strong>'+esc(y)+'</strong><span>'+numFmt(data.length)+' games attended</span><small>'+plural(sportCount,'sport')+'</small></button>';
 }).join('');
 byId('year-shelf-grid').querySelectorAll('button[data-year]').forEach(btn=>btn.addEventListener('click',()=>{
  selectYear(btn.dataset.year,true);
  page.scrollIntoView({behavior:window.matchMedia('(prefers-reduced-motion: reduce)').matches?'auto':'smooth',block:'start'});
 }));
}
function barRows(items,maxCount){
 return items.map(v=>'<div class="bar-row"><span class="bar-label">'+esc(v.name)+'</span>'
   +'<span class="bar-track"><span class="bar-fill" style="display:block;width:'+Math.round(100*v.count/Math.max(1,maxCount))+'%"></span></span>'
   +'<strong>'+numFmt(v.count)+'</strong></div>').join('');
}
function leaderRows(items,sportDetail){
 return items.length?items.slice(0,6).map(x=>'<div class="leader-row"><span>'+esc(x.name)
  +(sportDetail?' <small style="font-size:10px;font-weight:650;color:#6a8290">· '+esc(x.sport)+'</small>':'')+'</span>'
  +'<strong>'+numFmt(x.count)+' '+(x.count===1?'game':'games')+'</strong></div>').join('')
  :'<p class="mini-caption">No recorded entries for this year.</p>';
}
function memory(kind,title,description,link,cta){
 return '<article class="memory-card"><span class="memory-kind">'+esc(kind)+'</span><h4>'+esc(title)+'</h4>'
 +'<p>'+esc(description)+'</p><a href="'+esc(link)+'">'+esc(cta||'View game ↗')+'</a></article>';
}
function renderMemories(list){
 const first=list[0],last=list[list.length-1];
 const entries=[
  memory('The opening game','The year began here',fmtDate(first.date)+' · '+matchup(first)+' · '+first.sport,first.href),
 ];
 const nominatedGames=list.filter(g=>nominationKeys.has(memo(g)));
 if(nominatedGames.length){
  const show=nominatedGames[0];
  entries.push(memory('Museum nomination','A game with a story',fmtDate(show.date)+' · '+matchup(show)+' · '+show.sport+
  (nominatedGames.length>1?' · '+(nominatedGames.length-1)+' more Museum nominee(s) this year':''),
  '../museum/index.html#greatest-games','Explore Greatest Games ↗'));
 }
 const decided=list.filter(g=>g.awayScore!==null&&g.homeScore!==null&&g.awayScore!==g.homeScore)
  .sort((a,b)=>Math.abs(a.awayScore-a.homeScore)-Math.abs(b.awayScore-b.homeScore)||a.date.localeCompare(b.date));
 if(decided.length){
  const narrow=decided[0],margin=Math.abs(narrow.awayScore-narrow.homeScore);
  entries.push(memory('By the numbers','The narrowest decided finish',fmtDate(narrow.date)+' · '+matchup(narrow)+' · '+narrow.sport+' · '+margin+'-'+(narrow.sport==='MLB'||narrow.sport==='MiLB'||narrow.sport==='College Baseball'?'run':narrow.sport==='Soccer'?'goal':'point')+' margin',narrow.href));
 }
 if(first!==last)entries.push(memory('The closing game','The year ended here',fmtDate(last.date)+' · '+matchup(last)+' · '+last.sport,last.href));
 byId('year-memories').innerHTML=entries.join('');
}
function renderEdition(){
 const list=byYear.get(current);
 byId('edition-title').textContent=current+' · The year you witnessed';
 const idx=years.indexOf(current);
 byId('prev-year').disabled=idx===years.length-1;
 byId('next-year').disabled=idx===0;
 const teams=groups(list,g=>[g.away,g.home],'teams'),venues=groups(list,g=>g.venue,'venues');
 const sportTotals=groups(list,g=>g.sport,'sports');
 byId('year-metrics').innerHTML=[
  [numFmt(list.length),'Games attended'],[sportTotals.length,'Sports represented'],
  [numFmt(teams.length),'Different teams'],[numFmt(venues.length),'Venues visited']
 ].map(([value,label])=>'<div class="metric"><strong>'+esc(value)+'</strong><span>'+esc(label)+'</span></div>').join('');
 byId('sport-breakdown').innerHTML=barRows(sportTotals,Math.max(...sportTotals.map(v=>v.count)))+
  '<p class="mini-caption">Each game counts once in its sport.</p>';
 const months=monthNames.map((name,i)=>({name,count:list.filter(g=>Number(g.date.slice(5,7))===i+1).length}));
 byId('month-bars').innerHTML=barRows(months,Math.max(...months.map(v=>v.count)))+
  '<p class="mini-caption">Calendar months, January through December.</p>';
 byId('team-leaders').innerHTML=leaderRows(teams,true)+
  '<p class="mini-caption">Each game counts for both participating teams; team names remain sport-specific.</p>';
 byId('venue-leaders').innerHTML=leaderRows(venues,false)+
  '<p class="mini-caption">Venues use the names recorded in each game log.</p>';
 renderMemories(list);
 const currentSport=byId('filter-sport').value;
 const sportOptions=[...new Set(list.map(g=>g.sport))].sort((a,b)=>sources.findIndex(x=>x[0]===a)-sources.findIndex(x=>x[0]===b));
 byId('filter-sport').innerHTML='<option value="all">All sports</option>'+sportOptions.map(s=>'<option value="'+esc(s)+'">'+esc(s)+'</option>').join('');
 byId('filter-sport').value=sportOptions.includes(currentSport)?currentSport:'all';
 renderGameList();
}
function renderGameList(){
 const list=byYear.get(current)||[];
 const sport=byId('filter-sport').value,q=byId('filter-query').value.toLowerCase().trim(),direction=byId('filter-order').value;
 const filtered=list.filter(g=>(sport==='all'||g.sport===sport)&&(!q||
  [g.date,g.sport,g.away,g.home,g.venue].join(' ').toLowerCase().includes(q)));
 if(direction==='newest')filtered.reverse();
 byId('games-count').textContent=filtered.length+' of '+list.length+' games';
 if(!filtered.length){byId('games-list').innerHTML='<p class="empty">No attended games match these filters.</p>';return}
 let lastMonth='',output='';
 for(const g of filtered){
  const mk=monthKey(g);
  if(mk!==lastMonth){lastMonth=mk;output+='<h4 class="month-heading">'+esc(new Date(mk+'-15T12:00:00Z').toLocaleDateString('en-US',{year:'numeric',month:'long',timeZone:'UTC'}))+'</h4>';}
  output+='<article class="game-item">'
   +'<time datetime="'+esc(g.date)+'">'+esc(fmtDate(g.date))+'</time>'
   +'<div class="game-description"><span class="game-sport">'+esc(g.sport)+'</span>'
   +'<span class="game-matchup">'+esc(matchup(g))+'</span>'
   +'<span class="game-result">'+esc(scoreLine(g))+'</span></div>'
   +'<div class="game-venue">'+esc(g.venue||'Venue not recorded')
   +(nominationKeys.has(memo(g))?'<span class="museum-flag">★ Museum nominee</span>':'')+'</div>'
   +'<a class="game-link" href="'+esc(g.href)+'" aria-label="View game: '+esc(matchup(g))+'">View game ↗</a>'
   +'</article>';
 }
 byId('games-list').innerHTML=output;
}
function selectYear(year,historyUpdate){
 if(!byYear.has(year))return;
 current=year;
 byId('year-shelf-grid').querySelectorAll('button[data-year]').forEach(btn=>btn.setAttribute('aria-pressed',String(btn.dataset.year===year)));
 renderEdition();
 if(historyUpdate){
  const url=new URL(window.location.href);url.searchParams.set('year',year);
  window.history.pushState({year:year},'',url.pathname+url.search+url.hash);
 }
}
async function init(){
 const loaded=await Promise.all(sources.map(async ([sport,path,loader,prefix],sourceIndex)=>{
  const records=await loader(path);if(!Array.isArray(records))throw Error('Unexpected game list from '+path);
  return records.filter(g=>sport!=='College Baseball'||g.verification!=='attendance_only').map((g,recordIndex)=>{
   const date=String(g.date||''),away=canonicalName(g.away||g.away_team),
    home=canonicalName(g.home||g.home_team),id=sport==='MLB'?g.attendance_id:g.id;
   if(!/^\d{4}-\d{2}-\d{2}$/.test(date)||!id||!away||!home)return null;
   return {sport,date,year:date.slice(0,4),away,home,venue:venueOf(g),
    awayScore:scoreNumber(g.away_score),homeScore:scoreNumber(g.home_score),
    href:prefix+encodeURIComponent(String(id)),neutral:!!g.neutral_site||g.site_type==='neutral',
    sourceIndex,recordIndex};
  }).filter(Boolean);
 }));
 games=loaded.flat().sort((a,b)=>a.date.localeCompare(b.date)||a.sourceIndex-b.sourceIndex||a.recordIndex-b.recordIndex);
 byYear=new Map();
 games.forEach(g=>{if(!byYear.has(g.year))byYear.set(g.year,[]);byYear.get(g.year).push(g)});
 years=[...byYear.keys()].sort((a,b)=>b.localeCompare(a));
 if(!years.length)throw Error('There are no dated attended games in the eight archives.');
 const from=years[years.length-1],to=years[0];
 byId('hero-years').textContent=years.length;
 byId('hero-range').textContent=from+'–'+to;
 byId('yearbook-data-note').textContent=numFmt(games.length)+' attended games currently indexed across '+plural(years.length,'calendar year')+
  '. Entries use all nine sport logs; college baseball excludes attendance-only records, matching homepage milestones. Same-day games use archive/source order when start times are unavailable.';
 const requested=new URLSearchParams(location.search).get('year');
 current=byYear.has(requested)?requested:years[0];
 tilesForYear();renderEdition();
 byId('prev-year').addEventListener('click',()=>{const previous=years[years.indexOf(current)+1];if(previous)selectYear(previous,true)});
 byId('next-year').addEventListener('click',()=>{const next=years[years.indexOf(current)-1];if(next)selectYear(next,true)});
 for(const key of ['filter-sport','filter-query','filter-order']){
  const field=byId(key);field.addEventListener(key==='filter-query'?'input':'change',renderGameList);
 }
 window.addEventListener('popstate',()=>{const year=new URLSearchParams(location.search).get('year');selectYear(byYear.has(year)?year:years[0],false)});
}
init().catch(err=>{
 console.error('Could not load Courtside Yearbook',err);
 byId('year-shelf-grid').innerHTML='<p class="empty">The annual editions could not be loaded. '+esc(err.message)+' Please refresh to retry.</p>';
 byId('edition-title').textContent='Yearbook temporarily unavailable';
 byId('games-list').innerHTML='<p class="empty">The yearly game log was not loaded.</p>';
 byId('yearbook-data-note').textContent='The Yearbook requires the game logs from all eight sports to load successfully; incomplete counts are not shown.';
});
})();
