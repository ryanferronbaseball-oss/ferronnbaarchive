(()=>{'use strict';
const $=id=>document.getElementById(id),esc=v=>String(v??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const num=v=>Number(v)||0, avg=(h,ab)=>ab?(h/ab).toFixed(3).replace(/^0/,''):'.000',era=(er,outs)=>outs?(er*27/outs).toFixed(2):'—',ip=outs=>Math.floor(outs/3)+'.'+(outs%3);
const fetchData=path=>fetch('./data/'+path,{cache:'no-store'}).then(r=>{if(!r.ok)throw Error('Unable to load '+path);return r.json()});
let players=[];
const logo=id=>'https://www.mlbstatic.com/team-logos/'+encodeURIComponent(id)+'.svg';
function badge(s){return '<span class="school"><img src="'+logo(s.id)+'" alt="'+esc(s.name)+' logo" loading="lazy" onerror="this.style.display=\'none\'"><span>'+esc(s.name)+'</span></span>'}
function table(teams,type){const pitch=type==='p';if(!teams.some(s=>s[type].games.size))return '';
 const heads=pitch?['Team','Games','Innings','ERA','K']:['Team','Games','AVG','HR','RBI'];
 return '<div class="stat-caption">'+(pitch?'Pitching':'Hitting')+'</div><div style="overflow-x:auto"><table class="card-table"><thead><tr>'+heads.map(h=>'<th>'+h+'</th>').join('')+'</tr></thead><tbody>'+teams.filter(s=>s[type].games.size).map(s=>{const a=s[type];return '<tr><td>'+esc(s.name)+'</td><td>'+a.games.size+'</td>'+(pitch?'<td>'+ip(a.outs)+'</td><td>'+era(a.er,a.outs)+'</td><td>'+a.k+'</td>':'<td>'+avg(a.h,a.ab)+'</td><td>'+a.hr+'</td><td>'+a.rbi+'</td>')+'</tr>'}).join('')+'</tbody></table></div>'}
function render(){const q=$('search').value.trim().toLowerCase(),sort=$('sort').value;
 let list=players.filter(p=>(p.name+' '+p.teams.map(t=>t.name).join(' ')).toLowerCase().includes(q));
 list.sort((a,b)=>sort==='name'?a.name.localeCompare(b.name):sort==='schools'?b.teams.length-a.teams.length||b.games-a.games:b.games-a.games||a.name.localeCompare(b.name));
 $('directory').innerHTML=list.map(p=>'<article class="player-card"><div class="card-top"><a class="player-name" href="./player.html?id='+encodeURIComponent(p.id)+'">'+esc(p.name)+'</a><span class="badge">'+p.teams.length+' teams witnessed</span></div><div class="path">'+p.teams.map((s,i)=>(i?'<span class="arrow">→</span>':'')+badge(s)).join('')+'</div>'+table(p.teams,'b')+table(p.teams,'p')+'<div class="card-foot"><span>'+p.games+' games witnessed</span><a href="./player.html?id='+encodeURIComponent(p.id)+'">Full player profile →</a></div></article>').join('')||'<p class="empty">No players match your search.</p>';
}
Promise.all([fetchData('player_stats.json'),fetchData('games.json')]).then(([rows,games])=>{
 const dates=new Map(games.map(g=>[String(g.game_pk),g.date]));
 const byPlayer=new Map();
 for(const r of rows){if(r.player_id==null||r.team_id==null||r.game_pk==null)continue;
  const id=String(r.player_id),teamId=String(r.team_id),key=String(r.game_pk);
  let p=byPlayer.get(id);
  if(!p){p={id,name:r.name||'Unknown player',by:new Map()};byPlayer.set(id,p)}
  let s=p.by.get(teamId);
  if(!s){s={id:teamId,name:r.team||'Unknown team',first:'9999',all:new Set(),b:{games:new Set(),h:0,ab:0,hr:0,rbi:0},p:{games:new Set(),outs:0,er:0,k:0}};p.by.set(teamId,s)}
  const date=dates.get(key)||'9999';if(date<s.first)s.first=date;s.all.add(key);
  const b=r.batting||{};if(num(b.plateAppearances)>0||num(b.atBats)>0){if(!s.b.games.has(key)){s.b.games.add(key);s.b.h+=num(b.hits);s.b.ab+=num(b.atBats);s.b.hr+=num(b.homeRuns);s.b.rbi+=num(b.rbi)}}
  const a=r.pitching||{};if(a.outs!=null||a.inningsPitched!=null){if(!s.p.games.has(key)){s.p.games.add(key);s.p.outs+=num(a.outs);s.p.er+=num(a.earnedRuns);s.p.k+=num(a.strikeOuts)}}
 }
 players=[...byPlayer.values()].map(p=>({...p,teams:[...p.by.values()].sort((a,b)=>a.first.localeCompare(b.first)||a.name.localeCompare(b.name))})).filter(p=>p.teams.length>=3).map(p=>({...p,games:p.teams.reduce((n,s)=>n+s.all.size,0)}));
 $('playerCount').textContent=players.length;
 $('schoolCount').textContent=players.reduce((n,p)=>n+p.teams.length,0);
 $('gameCount').textContent=players.reduce((n,p)=>n+p.games,0);
 render();
}).catch(e=>{$('directory').innerHTML='<p class="empty">'+esc(e.message)+'</p>'});
$('search').addEventListener('input',render);$('sort').addEventListener('change',render);
const navReady=()=>{if(window.MLBArchive?.nav){$('navigation').innerHTML=window.MLBArchive.nav('multiple-teams')}else setTimeout(navReady,25)};navReady();
})();