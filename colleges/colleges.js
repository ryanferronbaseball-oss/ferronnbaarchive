
(() => {
'use strict';
const $ = id => document.getElementById(id);
const esc = value => String(value == null ? '' : value).replace(/[&<>"']/g, ch => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[ch]));
const text = value => String(value == null ? '' : value).trim();
const alias = {
 'san diego toreros':'San Diego',
 'butler bulldogs':'Butler',
 'davidson wildcats':'Davidson',
 "delaware fightin' blue hens":'Delaware',
 'nc state wolfpack':'NC State',
 'north carolina state':'NC State',
 'uc davis aggies':'UC Davis',
 'wake forest demon deacons':'Wake Forest',
 'western kentucky hilltoppers':'Western Kentucky',
 'western new mexico mustangs':'Western New Mexico',
 'cal state northrdige':'Cal State Northridge',
 'uc irvine':'UC Irvine'
};
const canonical = value => {
 const s = text(value).replace(/\s+/g,' ');
 return alias[s.toLowerCase()] || s;
};
const slug = value => canonical(value).normalize('NFKD').replace(/[\u0300-\u036f]/g,'').toLowerCase().replace(/[^a-z0-9]+/g,'-').replace(/^-|-$/g,'');
const finite = value => value !== null && value !== undefined && text(value) !== '' && Number.isFinite(Number(value)) ? Number(value) : null;
const dateFmt = value => { const d=new Date(text(value)+'T12:00:00Z');return Number.isFinite(d.getTime()) ? d.toLocaleDateString('en-US',{month:'short',day:'numeric',year:'numeric',timeZone:'UTC'}) : text(value); };
const format = n => Number(n||0).toLocaleString('en-US');
const sportInfo = [
 {key:'basketball',title:'Basketball',icon:'🏀',href:'../college/index.html'},
 {key:'baseball',title:'Baseball',icon:'⚾',href:'../college-baseball/index.html'},
 {key:'football',title:'Football',icon:'🏈',href:'../cfb/index.html'}
];
const blank = () => ({games:[],wins:0,losses:0,ties:0,unscored:0,for:0,against:0});
let schools=[], logos={}, chosen='', search='', filter='all', order='games';
const parseCSV = source => {
 const rows=[], row=[];let field='',quoted=false;
 for(let i=0;i<source.length;i++){
  const c=source[i];
  if(c==='"' && quoted && source[i+1]==='"'){field+='"';i++;}
  else if(c==='"'){quoted=!quoted;}
  else if(c===','&&!quoted){row.push(field);field='';}
  else if((c==='\n'||c==='\r')&&!quoted){if(c==='\r'&&source[i+1]==='\n')i++;row.push(field);field='';if(row.some(v=>v!==''))rows.push(row.splice(0));else row.length=0;}
  else field+=c;
 }
 if(field!==''||row.length){row.push(field);rows.push(row);}
 const header=rows.shift()||[];
 return rows.map(r=>Object.fromEntries(header.map((key,i)=>[key,r[i]||''])));
};
const getJSON = async path => {
 const response=await fetch(path,{cache:'no-store'});
 if(!response.ok)throw new Error(path+' (HTTP '+response.status+')');
 return response.json();
};
const getCSV = async path => {
 const response=await fetch(path,{cache:'no-store'});
 if(!response.ok)throw new Error(path+' (HTTP '+response.status+')');
 return parseCSV(await response.text());
};
const getSchool=(names,map)=>{
 const name=canonical(names),id=slug(name);
 if(!map.has(id))map.set(id,{id,name,logo:null,sports:{basketball:blank(),baseball:blank(),football:blank()},first:null,last:null});
 return map.get(id);
};
function addGame(map, sport, g){
 const away=canonical(g.away),home=canonical(g.home);
 if(!away || !home || !g.date)return;
 const awayScore=finite(g.away_score),homeScore=finite(g.home_score);
 const known=awayScore!==null&&homeScore!==null;
 const venue=text(g.venue);
 const site=text(g.site_type).toLowerCase();
 const isNeutral=site==='neutral'||Boolean(g.neutral_site);
 for(const side of ['away','home']){
  const school=getSchool(side==='away'?away:home,map);
  const own=side==='away'?awayScore:homeScore,other=side==='away'?homeScore:awayScore;
  const opp=side==='away'?home:away;
  const status=known?(own>other?'w':own<other?'l':'t'):'u';
  const sportRecord=school.sports[sport];
  sportRecord.games.push({
   id:g.id,date:g.date,opponent:opp,location:isNeutral?'vs':side==='away'?'at':'vs',
   own,other,status,venue,
   url:({basketball:'../college/game.html?id=',baseball:'../college-baseball/game.html?id=',football:'../cfb/game.html?id='})[sport]+encodeURIComponent(g.id)
  });
  if(known){sportRecord.for+=own;sportRecord.against+=other;
   if(status==='w')sportRecord.wins++;else if(status==='l')sportRecord.losses++;else sportRecord.ties++;
  }else sportRecord.unscored++;
  if(!school.first||g.date<school.first)school.first=g.date;
  if(!school.last||g.date>school.last)school.last=g.date;
  if(sport==='basketball'){
   const id=side==='away'?g.away_team_id:g.home_team_id;
   if(/^\d+$/.test(String(id)))school.logo=String(id);
  }
 }
}
const totalGames=school=>sportInfo.reduce((n,s)=>n+school.sports[s.key].games.length,0);
const activeSports=school=>sportInfo.filter(s=>school.sports[s.key].games.length).length;
const sums=school=>sportInfo.reduce((p,s)=>{const r=school.sports[s.key];p.wins+=r.wins;p.losses+=r.losses;p.ties+=r.ties;p.unscored+=r.unscored;return p;},{wins:0,losses:0,ties:0,unscored:0});
const recordText = row => row.wins+'–'+row.losses+(row.ties?'–'+row.ties:'');
const logoHTML=school=>{
 const name=school.name.split(/\s+/).slice(0,2).map(w=>w[0]).join('').toUpperCase();
 const id=school.logo||logos[school.name];
 const source=/^\d+$/.test(String(id))?'https://a.espncdn.com/i/teamlogos/ncaa/500/'+encodeURIComponent(id)+'.png'
  :typeof id==='string'&&/^https:\/\/(?:www\.ncaa\.com|www\.collegecod\.com|dxbhsrqyrr690\.cloudfront\.net)\//.test(id)?id:null;
 return '<div class="school-logo" aria-hidden="true"><span>'+esc(name)+'</span>'
  +(source?'<img src="'+esc(source)+'" alt="" loading="lazy" onerror="this.remove()">':'')
  +'</div>';
};
const gameRows=(list)=>list.map(g=>'<tr><td><a href="'+esc(g.url)+'">'+esc(dateFmt(g.date))+'</a></td><td>'+esc(g.location+' '+g.opponent)+'</td><td><b class="result '+esc(g.status)+'">'+(g.status==='u'?'—':g.status.toUpperCase())+'</b></td><td>'+(g.own===null?'Score unavailable':esc(g.own+'–'+g.other))+'</td><td>'+esc(g.venue||'—')+'</td></tr>').join('');
const gameTable=games=>'<div class="game-table-wrap"><table><thead><tr><th>Date</th><th>Opponent</th><th>Result</th><th>Score</th><th>Venue</th></tr></thead><tbody>'+gameRows(games)+'</tbody></table></div>';
function profile(school){
 const sum=sums(school),total=totalGames(school);
 const records=sportInfo.map(s=>{
  const row=school.sports[s.key],known=row.games.length-row.unscored;
  return '<article class="sport-panel'+(row.games.length?'':' empty')+'"><h3><span aria-hidden="true">'+s.icon+'</span>'+s.title+'</h3>'
  +(row.games?'<div class="record"><strong>'+recordText(row)+'</strong><small>'+format(row.games.length)+' game'+(row.games.length===1?'':'s')+'</small></div><div class="record-details"><span>Win rate <b>'+(known?(100*row.wins/known).toFixed(1)+'%':'—')+'</b></span><span>Scored <b>'+format(row.for)+'</b></span><span>Allowed <b>'+format(row.against)+'</b></span></div>'
   :'<div class="record"><strong>—</strong><small>No attended games yet</small></div>')
  +'</article>';
 }).join('');
 const sections=sportInfo.map(s=>{
  const rows=school.sports[s.key].games.slice().sort((a,b)=>b.date.localeCompare(a.date)||String(b.id).localeCompare(String(a.id)));
  return '<section class="profile-section"><h3>'+s.icon+' '+s.title+' <small>('+rows.length+')</small></h3>'
  +(!rows.length?'<p class="detail-empty">You have not recorded an attended '+s.title.toLowerCase()+' game involving '+esc(school.name)+'.</p>'
  :'<p class="section-caption">Results are '+esc(school.name)+'’s scores in games you attended. Open a date for the original box score.</p>'
   +gameTable(rows.slice(0,8))
   +(rows.length>8?'<details class="extra"><summary>View '+format(rows.length-8)+' older '+s.title.toLowerCase()+' games</summary>'+gameTable(rows.slice(8))+'</details>':''))
  +'<a class="sport-link" href="'+esc(s.href)+'" style="display:inline-block;margin-top:9px;font-size:11px;font-weight:800">Explore '+s.title+' archive ↗</a></section>';
 }).join('');
 const period=school.first?(school.first.slice(0,4)===school.last.slice(0,4)?school.first.slice(0,4):school.first.slice(0,4)+'–'+school.last.slice(0,4)):'—';
 $('profile').innerHTML='<div class="profile-header">'+logoHTML(school)+'<div><div class="eyebrow">Combined college profile · '+activeSports(school)+' of 3 sports</div><h2>'+esc(school.name)+'</h2><p class="profile-intro">Attended history: '+esc(period)+' · Basketball, baseball and football</p></div><div class="profile-total"><strong>'+format(total)+'</strong><small>Attended games · '+recordText(sum)+(sum.unscored?' · '+sum.unscored+' unscored':'')+'</small></div></div><div class="sport-grid">'+records+'</div>'+sections;
 $('profile').setAttribute('aria-label',school.name+' combined college profile');
}
function drawDirectory(){
 const q=search.trim().toLowerCase();
 let shown=schools.filter(s=>s.name.toLowerCase().includes(q));
 if(filter==='multi')shown=shown.filter(s=>activeSports(s)>=2);
 if(filter==='three')shown=shown.filter(s=>activeSports(s)===3);
 shown.sort(order==='alpha'?(a,b)=>a.name.localeCompare(b.name):order==='sports'?(a,b)=>activeSports(b)-activeSports(a)||totalGames(b)-totalGames(a)||a.name.localeCompare(b.name):(a,b)=>totalGames(b)-totalGames(a)||a.name.localeCompare(b.name));
 $('showing').textContent='Showing '+format(shown.length)+' of '+format(schools.length)+' colleges';
 $('directory').innerHTML=shown.length?shown.map(s=>'<button type="button" class="school-card'+(s.id===chosen?' selected':'')+'" data-school="'+esc(s.id)+'" aria-pressed="'+(s.id===chosen?'true':'false')+'">'+logoHTML(s)+'<span style="min-width:0"><span class="name">'+esc(s.name)+'</span><small>'+activeSports(s)+' sport'+(activeSports(s)===1?'':'s')+' · '+recordText(sums(s))+'</small></span><span class="count"><strong>'+format(totalGames(s))+'</strong><small>games</small></span></button>').join(''):'<div class="no-results">No colleges match those filters.</div>';
}
function select(id,scroll,updateUrl){
 const school=schools.find(s=>s.id===id);
 if(!school)return;
 chosen=id;
 profile(school);
 drawDirectory();
 if(updateUrl){
  const next=new URL(location.href);
  next.searchParams.set('school',id);
  history.pushState({school:id},'',next);
 }
 if(scroll)$('profile').scrollIntoView({behavior:matchMedia('(prefers-reduced-motion: reduce)').matches?'auto':'smooth',block:'start'});
}
async function boot(){
 try{
 const [basketball,football,baseball,corrections,logoData,additionalLogos]=await Promise.all([
  getCSV('../college/data/games.csv'),
  getJSON('../cfb/data/games.json'),
  getJSON('../college-baseball/data/games.json'),
  getJSON('../college-baseball/data/attendance_game_corrections.json'),
  getJSON('../college-baseball/data/team_logo_ids.json'),
  getJSON('./logo_overrides.json')
 ]);
 logos={...logoData,...additionalLogos};
 const replaced=new Map((corrections.games||[]).filter(c=>c.replaces_game_id&&c.game).map(c=>[c.replaces_game_id,c.game]));
 const map=new Map();
 for(const g of basketball)addGame(map,'basketball',{...g,venue:g.arena});
 for(const g of football)addGame(map,'football',{...g,venue:g.stadium});
 for(const raw of baseball){
  const patch=replaced.get(raw.id);
  const g=patch?{...raw,...patch}:raw;
  addGame(map,'baseball',{...g,venue:g.ballpark});
 }
 schools=[...map.values()].sort((a,b)=>a.name.localeCompare(b.name));
 const total=schools.reduce((n,s)=>n+totalGames(s),0);
 $('schoolCount').textContent=format(schools.length);
 $('appearanceCount').textContent=format(total);
 $('multiCount').textContent=format(schools.filter(s=>activeSports(s)>=2).length);
 $('allThreeCount').textContent=format(schools.filter(s=>activeSports(s)===3).length);
 $('search').disabled=false;$('filter').disabled=false;$('order').disabled=false;
 $('search').addEventListener('input',event=>{search=event.target.value;drawDirectory();});
 $('filter').addEventListener('change',event=>{filter=event.target.value;drawDirectory();});
 $('order').addEventListener('change',event=>{order=event.target.value;drawDirectory();});
 $('directory').addEventListener('click',event=>{
  const btn=event.target.closest('button[data-school]');
  if(btn)select(btn.dataset.school,true,true);
 });
 addEventListener('popstate',()=>{
  const id=new URLSearchParams(location.search).get('school');
  select(id||'wake-forest',false,false);
 });
 const wanted=new URLSearchParams(location.search).get('school');
 select(wanted||'wake-forest',false,false);
 }catch(error){
  $('error').hidden=false;
  $('error').textContent='Unable to load the combined college game records: '+error.message+'. Try refreshing the page.';
  $('profile').innerHTML='<p class="detail-empty">College profiles are temporarily unavailable.</p>';
  $('showing').textContent='Data unavailable';
  console.error('Cross-sport college profiles failed to load',error);
 }
}
boot();
})();
