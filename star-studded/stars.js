/* Courtside Archive cross-sport Star-Studded Games.
   Career honors are retrospective; only witnessed playing appearances are scored. */
(()=>{'use strict';
const $=id=>document.getElementById(id);
const esc=v=>String(v??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;','\'':'&#39;'}[c]));
const fmt=v=>new Date(String(v)+'T12:00:00Z').toLocaleDateString('en-US',{month:'short',day:'numeric',year:'numeric',timeZone:'UTC'});
const isPlayed=v=>v!==null&&v!==undefined&&v!==''&&v!=='--'&&v!=='DNP'&&Number.parseFloat(v)>0;
const awardArray=v=>Array.isArray(v)&&v.length>0;
const getJSON=async path=>{const r=await fetch(path,{cache:'no-store'});if(!r.ok)throw Error(path+' HTTP '+r.status);return r.json()};
const csv=async path=>{
 const r=await fetch(path,{cache:'no-store'});if(!r.ok)throw Error(path+' HTTP '+r.status);
 const lines=(await r.text()).replace(/\r/g,'').split('\n').filter(Boolean);
 const split=line=>{const fields=[];let v='',quoted=false;for(let i=0;i<line.length;i++){const ch=line[i];if(ch==='"'){if(quoted&&line[i+1]==='"'){v+='"';i++}else quoted=!quoted;}else if(ch===','&&!quoted){fields.push(v);v=''}else v+=ch;}fields.push(v);return fields;};
 const keys=split(lines.shift()||'');return lines.map(line=>Object.fromEntries(split(line).map((v,i)=>[keys[i],v])));
};
const slug=v=>String(v||'').normalize('NFKD').replace(/[\u0300-\u036f]/g,'').toLowerCase().replace(/[^a-z0-9]+/g,'-').replace(/^-|-$/g,'');
const nbaHof=new Set(['662','110','136','885','261','592','336','215','1015','272','1987','614','996','1975','2384','1722']);
const nflHof=new Set(['1682','1755','10455','668']);
const byGame=(rows,getId)=>{const map=new Map();for(const row of rows){const id=String(getId(row)||'');if(!id)continue;if(!map.has(id))map.set(id,[]);map.get(id).push(row);}return map;};
function recognized(name,id,link,side,honors){
 const tags=honors.filter(x=>x&&x.title);
 if(!tags.length)return null;
 const ordered=tags.sort((a,b)=>b.weight-a.weight);
 return {name,id:String(id),link,side,tag:ordered[0].title,prestige:Math.min(12,ordered.reduce((s,x)=>s+x.weight,0)),elite:ordered.some(x=>x.elite)};
}
function makeGame(sport,g,players,url){
 const found=new Map();for(const p of players){if(p&&!found.has(p.id))found.set(p.id,p);}
 const stars=[...found.values()].sort((a,b)=>b.prestige-a.prestige||a.name.localeCompare(b.name));
 if(stars.length<2)return null;
 const legends=stars.filter(p=>p.elite).length;
 return {sport,id:String(g.id),date:g.date,away:g.away,home:g.home,awayScore:g.away_score,homeScore:g.home_score,venue:g.venue||'',url,stars,count:stars.length,legends,index:stars.length*5+stars.reduce((s,p)=>s+p.prestige,0)};
}
async function nba(){
 const [games,logs,career,legacy]=await Promise.all([
  csv('../data/games.csv'),getJSON('../data/player_boxscores_espn.json'),getJSON('../data/nba_career_awards.json'),getJSON('../data/nba_legacy_honors.json')
 ]);
 const groups=byGame(logs,r=>r.game_id);
 return games.map(g=>{
  const rows=(groups.get(String(g.nba_game_id))||[]).filter(r=>isPlayed(r.minutes));
  const players=rows.map(r=>{
   const id=String(r.player_id||'').replace(/^espn:/,''),a=career.players?.[id]||{},b=legacy.players?.[id]||{};
   const awards=[];
   if(nbaHof.has(id))awards.push({title:'Hall of Fame',weight:5,elite:true});
   if(a.mvp)awards.push({title:'NBA MVP',weight:5,elite:true});
   if(b.nba75)awards.push({title:'NBA 75',weight:3});
   if(a.all_nba)awards.push({title:'All-NBA',weight:2});
   if(Number(a.all_star)>0)awards.push({title:Number(a.all_star)+'× NBA All-Star',weight:2});
   if(awardArray(b.finals_mvp))awards.push({title:'Finals MVP',weight:3,elite:true});
   if(awardArray(b.dpoy))awards.push({title:'Defensive POY',weight:2});
   const side=String(r.team_id||'');
   return recognized(r.player,id,'../nba/player.html?id='+encodeURIComponent(r.player_id),side,awards);
  });
  return makeGame('NBA',{id:g.id,date:g.date,away:g.away,home:g.home,away_score:g.away_score,home_score:g.home_score,venue:g.arena},players,'../nba/game.html?id='+encodeURIComponent(g.id));
 }).filter(Boolean);
}
async function nfl(){
 const [games,rows,career,extra]=await Promise.all([
  getJSON('../nfl/data/games.json'),getJSON('../nfl/data/player_stats.json'),getJSON('../nfl/data/career_awards.json'),getJSON('../nfl/data/extra_career_honors.json')
 ]);
 const groups=byGame(rows,r=>r.game_id);
 return games.map(g=>{
  const players=(groups.get(g.id)||[]).map(r=>{
   const id=String(r.athlete_id||''),a=career.players?.[id]||{},b=extra.players?.[id]||{},awards=[];
   if(nflHof.has(id))awards.push({title:'Hall of Fame',weight:5,elite:true});
   if(awardArray(a.ap_mvp))awards.push({title:'NFL MVP',weight:5,elite:true});
   if(awardArray(b.super_bowl_mvp))awards.push({title:'Super Bowl MVP',weight:4,elite:true});
   if(awardArray(b.nfl_100))awards.push({title:'NFL 100',weight:3});
   if(awardArray(a.ap_first_team))awards.push({title:'First-Team All-Pro',weight:3});
   if(Number(a.pro_bowl_count)>0)awards.push({title:Number(a.pro_bowl_count)+'× Pro Bowl',weight:2});
   if(awardArray(b.all_decade))awards.push({title:'All-Decade',weight:2});
   return recognized(r.player,id,'../nfl/player.html?id='+encodeURIComponent(id),r.team,awards);
  });
  return makeGame('NFL',{...g,venue:g.stadium},players,'../nfl/game.html?id='+encodeURIComponent(g.id));
 }).filter(Boolean);
}
async function mlb(){
 const [games,rows,career]=await Promise.all([
  getJSON('../mlb/data/games.json'),getJSON('../mlb/data/player_stats.json'),getJSON('../mlb/data/career_awards.json')
 ]);
 const groups=byGame(rows,r=>r.game_pk);
 return games.filter(g=>g.game_pk!=null).map(g=>{
  const players=(groups.get(String(g.game_pk))||[]).map(r=>{
   const id=String(r.player_id||''),a=career.players?.[id]||{},awards=[];
   if(a.hall_of_fame)awards.push({title:'Baseball Hall of Fame',weight:5,elite:true});
   if(awardArray(a.mvp))awards.push({title:'MLB MVP',weight:5,elite:true});
   if(awardArray(a.cy_young))awards.push({title:'Cy Young',weight:5,elite:true});
   if(awardArray(a.all_star))awards.push({title:a.all_star.length+'× MLB All-Star',weight:2});
   if(awardArray(a.silver_slugger))awards.push({title:'Silver Slugger',weight:1});
   if(awardArray(a.gold_glove))awards.push({title:'Gold Glove',weight:1});
   return recognized(r.name,id,'../mlb/player.html?id='+encodeURIComponent(id),r.team,awards);
  });
  return makeGame('MLB',{id:g.attendance_id,date:g.date,away:g.away,home:g.home,away_score:g.away_score,home_score:g.home_score,venue:g.ballpark},players,'../mlb/game.html?id='+encodeURIComponent(g.attendance_id));
 }).filter(Boolean);
}
async function college(){
 const [games,rows,tags,cross]=await Promise.all([
  csv('../college/data/games.csv'),getJSON('../college/data/player_boxscores_espn.json'),getJSON('../college/data/career_tags_high_priority.json'),getJSON('../college/data/nba_crosswalk.json')
 ]);
 const groups=byGame(rows,r=>r.game_id);
 const pros=new Map(cross.map(p=>[String(p.player_id),p]));
 return games.map(g=>{
  const players=(groups.get(String(g.id))||[]).filter(r=>isPlayed(r.minutes)).map(r=>{
   const id=String(r.player_id||''),a=tags.players?.[id]||{},pro=pros.get(id),awards=[];
   if(awardArray(a.final_four_mop))awards.push({title:'Final Four MOP',weight:5,elite:true});
   if(awardArray(a.conference_poy))awards.push({title:'Conference POY',weight:3});
   if(awardArray(a.conference_dpoy))awards.push({title:'Conference DPOY',weight:2});
   if(awardArray(a.all_conference))awards.push({title:'All-Conference',weight:1});
   if(pro?.draft_pick!=null){const pick=Number(pro.draft_pick);awards.push({title:'NBA Draft pick '+pick,weight:pick<=30?4:2,elite:pick<=14});}
   else if(pro?.nba_debut)awards.push({title:'Reached NBA',weight:2});
   return recognized(r.player,id,'../college/player.html?id='+encodeURIComponent(id),r.team,awards);
  });
  return makeGame('College Basketball',{id:g.id,date:g.date,away:g.away,home:g.home,away_score:g.away_score,home_score:g.home_score,venue:g.arena},players,'../college/game.html?id='+encodeURIComponent(g.id));
 }).filter(Boolean);
}
async function soccer(){
 const [matches,career,individual]=await Promise.all([
  getJSON('../soccer/data/matches.json'),getJSON('../soccer/data/career_honors.json'),getJSON('../soccer/data/individual_honors.json')
 ]);
 const byName=new Map();
 for(const [id,obj] of Object.entries(career.players||{}))byName.set(slug(obj.name||id),id);
 for(const [id,obj] of Object.entries(individual.players||{}))if(!byName.has(slug(obj.name||id)))byName.set(slug(obj.name||id),id);
 return matches.map(g=>{
  const names=[
   ...(g.home_starters||[]).map(name=>[name,g.home]),
   ...(g.away_starters||[]).map(name=>[name,g.away]),
   ...(g.home_subs_used||[]).map(name=>[name,g.home]),
   ...(g.away_subs_used||[]).map(name=>[name,g.away])
  ];
  const players=names.map(([name,side])=>{
   const id=byName.get(slug(name))||slug(name),a=career.players?.[id]||{},b=individual.players?.[id]||{},awards=[];
   const global=b.global||[];
   if(global.some(x=>/Ballon d'Or|Best FIFA Men's Player|FIFPRO.*World XI/i.test(x.award||'')))awards.push({title:'Global elite XI / award',weight:5,elite:true});
   if(awardArray(b.uefa))awards.push({title:'UEFA honors',weight:3});
   if(awardArray(b.domestic)||awardArray(b.international))awards.push({title:'Individual honors',weight:2});
   if(awardArray(a.world_cup))awards.push({title:'World Cup player',weight:2});
   if(awardArray(a.league_titles))awards.push({title:'League champion',weight:1});
   if(awardArray(a.mls_awards))awards.push({title:'MLS award',weight:2});
   return recognized(name,id,'../soccer/player.html?id='+encodeURIComponent(id),side,awards);
  });
  return makeGame('Soccer',{...g,venue:g.venue},players,'../soccer/game.html?id='+encodeURIComponent(g.id));
 }).filter(Boolean);
}
async function collegeFootball(){
 const [games,rows,cross]=await Promise.all([
  getJSON('../cfb/data/games.json'),getJSON('../cfb/data/player_stats.json'),getJSON('../cfb/data/nfl_crosswalk.json')
 ]);
 const groups=byGame(rows,r=>r.game_id),known=new Map(cross.map(p=>[String(p.athlete_id),p]));
 return games.map(g=>{
  const players=(groups.get(g.id)||[]).map(r=>{
   const id=String(r.athlete_id||''),a=known.get(id),awards=[];
   if(a?.category==='nfl')awards.push({title:'Reached the NFL',weight:2});
   const pick=a?.draft_pick==null?null:Number(a.draft_pick);
   if(pick!==null&&Number.isFinite(pick))awards.push({title:'NFL Draft pick '+pick,weight:pick<=32?5:pick<=100?3:2,elite:pick<=32});
   return recognized(r.player,id,'../cfb/player.html?id='+encodeURIComponent(id),r.team,awards);
  });
  return makeGame('College Football',{...g,venue:g.stadium},players,'../cfb/game.html?id='+encodeURIComponent(g.id));
 }).filter(Boolean);
}
async function collegeBaseball(){
 const [games,rows,draft,national,american]=await Promise.all([
  getJSON('../college-baseball/data/games.json'),getJSON('../college-baseball/data/player_stats.json'),
  getJSON('../college-baseball/data/draft_profile_tags.json'),
  getJSON('../college-baseball/data/national_award_profile_tags.json'),
  getJSON('../college-baseball/data/baseball_america_all_american_tags.json')
 ]);
 const groups=byGame(rows,r=>r.game_id);
 const drafts=new Map((draft.picks||[]).map(p=>[String(p.college_player_id),p]));
 const nationals=new Map(),allAmericans=new Map();
 for(const a of national.awards||[]){const id=String(a.college_player_id||'');if(!id)continue;if(!nationals.has(id))nationals.set(id,[]);nationals.get(id).push(a);}
 for(const a of american.honors||[]){const id=String(a.college_player_id||'');if(!id)continue;if(!allAmericans.has(id))allAmericans.set(id,[]);allAmericans.get(id).push(a);}
 return games.map(g=>{
  const players=(groups.get(g.id)||[]).map(r=>{
   const id=String(r.player_id||''),d=drafts.get(id),n=nationals.get(id)||[],aa=allAmericans.get(id)||[],awards=[];
   if(n.length)awards.push({title:/Golden Spikes|Dick Howser|Player of the Year/i.test(n.map(x=>x.award).join(', '))?'National POY / top award':'National award winner',weight:5,elite:true});
   if(aa.some(x=>/First/i.test(x.team||'')))awards.push({title:'First-Team All-American',weight:4});
   else if(aa.length)awards.push({title:'All-American',weight:3});
   const pick=d?.draft_pick==null?null:Number(d.draft_pick);
   if(pick!==null&&Number.isFinite(pick)&&pick<=300)awards.push({title:'MLB Draft pick '+pick,weight:pick<=30?5:pick<=100?3:1,elite:pick<=30});
   return recognized(r.name,id,'../college-baseball/player.html?id='+encodeURIComponent(id),r.team,awards);
  });
  return makeGame('College Baseball',{...g,venue:g.ballpark},players,'../college-baseball/game.html?id='+encodeURIComponent(g.id));
 }).filter(Boolean);
}
async function milb(){
 const [games,rows,seed,career]=await Promise.all([
  getJSON('../milb/data/games.json'),getJSON('../milb/data/player_stats.json'),getJSON('../milb/data/mlb_alumni_seed.json'),getJSON('../mlb/data/career_awards.json')
 ]);
 const groups=byGame(rows,r=>r.game_id),alumni=new Map((seed.players||[]).map(p=>[String(p.milb_player_id),p]));
 return games.map(g=>{
  const players=(groups.get(g.id)||[]).map(r=>{
   const id=String(r.player_id||''),a=alumni.get(id),c=career.players?.[id]||{},awards=[];
   if(c.hall_of_fame)awards.push({title:'Baseball Hall of Fame',weight:5,elite:true});
   if(awardArray(c.mvp)||awardArray(c.cy_young))awards.push({title:'MLB MVP / Cy Young',weight:5,elite:true});
   if(awardArray(c.all_star))awards.push({title:'MLB All-Star',weight:3});
   if(a?.mlb_debut)awards.push({title:'Reached MLB',weight:2});
   const pick=a?.draft_pick==null?null:Number(a.draft_pick);
   if(pick!==null&&Number.isFinite(pick)&&pick<=100)awards.push({title:'MLB Draft pick '+pick,weight:pick<=30?4:2,elite:pick<=30});
   return recognized(r.name,id,'../milb/player.html?id='+encodeURIComponent(id),r.team,awards);
  });
  return makeGame('MiLB',{id:g.id,date:g.date,away:g.away_team,home:g.home_team,away_score:g.away_score,home_score:g.home_score,venue:g.venue},players,'../milb/game.html?id='+encodeURIComponent(g.id));
 }).filter(Boolean);
}
async function nhl(){
 const games=await getJSON('../nhl/data/games.json');
 return games.map(g=>{
  const players=(g.players||[]).filter(p=>p.skater||p.goalie).map(p=>{
   const honors=p.awards||[],awards=[];
   if(honors.some(a=>a.title==='Hockey Hall of Fame'))awards.push({title:'Hockey Hall of Fame',weight:5,elite:true});
   if(honors.some(a=>(a.category==='award'||/Trophy|Award/i.test(a.title))&&/Hart Memorial Trophy|Art Ross Trophy|Vezina Trophy|Conn Smythe Trophy/i.test(a.title)))awards.push({title:'Major NHL trophy',weight:5,elite:true});
   else if(honors.some(a=>a.category==='award'||/Trophy|Award/i.test(a.title)))awards.push({title:'NHL award winner',weight:3});
   if(honors.some(a=>a.category==='allteam'))awards.push({title:'NHL All-Star Team',weight:2});
   if(honors.some(a=>a.category==='allstar'||/All-Star Game/i.test(a.title)))awards.push({title:'NHL All-Star',weight:2});
   if(honors.some(a=>a.category==='stanley'||/Stanley Cup/i.test(a.title)))awards.push({title:'Stanley Cup champion',weight:1});
   return recognized(p.name,p.id,'../nhl/player.html?id='+encodeURIComponent(p.id),p.team,awards);
  });
  return makeGame('NHL',g,players,'../nhl/game.html?id='+encodeURIComponent(g.id));
 }).filter(Boolean);
}
let collection=[],loadErrors=[],expanded=24;
const order=['NBA','College Basketball','NFL','College Football','MLB','MiLB','College Baseball','NHL','Soccer'];
const rankList=items=>items.sort((a,b)=>b.index-a.index||b.count-a.count||a.date.localeCompare(b.date));
function draw(){
 const sport=$('sportFilter').value,sort=$('sortFilter').value,q=$('searchFilter').value.trim().toLocaleLowerCase();
 let list=collection.filter(g=>(sport==='all'||g.sport===sport)
  &&(!q||[g.sport,g.away,g.home,g.date,g.venue,...g.stars.map(x=>x.name)].join(' ').toLocaleLowerCase().includes(q)));
 list.sort((a,b)=>sort==='stars'?b.count-a.count||b.index-a.index
  :sort==='legends'?b.legends-a.legends||b.index-a.index
  :sort==='oldest'?a.date.localeCompare(b.date)||b.index-a.index
  :sort==='newest'?b.date.localeCompare(a.date)||b.index-a.index
  :b.index-a.index||b.count-a.count||a.date.localeCompare(b.date));
 const count=list.length;
 $('resultsNote').textContent='Showing '+Math.min(expanded,count)+' of '+count+' qualifying matchups · '+collection.length+' verified games indexed'+(loadErrors.length?' · Coverage still incomplete for '+loadErrors.join(', '):'');
 $('gameList').innerHTML=list.slice(0,expanded).map((g,i)=>
  '<article class="star-card"><div class="card-top"><span class="rank">#'+String(i+1).padStart(2,'0')+'</span><span class="sport">'+esc(g.sport)+'</span></div>'
  +'<h3>'+esc(g.away)+' <span aria-label="versus">vs.</span> '+esc(g.home)+'</h3>'
  +'<p class="meta">'+esc(fmt(g.date))+(g.venue?' · '+esc(g.venue):'')+'</p>'
  +'<div class="scoreline"><div><strong>'+g.count+'</strong><small>Recognized players</small></div><div><strong>'+g.legends+'</strong><small>HOF / top honorees</small></div><div><strong>'+g.index+'</strong><small>Star Power Index</small></div></div>'
  +'<ul class="star-list">'+g.stars.slice(0,7).map(p=>'<li><a href="'+esc(p.link)+'">'+esc(p.name)+'</a><small>'+esc(p.tag)+'</small></li>').join('')+'</ul>'
  +(g.stars.length>7?'<details class="star-extra"><summary>Show '+(g.stars.length-7)+' more recognized '+(g.stars.length-7===1?'player':'players')+'</summary><ul class="star-list">'+g.stars.slice(7).map(p=>'<li><a href="'+esc(p.link)+'">'+esc(p.name)+'</a><small>'+esc(p.tag)+'</small></li>').join('')+'</ul></details>':'')
  +'<div class="card-footer"><span>'+esc(g.date)+' · '+esc(g.sport)+'</span><a href="'+esc(g.url)+'">Open game ↗</a></div></article>').join('')
  +(count>expanded?'<button class="load-more" id="moreStars" type="button">Show more games ('+(count-expanded)+' remaining)</button>':'')
  ||'<div class="empty">No qualifying games match these filters. Try a different sport or search term.</div>';
 const more=$('moreStars');if(more)more.addEventListener('click',()=>{expanded+=24;draw()});
}
async function init(){
 const funcs=[nba,college,nfl,collegeFootball,mlb,milb,collegeBaseball,nhl,soccer];
 const results=await Promise.allSettled(funcs.map(f=>f()));
 const successful=[];
 results.forEach((r,i)=>{if(r.status==='fulfilled'){successful.push(order[i]);collection.push(...r.value)}else{loadErrors.push(order[i]);console.warn('Star-Studded Games source unavailable',order[i],r.reason)}});
 collection=rankList(collection);
 const options=[...new Set(collection.map(g=>g.sport))].sort((a,b)=>order.indexOf(a)-order.indexOf(b));
 $('sportFilter').innerHTML='<option value="all">All covered sports</option>'+options.map(x=>'<option value="'+esc(x)+'">'+esc(x)+'</option>').join('');
 $('starGames').textContent=collection.length.toLocaleString('en-US');
 $('starNames').textContent=new Set(collection.flatMap(g=>g.stars.map(p=>g.sport+':'+p.id))).size.toLocaleString('en-US');
 $('starSports').textContent=options.length;
 $('starTop').textContent=collection.length?Math.max(...collection.map(g=>g.count)):'—';
 if(!collection.length){$('resultsNote').textContent='No verified games could be loaded. '+(loadErrors.length?'Source files unavailable: '+loadErrors.join(', '):'Check the archive’s award and box-score coverage.');}
 ['sportFilter','sortFilter','searchFilter'].forEach(id=>$(id).addEventListener(id==='searchFilter'?'input':'change',()=>{expanded=24;draw()}));
 draw();
}
init().catch(err=>{$('gameList').innerHTML='<div class="empty">Unable to assemble the archive collection right now. Please try again later.</div>';console.error(err)});
})();