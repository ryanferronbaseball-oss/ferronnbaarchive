/* Courtside Archive cross-sport Star-Studded Games.
   Career honors are retrospective; only witnessed playing appearances are scored. */
(()=>{'use strict';
const $=id=>document.getElementById(id);
const Prime=window.CourtsidePrime;
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
function recognized(name,id,link,side,honors,evidence=[]){
 const tags=honors.filter(x=>x&&x.title);
 if(!tags.length)return null;
 const ordered=tags.sort((a,b)=>b.weight-a.weight);
 return {name,id:String(id),link,side,tag:ordered[0].title,prestige:Math.min(12,ordered.reduce((s,x)=>s+x.weight,0)),elite:ordered.some(x=>x.elite),evidence:evidence.filter(Boolean)};
}
function makeGame(sport,g,players,url){
 const found=new Map();for(const p of players){if(p&&!found.has(p.id))found.set(p.id,p);}
 const stars=[...found.values()].map(p=>({...p,prime:Prime.assess(sport,g.date,p.evidence)})).sort((a,b)=>b.prestige-a.prestige||a.name.localeCompare(b.name));
 if(stars.length<2)return null;
 const legends=stars.filter(p=>p.elite).length;
 const primePlayers=stars.filter(p=>p.prime.tier==='prime').length;
 const primeMeasured=stars.filter(p=>p.prime.assessed).length;
 const primeIndex=Math.round(stars.reduce((sum,p)=>sum+(p.prime.score||0),0))/10;
 return {sport,id:String(g.id),date:g.date,away:g.away,home:g.home,awayScore:g.away_score,homeScore:g.home_score,venue:g.venue||'',url,stars,count:stars.length,legends,index:stars.length*5+stars.reduce((s,p)=>s+p.prestige,0),primePlayers,primeMeasured,primeIndex};
}
async function nba(){
 const [games,logs,career,legacy,years]=await Promise.all([
  csv('../data/games.csv'),getJSON('../data/player_boxscores_espn.json'),getJSON('../data/nba_career_awards.json'),getJSON('../data/nba_legacy_honors.json'),getJSON('../data/nba_award_years.json')
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
   const n=years.players?.[id]||{},evidence=[
    ...Prime.list(n.mvp,8,'NBA MVP',x=>x.season),
    ...(n.all_nba||[]).map(x=>Prime.signal(x.season,x.selection==='First Team'?5:x.selection==='Second Team'?3:2,'All-NBA '+(x.selection||''))),
    ...Prime.list(n.all_star,2,'NBA All-Star'),
    ...Prime.list(b.finals_mvp,6,'Finals MVP',x=>x.season),
    ...Prime.list(b.dpoy,5,'Defensive Player of the Year',x=>x.season),
    ...Prime.list(b.all_defensive,1,'All-Defensive Team',x=>x.season)
   ];
   const side=String(r.team_id||'');
   return recognized(r.player,id,'../nba/player.html?id='+encodeURIComponent(r.player_id),side,awards,evidence);
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
   const evidence=[
    ...Prime.list(a.ap_mvp,8,'NFL MVP'),
    ...Prime.list(a.ap_first_team,5,'First-Team All-Pro'),
    ...Prime.list(a.ap_second_team,3,'Second-Team All-Pro'),
    ...Prime.list(b.pro_bowl_years,2,'Pro Bowl'),
    ...Prime.list(b.super_bowl_mvp,6,'Super Bowl MVP',x=>x.year),
    ...Prime.list(b.ap_opoy,5,'Offensive Player of the Year',x=>x.year),
    ...Prime.list(b.ap_dpoy,5,'Defensive Player of the Year',x=>x.year),
    ...Prime.list(b.ap_oroy,2,'Offensive Rookie of the Year',x=>x.year),
    ...Prime.list(b.ap_droy,2,'Defensive Rookie of the Year',x=>x.year)
   ];
   return recognized(r.player,id,'../nfl/player.html?id='+encodeURIComponent(id),r.team,awards,evidence);
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
   const evidence=[
    ...Prime.list(a.mvp,8,'MLB MVP',x=>x.year),
    ...Prime.list(a.cy_young,8,'Cy Young',x=>x.year),
    ...Prime.list(a.all_star,2,'MLB All-Star',x=>x.year),
    ...Prime.list(a.silver_slugger,2,'Silver Slugger',x=>x.year),
    ...Prime.list(a.gold_glove,1,'Gold Glove',x=>x.year)
   ];
   return recognized(r.name,id,'../mlb/player.html?id='+encodeURIComponent(id),r.team,awards,evidence);
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
   const evidence=[
    ...Prime.list(a.final_four_mop,8,'Final Four MOP',x=>x.year||x.season),
    ...Prime.list(a.conference_poy,6,'Conference Player of the Year',x=>x.season||x.year),
    ...Prime.list(a.conference_dpoy,5,'Conference Defensive POY',x=>x.season||x.year),
    ...(a.all_conference||[]).map(x=>Prime.signal(x.season||x.year,x.team===1?4:2,'All-Conference '+(x.team===1?'First Team':'Team'))),
    ...Prime.list(a.ncaa_champion,1,'NCAA champion',x=>x.year)
   ];
   return recognized(r.player,id,'../college/player.html?id='+encodeURIComponent(id),r.team,awards,evidence);
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
   const evidence=[
    ...(b.global||[]).map(x=>Prime.signal(x.year||x.season,/Ballon d.Or|Best FIFA Men.s Player/i.test(x.award||'')?8:6,x.award||'Global individual honor')),
    ...(b.uefa||[]).map(x=>Prime.signal(x.year||x.season,5,x.award||'UEFA award')),
    ...(b.domestic||[]).map(x=>Prime.signal(x.year||x.season,3,x.award||'Domestic award')),
    ...(b.international||[]).map(x=>Prime.signal(x.year||x.season,4,x.award||'International award')),
    ...(a.mls_awards||[]).map(x=>Prime.signal(x.year||x.season,4,x.award||'MLS award'))
   ];
   return recognized(name,id,'../soccer/player.html?id='+encodeURIComponent(id),side,awards,evidence);
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
   // The current CFB crosswalk establishes later NFL progression, not dated college prime seasons.
   return recognized(r.player,id,'../cfb/player.html?id='+encodeURIComponent(id),r.team,awards,[]);
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
   const evidence=[
    ...n.map(x=>Prime.signal(x.year,7,x.award||'National award')),
    ...aa.map(x=>Prime.signal(x.year,/First/i.test(x.team||'')?5:3,'Baseball America '+(x.team||'All-American')))
   ];
   return recognized(r.name,id,'../college-baseball/player.html?id='+encodeURIComponent(id),r.team,awards,evidence);
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
   const evidence=[
    ...Prime.list(c.mvp,8,'MLB MVP',x=>x.year),
    ...Prime.list(c.cy_young,8,'Cy Young',x=>x.year),
    ...Prime.list(c.all_star,2,'MLB All-Star',x=>x.year)
   ];
   return recognized(r.name,id,'../milb/player.html?id='+encodeURIComponent(id),r.team,awards,evidence);
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
   const evidence=honors.flatMap(h=>{
    if(h.category==='award')return String(h.years||'').match(/\b(?:19|20)\d{2}\b/g)?.map(y=>Prime.signal(y,/Hart|Art Ross|Vezina|Conn Smythe|Norris|Selke/i.test(h.title)?6:4,h.title))||[];
    if(h.category==='allstar')return String(h.years||'').match(/\b(?:19|20)\d{2}\b/g)?.map(y=>Prime.signal(y,2,'NHL All-Star Game'))||[];
    if(h.category==='allteam')return String(h.years||'').match(/\b(?:19|20)\d{2}\b/g)?.map(y=>Prime.signal(y,/First All-Star/i.test(h.title)?5:/Second All-Star/i.test(h.title)?3:1,h.title))||[];
    return [];
   });
   return recognized(p.name,p.id,'../nhl/player.html?id='+encodeURIComponent(p.id),p.team,awards,evidence);
  });
  return makeGame('NHL',g,players,'../nhl/game.html?id='+encodeURIComponent(g.id));
 }).filter(Boolean);
}
let collection=[],loadErrors=[],expanded=24;
const order=['NBA','College Basketball','NFL','College Football','MLB','MiLB','College Baseball','NHL','Soccer'];
const rankList=items=>items.sort((a,b)=>b.index-a.index||b.count-a.count||a.date.localeCompare(b.date));
const primeTierLabel=p=>{
 const label=p.prime?.label||'Not rated';
 return '<span class="prime-status '+esc(p.prime?.tier||'unknown')+'" title="'+esc(p.prime?.detail||'No dated recognition on record')+'">'+esc(label)+'</span>';
};
function draw(){
 const sport=$('sportFilter').value,sort=$('sortFilter').value,q=$('searchFilter').value.trim().toLocaleLowerCase();
 const lens=$('lensFilter').value||'prime',filter=$('primeFilter').value||'all';
 $('primeFilterWrap').hidden=lens!=='prime';
 let list=collection.filter(g=>(sport==='all'||g.sport===sport)
  &&(!q||[g.sport,g.away,g.home,g.date,g.venue,...g.stars.map(x=>x.name)].join(' ').toLocaleLowerCase().includes(q))
  &&(lens!=='prime'||filter==='all'
     ||(filter==='one'&&g.primePlayers>=1)
     ||(filter==='two'&&g.primePlayers>=2)
     ||(filter==='three'&&g.primePlayers>=3)
     ||(filter==='rated'&&g.primeMeasured>=2)));
 list.sort((a,b)=>sort==='stars'?b.count-a.count||b.index-a.index
  :sort==='legends'?b.legends-a.legends||b.index-a.index
  :sort==='primeStars'?b.primePlayers-a.primePlayers||b.primeIndex-a.primeIndex
  :sort==='oldest'?a.date.localeCompare(b.date)||b.index-a.index
  :sort==='newest'?b.date.localeCompare(a.date)||b.index-a.index
  :lens==='prime'?b.primeIndex-a.primeIndex||b.primePlayers-a.primePlayers||b.index-a.index
  :b.index-a.index||b.count-a.count||a.date.localeCompare(b.date));
 const count=list.length;
 $('resultsNote').textContent='Showing '+Math.min(expanded,count)+' of '+count+' qualifying matchups · '+collection.length+' games indexed · '
  +(lens==='prime'?'Prime-era evidence is available for '+collection.filter(g=>g.primeMeasured>0).length+' games':'Showing lifetime career honors')
  +(loadErrors.length?' · Source coverage incomplete for '+loadErrors.join(', '):'');
 $('gameList').innerHTML=list.slice(0,expanded).map((g,i)=>{
  const stars=lens==='prime'
   ?g.stars.slice().sort((a,b)=>(b.prime.score??-1)-(a.prime.score??-1)||b.prestige-a.prestige)
   :g.stars;
  const scoreline=lens==='prime'
   ?'<div><strong>'+g.primePlayers+'</strong><small>Prime-era players</small></div><div><strong>'+g.primeMeasured+'/'+g.count+'</strong><small>Dated evidence</small></div><div><strong>'+(g.primeMeasured?g.primeIndex.toFixed(1):'—')+'</strong><small>Prime Era Index</small></div>'
   :'<div><strong>'+g.count+'</strong><small>Recognized players</small></div><div><strong>'+g.legends+'</strong><small>Marquee players</small></div><div><strong>'+g.index+'</strong><small>Career Star Power Index</small></div>';
  const line=p=>'<li><a href="'+esc(p.link)+'">'+esc(p.name)+'</a><small>'
   +(lens==='prime'?primeTierLabel(p)+'<span class="prime-context">'+esc(p.prime?.detail||'Undated career recognition')+'</span>':esc(p.tag))
   +'</small></li>';
  return '<article class="star-card"><div class="card-top"><span class="rank">#'+String(i+1).padStart(2,'0')+'</span><span class="sport">'+esc(g.sport)+'</span></div>'
   +'<h3>'+esc(g.away)+' <span aria-label="versus">vs.</span> '+esc(g.home)+'</h3>'
   +'<p class="meta">'+esc(fmt(g.date))+(g.venue?' · '+esc(g.venue):'')+'</p>'
   +'<div class="scoreline">'+scoreline+'</div>'
   +'<ul class="star-list">'+stars.slice(0,7).map(line).join('')+'</ul>'
   +(stars.length>7?'<details class="star-extra"><summary>Show '+(stars.length-7)+' more recognized '+(stars.length-7===1?'player':'players')+'</summary><ul class="star-list">'+stars.slice(7).map(line).join('')+'</ul></details>':'')
   +'<div class="card-footer"><span>'+esc(g.date)+' · '+esc(g.sport)+'</span><a href="'+esc(g.url)+'">Open game ↗</a></div></article>';
 }).join('')
 +(count>expanded?'<button class="load-more" id="moreStars" type="button">Show more games ('+(count-expanded)+' remaining)</button>':'')
 ||'<div class="empty">No qualifying games match these filters. Try a different sport, prime threshold, or search term.</div>';
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
 ['sportFilter','sortFilter','searchFilter','lensFilter','primeFilter'].forEach(id=>$(id).addEventListener(id==='searchFilter'?'input':'change',()=>{expanded=24;draw()}));
 draw();
}
init().catch(err=>{$('gameList').innerHTML='<div class="empty">Unable to assemble the archive collection right now. Please try again later.</div>';console.error(err)});
})();