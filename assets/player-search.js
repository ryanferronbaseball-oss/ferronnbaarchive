/* Courtside Archive — shared, sport-scoped player quick search. */
(()=>{
'use strict';
const sport=location.pathname.split('/').filter(Boolean)[0];
const sources={
 mlb:{url:'./data/player_stats.json',name:'name',id:'player_id'},
 nba:{url:'../data/player_boxscores_espn.json',name:'player',id:'player_id'},
 college:{url:'./data/player_boxscores_espn.json',name:'player',id:'player_id'},
 nfl:{url:'./data/player_stats.json',name:'player',id:'athlete_id'},
 cfb:{url:'./data/player_stats.json',name:'player',id:'athlete_id'}
};
const info=sources[sport];if(!info)return;
const normalize=s=>String(s||'').normalize('NFD').replace(/[\u0300-\u036f]/g,'').toLowerCase().trim();
const profile=p=>(sport==='college'?'./stats.html?player=':'./player.html?id=')+encodeURIComponent(p.id);
const label={mlb:'MLB',nba:'NBA',college:'College basketball',nfl:'NFL',cfb:'College football'}[sport];
function mount(){
 if(document.getElementById('ca-player-quick-search'))return;
 const header=document.querySelector('.archive-header,.ca-header,header.ca-header');
 if(!header){setTimeout(mount,250);return}
 const css=document.createElement('style');css.textContent=`
 #ca-player-quick-search{position:relative;flex:1 1 210px;max-width:300px;min-width:170px;margin-left:auto;font:inherit;z-index:25}
 #ca-player-quick-search input{display:block;width:100%;min-width:0;box-sizing:border-box;border:1px solid #70879a;border-radius:9px;padding:10px 13px;background:#fff;color:#162634;font:500 13px/1.4 system-ui,sans-serif}
 #ca-player-quick-search input:focus{outline:2px solid #69a4cf;outline-offset:2px}
 #ca-player-quick-search .ca-search-results{position:absolute;top:calc(100% + 5px);left:0;right:0;max-height:315px;overflow:auto;background:#fff;border:1px solid #becbd3;border-radius:10px;box-shadow:0 12px 27px #0003;color:#23313a}
 #ca-player-quick-search .ca-search-results[hidden]{display:none!important}
 #ca-player-quick-search .ca-search-results a{display:block;padding:10px 12px;color:#153e63!important;text-decoration:none!important;font:600 13px/1.4 system-ui,sans-serif;border-bottom:1px solid #e3e7e8}
 #ca-player-quick-search .ca-search-results a:hover,#ca-player-quick-search .ca-search-results a:focus{background:#eaf3f7}
 #ca-player-quick-search .ca-search-results small{display:block;color:#697a86;font-weight:400;font-size:11px}
 #ca-player-quick-search .ca-search-message{font:12px/1.5 system-ui,sans-serif;padding:11px;color:#586675}
 @media(max-width:900px){#ca-player-quick-search{flex-basis:100%;max-width:none;order:10;margin:9px 0 0}.archive-header,.ca-header{flex-wrap:wrap}}
 `;
 document.head.appendChild(css);
 const box=document.createElement('div');box.id='ca-player-quick-search';
 box.setAttribute('role','search');box.innerHTML='<input type="search" aria-label="Search '+label+' players" aria-controls="ca-quick-search-results" aria-expanded="false" autocomplete="off" placeholder="Search '+label+' players…"><div id="ca-quick-search-results" class="ca-search-results" hidden></div>';
 header.appendChild(box);
 const input=box.querySelector('input'),panel=box.querySelector('.ca-search-results');
 let players=[],loaded=false,error=false,open=false;
 const close=()=>{panel.hidden=true;input.setAttribute('aria-expanded','false');open=false};
 const show=(html)=>{panel.innerHTML=html;panel.hidden=false;input.setAttribute('aria-expanded','true');open=true};
 const esc=s=>String(s).replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
 const render=()=>{
  const q=normalize(input.value);if(!q){close();return}
  if(!loaded){show('<div class="ca-search-message">'+(error?'Player search unavailable right now.':'Loading player index…')+'</div>');return}
  const matches=players.filter(p=>p.key.includes(q)).sort((a,b)=>Number(b.key.startsWith(q))-Number(a.key.startsWith(q))||a.name.localeCompare(b.name)).slice(0,8);
  if(!matches.length){show('<div class="ca-search-message">No matching players in this '+esc(label)+' archive.</div>');return}
  show(matches.map(p=>'<a href="'+profile(p)+'">'+esc(p.name)+'<small>'+esc(label)+' · View player profile →</small></a>').join(''));
 };
 input.addEventListener('input',render);
 input.addEventListener('focus',render);
 input.addEventListener('keydown',e=>{if(e.key==='Escape')close();if(e.key==='Enter'&&open){const first=panel.querySelector('a');if(first){e.preventDefault();location.href=first.href}}});
 document.addEventListener('pointerdown',e=>{if(!box.contains(e.target))close()});
 fetch(info.url,{cache:'no-store'}).then(r=>{if(!r.ok)throw Error('Player index unavailable');return r.json()}).then(data=>{
  const rows=Array.isArray(data)?data:Array.isArray(data.rows)?data.rows:[];
  const map=new Map();
  rows.forEach(row=>{const id=row[info.id],name=row[info.name];if(id==null||!name)return;const key=String(id);if(!map.has(key))map.set(key,{id:key,name:String(name),key:normalize(name)})});
  players=[...map.values()];loaded=true;render();
 }).catch(()=>{error=true;render()});
}
if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',mount);else mount();
})();