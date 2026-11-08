/* Museum game-gallery nominations. Only approved stories are published as full exhibits. */
(()=>{'use strict';
const candidates=[
 ['2007-03-18','Minnesota Timberwolves','Los Angeles Lakers','NBA'],
 ['2008-01-27','Cleveland Cavaliers','Los Angeles Lakers','NBA'],
 ['2008-12-05','Utah Jazz','Phoenix Suns','NBA'],
 ['2010-11-22','New Orleans Hornets','Los Angeles Clippers','NBA'],
 ['2018-02-03',"Saint Mary's",'San Diego','College Basketball'],
 ['2019-02-20','Nevada','San Diego State','College Basketball'],
 ['2019-11-30','Eastern Michigan','UC Irvine','College Basketball'],
 ['2022-11-17','Utah State','San Diego','College Basketball'],
 ['2007-11-25','San Francisco 49ers','Arizona Cardinals','NFL'],
 ['2018-11-10','Davidson','San Diego','College Football'],
 ['2003-07-24','Colorado Rockies','Los Angeles Dodgers','MLB'],
 ['2006-06-28','Atlanta Braves','New York Yankees','MLB'],
 ['2012-04-06','Kansas City Royals','Los Angeles Angels','MLB'],
 ['2013-08-09','Tampa Bay Rays','Los Angeles Dodgers','MLB'],
 ['2018-09-28','Arizona Diamondbacks','San Diego Padres','MLB'],
 ['2022-10-18','Philadelphia Phillies','San Diego Padres','MLB'],
 ['2018-02-17','California','San Diego','College Baseball'],
 ['2019-02-22','Oklahoma','San Diego','College Baseball'],
 ['2020-02-28','Monmouth','San Diego','College Baseball'],
 ['2022-03-05','Dallas Baptist','San Diego','College Baseball'],
 ['2022-05-28','San Diego','Gonzaga','College Baseball','neutral'],
 ['2022-06-03','San Diego','Vanderbilt','College Baseball','neutral'],
 ['2024-02-23','Iowa','Auburn','College Baseball','neutral'],
 ['2025-05-18','Oregon','Iowa','College Baseball'],
 ['2025-05-23','Texas A&M','LSU','College Baseball','neutral'],
 ['2026-04-05','LSU','Tennessee','College Baseball'],
 ['2026-05-16','Arkansas','Kentucky','College Baseball']
].map(([date,away,home,sport,site])=>({date,away,home,sport,site}));
const stories={
 '2007-03-18':{
  title:'Kobe’s historic streak meets Garnett’s Timberwolves',
  score:'Los Angeles Lakers 109 · Minnesota Timberwolves 102',
  venue:'Staples Center · Los Angeles, California',
  image:'./timberwolves-lakers-2007.webp',
  caption:'MARCH 18, 2007 · KOBE BRYANT AND KEVIN GARNETT',
  game:'../nba/game.html?id=7',
  paragraphs:[
   'March 18, 2007, featured an extraordinary battle between two of the NBA’s defining superstars in their primes, Kobe Bryant and Kevin Garnett, as the Los Angeles Lakers defeated the Minnesota Timberwolves 109–102 at Staples Center.',
   'Bryant delivered a remarkable 50-point performance, shooting 17-for-35 from the field, 4-for-9 from three-point range, and 12-for-14 at the free-throw line. He added six rebounds, three assists, and three steals in the victory. The performance marked the second of four consecutive games in which Bryant scored at least 50 points, placing this night in the middle of one of the most extraordinary scoring stretches in NBA history.',
   'Minnesota countered with outstanding performances of its own. Garnett showcased his exceptional all-around abilities, finishing with 26 points, 15 rebounds, six assists, and three blocks while shooting 9-for-16 from the field. Ricky Davis was equally impressive, leading the Timberwolves with 33 points, six rebounds, and six assists while connecting on four three-pointers.',
   'With three players delivering exceptional statistical performances, two generational talents competing at the height of their careers, and Bryant making history during his legendary scoring streak, this game stands as one of the defining early experiences of the Courtside Archive.'
  ],
  photoAlt:'Kobe Bryant at the rim with Kevin Garnett nearby during the March 18, 2007 Lakers and Timberwolves game',
  columns:['PTS','REB','AST','More'],
  players:[['Kobe Bryant','50','6','3','3 steals · 4 threes'],['Kevin Garnett','26','15','6','3 blocks'],['Ricky Davis','33','6','6','4 threes']]
 },
 '2026-05-16':{
  title:'A ten-run opening, a nine-run comeback, and 28 runs',
  score:'Arkansas 16 · Kentucky 12',
  venue:'Kentucky Proud Park · Lexington, Kentucky',
  image:'./arkansas-kentucky-2026.webp',
  photoAlt:'Arkansas players celebrating during the May 16, 2026 game against Kentucky',
  caption:'MAY 16, 2026 · ARKANSAS AT KENTUCKY',
  game:'../college-baseball/game.html?id=cb-2026-05-16-arkansas-kentucky-att0424',
  paragraphs:[
   'What began with a 40-minute rain delay turned into one of the wildest offensive games in Courtside Archive history, as Arkansas outlasted Kentucky 16–12 in an extraordinary back-and-forth contest at Kentucky Proud Park on May 16, 2026.',
   'The Razorbacks wasted absolutely no time taking control, exploding for 10 runs in the top of the first inning. Kentucky was forced to use three pitchers just to escape the opening frame, and by the top of the fourth, Arkansas had built a seemingly insurmountable 12–2 advantage.',
   'But the Wildcats were far from finished. In an astonishing fifth-inning rally, Kentucky erupted for nine runs in the bottom half, completing an unlikely comeback to tie the game at 12. What had appeared to be a blowout suddenly became a dramatic contest with both teams fighting for control.',
   'Arkansas ultimately regained the advantage, scoring twice in the sixth inning before adding two insurance runs in the ninth to secure the 16–12 victory. Zack Stewart led the Razorbacks’ offensive attack with four hits in six at-bats, including two doubles, a home run, and four RBI. Kentucky’s Jayce Tharnish delivered an impressive performance of his own, going 3-for-6 with a home run and three RBI.',
   'With 28 combined runs, enormous momentum swings, and one of the most improbable rallies witnessed in the Archive, this game stands as an unforgettable example of how quickly a college baseball game can change. From a ten-run opening inning to a stunning comeback and a final Arkansas response, nearly every chapter of this contest delivered something extraordinary.'
  ],
  columns:['H-AB','2B','HR','RBI'],
  players:[['Zack Stewart','4-6','2','1','4'],['Jayce Tharnish','3-6','1','1','3']]
 }
};
const root=document.getElementById('greatestGamesList'),sportEl=document.getElementById('greatestGamesSport'),sortEl=document.getElementById('greatestGamesSort'),searchEl=document.getElementById('greatestGamesSearch'),countEl=document.getElementById('greatestGamesCount');
if(!root)return;
const esc=v=>String(v).replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const formatDate=date=>new Date(date+'T12:00:00Z').toLocaleDateString('en-US',{month:'long',day:'numeric',year:'numeric',timeZone:'UTC'});
const expanded=new Set();
const label=g=>g.site==='neutral'?`${g.away} vs. ${g.home}`:`${g.away} @ ${g.home}`;
function content(g){const s=stories[g.date];if(!s)return `<div class="gg-pending"><p>This game has been nominated for the permanent collection. Its story, selected performances, photograph and box-score link will be added after review.</p></div>`;
 return `<div class="gg-story-layout"><figure class="gg-photo"><img src="${esc(s.image)}" alt="${esc(s.photoAlt)}" loading="lazy"><figcaption>${esc(s.caption)}</figcaption></figure><div class="gg-narrative"><span class="eyebrow">THE GAME STORY</span><h3>${esc(s.title)}</h3><p class="gg-final">${esc(s.score)}</p><p class="gg-venue">${esc(s.venue)}</p>${s.paragraphs.map(p=>`<p>${esc(p)}</p>`).join('')}</div></div><div class="gg-performances"><h4>Featured performances</h4><div class="gg-table-wrap"><table><thead><tr><th>Player</th>${s.columns.map(v=>`<th>${esc(v)}</th>`).join('')}</tr></thead><tbody>${s.players.map(p=>`<tr><th scope="row">${esc(p[0])}</th>${p.slice(1).map(v=>`<td>${esc(v)}</td>`).join('')}</tr>`).join('')}</tbody></table></div><a class="gg-box-link" href="${esc(s.game)}">View Courtside Archive box score ↗</a></div>`;
}
function render(){root.querySelectorAll('details[open]').forEach(d=>expanded.add(d.dataset.date));
 const sport=sportEl.value,order=sortEl.value,q=searchEl.value.toLowerCase().trim();const matches=candidates.filter(g=>(sport==='all'||g.sport===sport)&&`${g.away} ${g.home} ${g.sport} ${g.date}`.toLowerCase().includes(q)).sort((a,b)=>order==='oldest'?a.date.localeCompare(b.date):b.date.localeCompare(a.date));
 const completed=Object.keys(stories).length;countEl.textContent=`${matches.length} of ${candidates.length} games · ${completed} completed ${completed===1?'story':'stories'}`;
 root.innerHTML=matches.length?matches.map(g=>{const s=stories[g.date],icon=g.sport==='NBA'||g.sport==='College Basketball'?'🏀':g.sport==='NFL'||g.sport==='College Football'?'🏈':'⚾';return `<details class="gg-game ${s?'gg-complete':''}" data-date="${g.date}" ${expanded.has(g.date)?'open':''}><summary><span class="gg-card-image">${s?`<img src="${esc(s.image)}" alt="" loading="lazy">`:`<span class="gg-sport-symbol" aria-hidden="true">${icon}</span>`}<span class="gg-card-year">${g.date.slice(0,4)}</span></span><span class="gg-card-body"><span class="gg-card-sport">${esc(g.sport)}</span><strong>${esc(label(g))}</strong><span class="gg-date">${formatDate(g.date)}</span><small>${s?esc(s.score):'Story pending'}</small><span class="gg-card-action">${s?'Explore game story':'View nomination'} <span aria-hidden="true">↗</span></span></span></summary><div class="gg-content">${content(g)}</div></details>`}).join(''):'<p class="gg-empty">No nominated games match these filters.</p>';
 root.querySelectorAll('details').forEach(d=>d.addEventListener('toggle',()=>{if(d.open)expanded.add(d.dataset.date);else expanded.delete(d.dataset.date)}));
}
[sportEl,sortEl,searchEl].forEach(el=>el.addEventListener(el===searchEl?'input':'change',render));render();
})();
