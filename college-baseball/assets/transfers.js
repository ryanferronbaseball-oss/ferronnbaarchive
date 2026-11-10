(()=>{'use strict';
const $=id=>document.getElementById(id),esc=x=>String(x??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const num=x=>Number(x)||0,ave=(h,ab)=>ab?(h/ab).toFixed(3).replace(/^0/, ''):'.000',era=(er,outs)=>outs?(er*27/outs).toFixed(2):'—',ip=outs=>Math.floor(outs/3)+'.'+outs%3;
const get=name=>fetch('./data/'+name,{cache:'no-store'}).then(r=>{if(!r.ok)throw Error('Unable to load '+name);return r.json()});
let players=[],logos=new Map();
const norm=s=>String(s||'').toLowerCase().replace(/[^a-z0-9]/g,'');
function mark(s){const id=logos.get(norm(s.name));return id?'<img src="https://a.espncdn.com/i/teamlogos/ncaa/500/'+encodeURIComponent(id)+'.png" alt="'+esc(s.name)+' logo" loading="lazy" onerror="this.replaceWith(document.createTextNode(\''+esc(s.name.split(' ').map(w=>w[0]).join('').slice(0,3))+'\'))">':'<strong aria-hidden="true">'+esc(s.name.split(' ').map(w=>w[0]).join('').slice(0,3))+'</strong>'}
function statTable(schools,side){let any=schools.some(s=>s[side].g.size);if(!any)return '';
 const pitch=side==='p',headers=pitch?['School','Games','Innings','ERA','K']:['School','Games','AVG','HR','RBI'];
 return '<div class="stat-caption">'+(pitch?'Pitching':'Hitting')+'</div><table class="card-table"><thead><tr>'+headers.map(x=>'<th>'+x+'</th>').join('')+'</tr></thead><tbody>'+schools.filter(s=>s[side].g.size).map(s=>{const a=s[side];return '<tr><td>'+esc(s.name)+'</td><td>'+a.g.size+'</td>'+(pitch?'<td>'+ip(a.outs)+'</td><td>'+era(a.er,a.outs)+'</td><td>'+a.k+'</td>':'<td>'+ave(a.h,a.ab)+'</td><td>'+a.hr+'</td><td>'+a.rbi+'</td>')+'</tr>'}).join('')+'</tbody></table>'}
function render(){const q=$('search').value.trim().toLowerCase(),sort=$('sort').value;let list=players.filter(p=>(p.name+' '+p.schools.map(s=>s.name).join(' ')).toLowerCase().includes(q));list.sort((a,b)=>sort==='name'?a.name.localeCompare(b.name):sort==='schools'?b.schools.length-a.schools.length||b.games-a.games:b.games-a.games||a.name.localeCompare(b.name));
 $('directory').innerHTML=list.map(p=>'<article class="player-card"><div class="card-top"><a class="player-name" href="./player.html?id='+encodeURIComponent(p.id)+'">'+esc(p.name)+'</a><span class="badge">'+p.schools.length+' schools witnessed</span></div><div class="path">'+p.schools.map((s,i)=>(i?'<span class="arrow">→</span>':'')+'<span class="school">'+mark(s)+'<span>'+esc(s.name)+'</span></span>').join('')+'</div>'+statTable(p.schools,'b')+statTable(p.schools,'p')+'<div class="card-foot"><span>'+p.games+' games witnessed</span><a href="./player.html?id='+encodeURIComponent(p.id)+'">Full player profile →</a></div></article>').join('')||'<p class="empty">No transfer connections match your search.</p>'}
Promise.all([get('player_stats.json'),get('player_identity_crosswalk.json'),get('games.json'),get('attendance_game_corrections.json'),get('team_logo_ids.json')]).then(([rows,cross,games,fixes,teams])=>{
 for(const fix of fixes.games||[]){const cols=fix.batting_columns||[];for(const [team,batters] of Object.entries(fix.batting||{}))for(const vals of batters){const b=Object.fromEntries(cols.map((k,i)=>[k,vals[i]]));if(!['Michael Graziano','Jett Lovett'].includes(b.player))continue;rows.push({game_id:fix.game.id,team,player_id:'cb-'+norm(team).replace('georgiatech','georgia-tech')+'-'+b.player.toLowerCase().replace(/[^a-z0-9]+/g,'-'),batting:b})}games.push(fix.game)}
 logos=new Map(Object.entries(teams).map(([name,id])=>[norm(name),id]));
 const dates=new Map(games.map(g=>[g.id,g.date]));const owners=new Map();const links=new Map();
 for(const m of cross.merges||[]){if(!m.canonical_id||!m.pairs||m.pairs.length<2)continue;const p={id:m.canonical_id,name:m.display_name||m.name,by:new Map()};owners.set(m.canonical_id,p);for(const pair of m.pairs)links.set(pair.team+'|'+pair.source_player_id,m.canonical_id)}
 for(const r of rows){const id=links.get(r.team+'|'+r.player_id);if(!id)continue;const p=owners.get(id);if(!p.by.has(r.team))p.by.set(r.team,{name:r.team,first:'9999',all:new Set(),b:{g:new Set(),h:0,ab:0,hr:0,rbi:0},p:{g:new Set(),outs:0,er:0,k:0}});const s=p.by.get(r.team),date=dates.get(r.game_id)||'9999';if(date<s.first)s.first=date;s.all.add(r.game_id);
  if(r.batting){const b=r.batting;s.b.g.add(r.game_id);s.b.h+=num(b.hits);s.b.ab+=num(b.atBats);s.b.hr+=num(b.homeRuns);s.b.rbi+=num(b.rbi)}
  if(r.pitching){const a=r.pitching;s.p.g.add(r.game_id);s.p.outs+=num(a.outs);s.p.er+=num(a.earnedRuns);s.p.k+=num(a.strikeOuts)}
 }
 players=[...owners.values()].map(p=>({...p,schools:[...p.by.values()].sort((a,b)=>a.first.localeCompare(b.first)),games:[...p.by.values()].reduce((v,s)=>v+s.all.size,0)})).filter(p=>p.schools.length>1);
 $('playerCount').textContent=players.length;$('schoolCount').textContent=players.reduce((n,p)=>n+p.schools.length,0);$('gameCount').textContent=players.reduce((n,p)=>n+p.games,0);render();
}).catch(e=>{$('directory').innerHTML='<p class="empty">'+esc(e.message)+'</p>'});
$('search').addEventListener('input',render);$('sort').addEventListener('change',render);
})();
