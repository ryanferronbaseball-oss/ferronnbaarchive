/* Coach History: verified head-coach/manager rules joined to personally attended games. */
(()=>{'use strict';
const $=id=>document.getElementById(id);
const esc=s=>String(s??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const norm=s=>String(s||'').normalize('NFKD').replace(/[\u0300-\u036f]/g,'').replace(/[^a-z0-9]+/gi,' ').trim().toLowerCase();
const slug=s=>norm(s).replace(/\s+/g,'-');
const dateLabel=s=>new Date(s+'T12:00:00Z').toLocaleDateString('en-US',{month:'short',day:'numeric',year:'numeric',timeZone:'UTC'});
const sports=['NBA','College Basketball','NFL','College Football','MLB','College Baseball','MiLB','Soccer'];
const scopedSport=document.body.dataset.sport||'all';
const assignmentPath=document.body.dataset.assignmentPath||'./data/verified-assignments.json';
const feeds=[
 {sport:'NBA',url:'../data/games.csv',format:'csv',id:'id',away:'away',home:'home',urlPrefix:'../nba/game.html?id='},
 {sport:'College Basketball',url:'../college/data/games.csv',format:'csv',id:'id',away:'away',home:'home',urlPrefix:'../college/game.html?id='},
 {sport:'NFL',url:'../nfl/data/games.json',id:'id',away:'away',home:'home',urlPrefix:'../nfl/game.html?id='},
 {sport:'College Football',url:'../cfb/data/games.json',id:'id',away:'away',home:'home',urlPrefix:'../cfb/game.html?id='},
 {sport:'MLB',url:'../mlb/data/games.json',id:'attendance_id',away:'away',home:'home',urlPrefix:'../mlb/game.html?id='},
 {sport:'College Baseball',url:'../college-baseball/data/games.json',id:'id',away:'away',home:'home',urlPrefix:'../college-baseball/game.html?id='},
 {sport:'MiLB',url:'../milb/data/games.json',id:'id',away:'away_team',home:'home_team',urlPrefix:'../milb/game.html?id='},
 {sport:'Soccer',url:'../soccer/data/matches.json',id:'id',away:'away',home:'home',urlPrefix:'../soccer/game.html?id='}
];
// Small CSV reader supporting quoted team names and both LF and CRLF archives.
function readCSV(str){const rows=[];let row=[],value='',quoted=false;
 for(let i=0;i<str.length;i++){const ch=str[i];if(ch==='"'){if(quoted&&str[i+1]==='"'){value+='"';i++}else quoted=!quoted}
 else if(ch===','&&!quoted){row.push(value);value=''}else if((ch==='\n'||ch==='\r')&&!quoted){if(ch==='\r'&&str[i+1]==='\n')i++;row.push(value);if(row.some(Boolean))rows.push(row);row=[];value=''}else value+=ch}
 if(value||row.length){row.push(value);rows.push(row)}const [keys,...data]=rows;return data.map(a=>Object.fromEntries(keys.map((k,i)=>[k,a[i]??''])))}
let coaches=[],allCoaches=[],coverage={},loaded=false;
const enriched=c=>{c.rows.sort((a,b)=>a.date.localeCompare(b.date)||a.sport.localeCompare(b.sport));c.games=c.rows.length;c.wins=c.rows.filter(r=>r.result==='W').length;c.losses=c.rows.filter(r=>r.result==='L').length;c.ties=c.rows.filter(r=>r.result==='T').length;c.decisions=c.wins+c.losses;c.pct=c.decisions?c.wins/c.decisions:0;c.sports=[...new Set(c.rows.map(r=>r.sport))];c.teams=[...new Set(c.rows.map(r=>r.team))];c.sources=new Set(c.rows.map(r=>r.source));return c};
async function fetchData(){const ruleResponse=await fetch(assignmentPath,{cache:'no-store'});if(!ruleResponse.ok)throw Error('Coaching assignment index unavailable');const index=await ruleResponse.json();const rules=index.rules;
 const results=await Promise.allSettled(feeds.map(async f=>{const r=await fetch(f.url,{cache:'no-store'});if(!r.ok)throw Error(f.sport+' games unavailable ('+r.status+')');const raw=f.format==='csv'?readCSV(await r.text()):await r.json();return raw.map(g=>({sport:f.sport,id:String(g[f.id]),date:g.date,away:g[f.away],home:g[f.home],awayScore:g.away_score,homeScore:g.home_score,url:f.urlPrefix+encodeURIComponent(g[f.id])})).filter(g=>g.date&&g.away&&g.home)}));
 const byCoach=new Map(),cov={},errors=[];let gameCount=0,verified=0,total=0;
 for(let i=0;i<feeds.length;i++){const sport=feeds[i].sport,result=results[i];if(result.status==='rejected'){errors.push(result.reason.message);cov[sport]={complete:0,total:0,error:true};continue}const games=result.value;gameCount+=games.length;cov[sport]={complete:0,total:games.length*2};total+=games.length*2;
  for(const g of games)for(const side of ['away','home']){
   const team=g[side],matching=rules.filter(r=>r.sport===sport&&norm(r.team)===norm(team)&&g.date>=r.from&&g.date<=r.to);
   if(matching.length!==1)continue; // Conflicts and unresolved historical appointments are not counted.
   const rule=matching[0];verified++;cov[sport].complete++;
   const id=slug(rule.coach);if(!byCoach.has(id))byCoach.set(id,{id,name:rule.coach,rows:[],sources:new Set()});const c=byCoach.get(id);
   const own=Number(g[side+'Score']),opp=Number(g[side==='home'?'awayScore':'homeScore']);
   const scored=g[side+'Score']!==''&&g[side+'Score']!=null&&g[side==='home'?'awayScore':'homeScore']!==''&&g[side==='home'?'awayScore':'homeScore']!=null&&Number.isFinite(own)&&Number.isFinite(opp);
   const resultText=!scored?'—':own>opp?'W':own<opp?'L':'T';
   c.rows.push({sport,team,side,date:g.date,opponent:g[side==='home'?'away':'home'],score:scored?`${own}–${opp}`:'—',result:resultText,url:g.url,gameId:g.id,source:rule.source});c.sources.add(rule.source);
  }
 }
 allCoaches=[...byCoach.values()].map(enriched);coaches=scopedSport==='all'?allCoaches:allCoaches.filter(c=>c.sports.includes(scopedSport)).map(c=>enriched({...c,rows:c.rows.filter(r=>r.sport===scopedSport)}));coverage=cov;loaded=true;
 const displayed=scopedSport==='all'?{complete:verified,total,games:gameCount}:{...(cov[scopedSport]||{complete:0,total:0}),games:(cov[scopedSport]?.total||0)/2};
 $('coachTotal').textContent=coaches.length.toLocaleString();$('appearanceTotal').textContent=displayed.complete.toLocaleString();$('gameTotal').textContent=displayed.games.toLocaleString();$('coverageTotal').textContent=displayed.total?`${Math.round(100*displayed.complete/displayed.total)}%`:'—';
 if(errors.length){const note=document.querySelector('.research-note');note.insertAdjacentHTML('beforeend','<p><strong>Loading note:</strong> '+esc(errors.join('; '))+'</p>')}
 render();renderCoverage();const selected=new URLSearchParams(location.search).get('coach');if(selected)showProfile(selected,false);
}
function render(){if(!loaded)return;const sport=$('sportFilter')?.value||scopedSport,term=norm($('searchFilter').value),sort=$('sortFilter').value;const list=coaches.filter(c=>(sport==='all'||c.sports.includes(sport))&&norm(c.name+' '+c.teams.join(' ')).includes(term)).sort((a,b)=>sort==='name'?a.name.localeCompare(b.name):sort==='wins'?b.wins-a.wins||b.games-a.games:sort==='pct'?((b.decisions>=3?b.pct:-1)-(a.decisions>=3?a.pct:-1))||b.games-a.games:b.games-a.games||b.wins-a.wins||a.name.localeCompare(b.name));
 $('shownCount').textContent=`${list.length} of ${coaches.length} verified coaches`;
 $('coachGrid').innerHTML=list.length?list.map(c=>`<article class="coach-card"><span class="badge">${esc(c.sports.join(' · '))}</span><h3>${esc(c.name)}</h3><div class="teams">${esc(c.teams.join(' · '))}</div><div class="record"><div><strong>${c.games}</strong><span>Games</span></div><div><strong>${c.wins}–${c.losses}${c.ties?'–'+c.ties:''}</strong><span>W–L${c.ties?'–T':''}</span></div><div><strong>${c.decisions?c.pct.toFixed(3).replace(/^0/,''): '—'}</strong><span>Win pct.</span></div></div><a class="card-link" href="?coach=${encodeURIComponent(c.id)}#profile" data-coach="${esc(c.id)}">View coaching history ↗</a></article>`).join(''):'<p class="empty">No verified coaches match that filter. The historical assignment audit is still in progress.</p>';
 $('coachGrid').querySelectorAll('[data-coach]').forEach(a=>a.addEventListener('click',e=>{e.preventDefault();showProfile(a.dataset.coach,true)}));
}
function showProfile(id,push){const c=coaches.find(x=>x.id===id);if(!c)return;const node=$('profile');const spans=new Map();for(const row of c.rows){const k=row.sport+'|'+row.team;if(!spans.has(k))spans.set(k,[]);spans.get(k).push(row.date)}
 node.innerHTML=`<div class="profile-head"><div><span class="badge">VERIFIED COACH HISTORY</span><h2>${esc(c.name)}</h2><p class="subtitle">${esc(c.sports.join(' · '))} · ${c.games} attended ${c.games===1?'game':'games'} · ${dateLabel(c.rows[0].date)} – ${dateLabel(c.rows.at(-1).date)}</p></div><a href="#directory" class="profile-close" id="profileClose">Close exhibit ↑</a></div><div class="profile-stats"><div class="stat"><strong>${c.games}</strong><small>Games witnessed</small></div><div class="stat"><strong>${c.wins}</strong><small>Wins</small></div><div class="stat"><strong>${c.losses}</strong><small>Losses</small></div><div class="stat"><strong>${c.decisions?c.pct.toFixed(3).replace(/^0/,''): '—'}</strong><small>Win percentage</small></div></div><h3>Teams witnessed</h3><div class="tenure">${[...spans].map(([key,dates])=>{const [sport,team]=key.split('|');return `<span>${esc(team)} · ${esc(sport)} · ${dates[0].slice(0,4)}${dates.at(-1).slice(0,4)!==dates[0].slice(0,4)?'–'+dates.at(-1).slice(0,4):''}</span>`}).join('')}</div><h3>Attended games</h3><div class="game-table-wrap"><table class="game-table"><thead><tr><th>Date</th><th>Sport</th><th>Team</th><th>Opponent</th><th>W/L</th><th>Score</th><th>Box score</th></tr></thead><tbody>${c.rows.map(r=>`<tr><td>${dateLabel(r.date)}</td><td>${esc(r.sport)}</td><td>${esc(r.team)}</td><td>${esc(r.opponent)}</td><td><span class="result ${r.result==='W'?'win':r.result==='L'?'loss':''}">${esc(r.result)}</span></td><td>${esc(r.score)}</td><td><a href="${esc(r.url)}">View ↗</a></td></tr>`).join('')}</tbody></table></div><h3>Assignment sources</h3><ul class="sources">${[...c.sources].map((s,i)=>`<li><a href="${esc(s)}" target="_blank" rel="noopener noreferrer">Verified coaching source ${i+1} ↗</a></li>`).join('')}</ul>`;
 const other=allCoaches.find(x=>x.id===id)?.sports.filter(s=>!c.sports.includes(s))||[];
 if(other.length){const sportLinks={'NBA':'../nba/coaches.html','NFL':'../nfl/coaches.html','MLB':'../mlb/coaches.html'};node.insertAdjacentHTML('beforeend','<h3>Also seen coaching at another level</h3><div class="tenure">'+other.map(s=>'<a class="cross-level-link" href="'+esc((sportLinks[s]||'../coach-history/index.html')+'?coach='+encodeURIComponent(id)+'#profile')+'">'+esc(s)+' coaching history ↗</a>').join('')+'</div>')}
 node.hidden=false;$('profileClose').addEventListener('click',e=>{e.preventDefault();node.hidden=true;if(history.replaceState)history.replaceState(null,'',location.pathname+'#directory');$('directory').scrollIntoView({behavior:'smooth'})});if(push)history.pushState(null,'','?coach='+encodeURIComponent(id)+'#profile');node.scrollIntoView({behavior:'smooth',block:'start'});
}
function renderCoverage(){const grid=$('coverageGrid');grid.innerHTML=(scopedSport==='all'?sports:[scopedSport]).map(s=>{const c=coverage[s]||{complete:0,total:0},pct=c.total?Math.round(100*c.complete/c.total):0;return `<div class="coverage-card"><strong>${esc(s)}</strong><small>${c.error?'Games unavailable':`${c.complete} of ${c.total} team-game positions verified`}</small><div class="bar"><span style="width:${pct}%"></span></div><small>${pct}% covered${c.total?' · '+(c.total-c.complete)+' to research':''}</small></div>`}).join('')}
['sportFilter','sortFilter','searchFilter'].forEach(id=>$(id)?.addEventListener(id==='searchFilter'?'input':'change',render));
fetchData().catch(e=>{$('coachGrid').innerHTML='<p class="empty">Coach History could not load: '+esc(e.message)+'</p>';document.querySelector('.research-note').insertAdjacentHTML('beforeend','<p>Please retry after the archive data becomes available.</p>')});
})();
