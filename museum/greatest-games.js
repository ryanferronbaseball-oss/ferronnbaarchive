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
 ['2025-05-16','Oregon','Iowa','College Baseball'],
 ['2025-05-23','Texas A&M','LSU','College Baseball','neutral'],
 ['2026-04-05','LSU','Tennessee','College Baseball'],
 ['2026-05-16','Arkansas','Kentucky','College Baseball']
].map(([date,away,home,sport,site])=>({date,away,home,sport,site}));
const stories={
 '2022-11-17':{
  title:'Eric Williams Jr. scores a school-record 43 in an overtime thriller',
  score:'Utah State 91 · San Diego 89 · Overtime',
  venue:'Jenny Craig Pavilion · San Diego, California',
  image:'./utah-state-san-diego-2022.webp',
  photoAlt:'San Diego forward Eric Williams Jr., number 50, celebrating with his teammates during the Utah State game',
  caption:'NOVEMBER 17, 2022 · UTAH STATE AT SAN DIEGO · ERIC WILLIAMS JR.',
  game:'../college/game.html?id=59',
  paragraphs:[
   'November 17, 2022, produced one of the greatest individual basketball performances in Courtside Archive history, as San Diego’s Eric Williams Jr. scored a school-record 43 points in a thrilling 91–89 overtime loss to Utah State at Jenny Craig Pavilion.',
   'Williams Jr. delivered an extraordinary offensive performance, shooting 13-for-20 from the field, 7-for-8 from three-point range, and 10-for-13 at the free-throw line. He also collected 13 rebounds, recording a remarkable 43-point double-double. His scoring total surpassed the previous San Diego single-game record of 40 points, established by Robert “Pinky” Smith in 1972.',
   'The game itself was a back-and-forth battle featuring 15 lead changes and 10 ties. San Diego jumped to an early 9–0 advantage, but Utah State responded to keep the contest close throughout the evening. With the Toreros trailing in the closing seconds of regulation, Williams Jr. hit a spectacular fadeaway three-pointer from the corner with 2.8 seconds remaining, tying the game at 78 and forcing overtime.',
   'Williams continued his historic night with another three-pointer in the extra period, securing the program scoring record. San Diego’s Marcellus Earlington converted a three-point play with 17 seconds remaining to tie the game at 89, but Utah State’s Steven Ashworth answered with the winning jumper with four seconds left. A final attempt by Sigu Sisoho Jawara missed, sealing a dramatic 91–89 Aggies victory.',
   'Utah State received outstanding contributions from Daniel Akin, who finished with 21 points and 15 rebounds, along with Taylor Funk and Max Shulga, who each scored 20 points. Nevertheless, the night belonged to Williams Jr., whose historic scoring performance and unforgettable game-tying shot made this one of the defining college basketball experiences of the Archive.'
  ],
  columns:['PTS','REB','AST','More'],
  players:[['Eric Williams Jr.','43','13','1','7-for-8 3PT · school record'],['Daniel Akin','21','15','0','7-for-11 FG'],['Taylor Funk','20','6','1','5 threes'],['Max Shulga','20','4','5','5-for-5 3PT'],['Sigu Sisoho Jawara','17','3','3','3 threes']]
 },
 '2022-10-18':{
  title:'An October first and Schwarber’s 488-foot blast',
  score:'Philadelphia Phillies 2 · San Diego Padres 0 · NLCS Game 1',
  venue:'Petco Park · San Diego, California · First MLB postseason game attended',
  image:'./phillies-padres-nlcs-2022.webp',
  photoAlt:'Kyle Schwarber follows through on a swing before a packed Petco Park crowd during the 2022 NLCS',
  caption:'OCTOBER 18, 2022 · PHILLIES AT PADRES · NLCS GAME 1',
  game:'../mlb/game.html?id=715731',
  paragraphs:[
   'October 18, 2022, marked a milestone in the Courtside Archive: the first Major League Baseball postseason game attended. With the San Diego Padres hosting the Philadelphia Phillies in Game 1 of the National League Championship Series, Petco Park provided the setting for an unforgettable evening featuring two outstanding starting pitchers and one of the most extraordinary home runs in postseason history.',
   'The game developed into a remarkable pitching duel between Philadelphia’s Zack Wheeler and San Diego’s Yu Darvish. Wheeler was nearly unhittable, throwing seven shutout innings while allowing just one hit and one walk and striking out eight. Darvish was similarly effective, surrendering only three hits and two runs over seven innings while recording seven strikeouts. Neither offense found much success against the opposing starter.',
   'Philadelphia’s first breakthrough came in the fourth inning when Bryce Harper launched a solo home run to left field, giving the Phillies a 1–0 advantage. Two innings later, Kyle Schwarber delivered the moment that would define the evening. Facing Darvish in the sixth, Schwarber crushed a towering solo home run into the upper deck in right field. The ball left his bat at 119.7 mph and traveled a Statcast-projected 488 feet, becoming the longest home run recorded at Petco Park during the Statcast era.',
   'The two home runs accounted for all of Philadelphia’s scoring. Wheeler and the Phillies bullpen combined to limit San Diego to a single hit, securing a 2–0 victory and a 1–0 series advantage.',
   'For the Courtside Archive, this game holds special significance beyond the final score. The first experience of October baseball at the major-league level featured an exceptional duel between two accomplished pitchers, a home run from Bryce Harper, and a historic display of power from Kyle Schwarber. It was a fitting introduction to the atmosphere and intensity of the MLB postseason.'
  ],
  columns:['H-AB / IP','HR / H','RBI / ER','BB / K'],
  players:[['Zack Wheeler (P)','7.0 IP','1 H','0 ER','1 BB · 8 K'],['Yu Darvish (P)','7.0 IP','3 H','2 ER','1 BB · 7 K'],['Kyle Schwarber','2-3','1','1','1 BB'],['Bryce Harper','1-4','1','1','—']]
 },
 '2024-02-23':{
  title:'A late-night showcase of triple-digit velocity and Auburn’s comeback',
  score:'Auburn 7 · Iowa 5',
  venue:'121 Financial Ballpark · Jacksonville, Florida · Jax College Baseball Classic',
  image:'./iowa-auburn-2024.webp',
  photoAlt:'Iowa baseball players huddle on the field beneath the lights during the late-night February 23, 2024 game',
  caption:'FEBRUARY 23, 2024 · IOWA VS. AUBURN · FIRST PITCH 9:28 P.M.',
  game:'../college-baseball/game.html?id=cb-2024-02-23-iowa-auburn-att0235',
  paragraphs:[
   'What was originally scheduled to begin at 6:00 p.m. turned into an unforgettable late-night college baseball experience on February 23, 2024. After a delay of nearly three and a half hours, No. 18 Iowa and No. 14 Auburn finally took the field at 9:28 p.m. in Jacksonville, Florida, for their opening matchup of the Jax College Baseball Classic.',
   'The early innings belonged to Iowa and its electric right-handed starter, Brody Brecht. Featuring a fastball that reached triple-digit velocity, Brecht overwhelmed Auburn’s lineup with 11 strikeouts across six innings, allowing just two hits, two runs (one earned), and four walks. His combination of premium velocity and swing-and-miss stuff made the performance one of the Archive’s most memorable pitching showcases.',
   'Iowa carried a 3–2 advantage into the seventh inning, but Auburn capitalized once Brecht departed. Mason Maners tied the game with a solo home run before Bobby Peirce delivered the decisive blow, a two-run homer that put the Tigers ahead 5–3. Christian Hall, who had already driven in a run against Brecht in the sixth, added a solo home run in the eighth as Auburn extended its lead to 7–3.',
   'Hall finished 2-for-4 with a home run and two RBI, while Peirce’s two-run homer proved to be the game’s defining swing. Auburn’s bullpen also delivered, with John Armstrong and Cam Tilly combining for 4⅔ scoreless innings after the starter exited. Iowa threatened one final time with a two-run home run from Sam Petersen in the ninth, but Auburn held on for the 7–5 victory.',
   'Between the unusually late first pitch, Brecht’s triple-digit fastball and 11-strikeout performance, and Auburn’s dramatic late-inning power surge, this game embodied the unpredictability that makes college baseball so memorable. An evening that began with hours of waiting ended with a showcase of elite talent and an exciting comeback under the Jacksonville lights.'
  ],
  columns:['H-AB / IP','HR / H','RBI / ER','BB / K'],
  players:[['Brody Brecht (P)','6.0 IP','2 H','1 ER','4 BB · 11 K'],['Bobby Peirce','1-4','1','2','—'],['Christian Hall','2-4','1','2','—'],['Mason Maners','1-2','1','1','2 BB'],['Sam Petersen','1-4','1','2','—']]
 },
 '2025-05-16':{
  title:'A record Iowa crowd witnesses Oregon’s four-run comeback',
  score:'Oregon 9 · Iowa 6',
  venue:'Duane Banks Field · Iowa City, Iowa · Record attendance: 3,339',
  image:'./oregon-iowa-2025.webp',
  photoAlt:'Oregon baseball players celebrating in front of the Iowa crowd at Duane Banks Field',
  caption:'MAY 16, 2025 · OREGON AT IOWA · JACOB WALSH',
  game:'../college-baseball/game.html?id=cb-2025-05-16-oregon-iowa-att0348',
  paragraphs:[
   'May 16, 2025, was a historic evening for Iowa baseball, as a record crowd of 3,339 fans packed Duane Banks Field to watch the Hawkeyes face No. 5 Oregon in a pivotal late-season Big Ten matchup. The home crowd had plenty to celebrate early, but the Ducks ultimately delivered a memorable comeback in a 9–6 victory.',
   'After Oregon opened the scoring in the first inning, Iowa seized momentum with three runs in the third and another in the fourth. Back-to-back solo home runs by Caleb Wulf and Daniel Rogers in the fifth extended the Hawkeyes’ advantage to 6–2, putting Iowa in command in front of the largest crowd in the ballpark’s history.',
   'Oregon’s offense, however, refused to go quietly. Jacob Walsh was the centerpiece of the comeback, finishing 3-for-5 with two doubles, a home run, two RBI, and three runs scored. His solo home run in the fifth traveled an estimated 445 feet, while Anson Aroz added a 430-foot home run in the sixth to begin closing the gap.',
   'The decisive blow came in the seventh inning. Oregon erupted for four runs, with Walsh delivering an RBI double before Ryan Cooney’s two-run double gave the Ducks their first lead since the opening innings. Oregon added two insurance runs in the ninth, while its bullpen shut out Iowa over the final four innings.',
   'Walsh’s three extra-base hits, Aroz’s home run, and the Ducks’ late offensive surge made this an exceptional game to witness. Combined with Iowa’s historic attendance and the atmosphere surrounding a pivotal conference series, the evening became a memorable chapter in the Courtside Archive.'
  ],
  columns:['H-AB','2B','HR','RBI'],
  players:[['Jacob Walsh','3-5','2','1','2'],['Anson Aroz','2-3','0','1','1'],['Ryan Cooney','2-4','1','0','2'],['Caleb Wulf','2-4','0','1','2'],['Daniel Rogers','2-4','0','1','1']]
 },
 '2025-05-23':{
  title:'Two LSU aces combine for 16 strikeouts as LaViolette plays through injury',
  score:'LSU 4 · Texas A&M 3',
  venue:'Hoover Metropolitan Stadium · Hoover, Alabama · SEC Tournament quarterfinal',
  image:'./lsu-texas-am-2025.webp',
  photoAlt:'LSU left-hander Kade Anderson pitching during the SEC Tournament',
  caption:'MAY 23, 2025 · TEXAS A&M VS. LSU · KADE ANDERSON',
  game:'../college-baseball/game.html?id=cb-2025-05-23-texas-a-m-lsu-att0361',
  paragraphs:[
   'A rare opportunity to witness two of college baseball’s premier pitchers in the same game made LSU’s 4–3 victory over Texas A&M in the 2025 SEC Tournament quarterfinals an unforgettable entry in the Courtside Archive.',
   'LSU turned to its two aces to cover all nine innings. Kade Anderson delivered a dominant six-inning start, striking out 12 Aggies while allowing four hits, one walk, and three earned runs. Anthony Eyanson, normally a member of LSU’s starting rotation, entered in the seventh and finished the game with three scoreless innings, four strikeouts, and his first save of the season. Together, the pair combined for 16 strikeouts across nine innings, showcasing two exceptional arms on the same night.',
   'Yet perhaps the most remarkable individual story belonged to Texas A&M’s Jace LaViolette. Just one day after suffering a broken left hand against Auburn and undergoing surgery that evening, LaViolette returned to the lineup against two of the nation’s most formidable pitchers. He finished 1-for-3 with two RBI, including an RBI single and a sacrifice fly, accounting for two of Texas A&M’s three runs.',
   'Ethan Frey’s two-run home run in the third inning ultimately provided LSU with the winning margin. The Tigers held on for a 4–3 victory, advancing to the SEC Tournament semifinals. For the Archive, the game represents a remarkable convergence of elite pitching talent and competitive determination, made even more memorable by LaViolette’s courageous performance.'
  ],
  columns:['IP / H','ER','BB / K','Decision / Batting'],
  players:[['Kade Anderson','6.0 / 4','3','1 / 12','Win'],['Anthony Eyanson','3.0 / 2','0','1 / 4','Save'],['Jace LaViolette','—','—','—','1-for-3 · 2 RBI'],['Ethan Frey','—','—','—','2-for-3 · 2B · HR · 3 RBI']]
 },
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
 },
 '2026-04-05':{
  title:'Cade Arrambide hits four home runs in a 12-inning epic',
  score:'LSU 16 · Tennessee 6 · 12 innings',
  venue:'Lindsey Nelson Stadium · Knoxville, Tennessee',
  image:'./lsu-tennessee-2026-arrambide.webp',
  photoAlt:'Cade Arrambide, number 0, celebrating with LSU teammates',
  caption:'APRIL 5, 2026 · LSU AT TENNESSEE · CADE ARRAMBIDE',
  game:'../college-baseball/game.html?id=cb-2026-04-05-lsu-tennessee-att0407',
  paragraphs:[
   'April 5, 2026, produced one of the most extraordinary individual offensive performances in Courtside Archive history, as LSU defeated Tennessee 16–6 in a remarkable 12-inning contest at Lindsey Nelson Stadium in Knoxville.',
   'Tennessee appeared to have the upper hand early, jumping to a 5–0 lead after three innings. LSU gradually battled back, scoring once in the fifth, three times in the seventh, and once in the ninth to force extra innings with the score tied at five.',
   'Both teams exchanged runs in the 11th inning, sending the game into the 12th tied 6–6. What followed was an extraordinary offensive explosion. LSU erupted for 10 runs in the top of the 12th, turning a tightly contested extra-inning battle into a stunning 16–6 victory.',
   'At the center of it all was LSU catcher Cade Arrambide, who delivered one of the greatest single-game hitting performances ever witnessed by the Archive. Arrambide went an incredible 5-for-6 with four home runs, seven RBI, and four runs scored. His extraordinary power display became the defining achievement of an already unforgettable afternoon.',
   'Between the early Tennessee lead, LSU’s relentless comeback, an unprecedented offensive outburst in the 12th inning, and Arrambide’s historic four-home-run performance, this game represents the kind of exceptional sporting experience that the Courtside Archive Museum was created to preserve.'
  ],
  columns:['H-AB','HR','RBI','Runs'],
  players:[['Cade Arrambide','5-6','4','7','4']]
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
