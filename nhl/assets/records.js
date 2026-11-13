/* Courtside Archive NHL records: verified attended-game data only. */
(()=>{'use strict';
const el=id=>document.getElementById(id);
const esc=value=>String(value??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const date=value=>new Date(value+'T12:00:00Z').toLocaleDateString('en-US',{timeZone:'UTC',month:'short',day:'numeric',year:'numeric'});
const playerLink=r=>'<a href="./player.html?id='+encodeURIComponent(r.player.id)+'">'+esc(r.player.name)+'</a>';
const gameLink=g=>'<a href="./game.html?id='+encodeURIComponent(g.id)+'">View game ↗</a>';
const num=x=>x!==null&&x!==undefined&&x!==''&&Number.isFinite(Number(x))?Number(x):null;
const timeSeconds=value=>{
 const match=String(value||'').match(/^(\d+):([0-5]\d)$/);
 return match?Number(match[1])*60+Number(match[2]):null;
};
const statValue=(r,key)=>key==='minutes'?timeSeconds(r.stats.minutes):num(r.stats[key]);
const showValue=(value,key)=>{
 if(value===null||!Number.isFinite(value))return '—';
 if(key==='minutes')return Math.floor(value/60)+':'+String(value%60).padStart(2,'0');
 if(key==='save_pct')return value.toFixed(3).replace(/^0/, '');
 if(key==='plus_minus')return (value>0?'+':'')+value;
 return String(value);
};
const stats={
 skater:[
  {key:'goals',label:'Goals',title:'Most goals'},
  {key:'assists',label:'Assists',title:'Most assists'},
  {key:'points',label:'Points',title:'Most points'},
  {key:'shots_on_goal',label:'Shots on goal',title:'Most shots on goal'},
  {key:'plus_minus',label:'Plus/minus',title:'Best plus/minus'},
  {key:'minutes',label:'Ice time',title:'Most ice time'},
  {key:'penalty_minutes',label:'Penalty minutes',title:'Most penalty minutes'}
 ],
 goalie:[
  {key:'saves',label:'Saves',title:'Most saves'},
  {key:'shots_against',label:'Shots faced',title:'Most shots faced'},
  {key:'shutouts',label:'Shutouts',title:'Most shutouts'},
  {key:'wins',label:'Wins',title:'Most wins'},
  {key:'save_pct',label:'Save percentage',title:'Highest save percentage'},
  {key:'minutes',label:'Ice time',title:'Most ice time'}
 ]
};
const milestones=[
 {key:'points3',title:'3+ points',role:'skater',test:r=>statValue(r,'points')>=3},
 {key:'goals2',title:'2+ goals',role:'skater',test:r=>statValue(r,'goals')>=2},
 {key:'assists2',title:'2+ assists',role:'skater',test:r=>statValue(r,'assists')>=2},
 {key:'shots5',title:'5+ shots on goal',role:'skater',test:r=>statValue(r,'shots_on_goal')>=5},
 {key:'shots7',title:'7+ shots on goal',role:'skater',test:r=>statValue(r,'shots_on_goal')>=7},
 {key:'time20',title:'20+ minutes on ice',role:'skater',test:r=>statValue(r,'minutes')>=1200},
 {key:'saves30',title:'30+ saves',role:'goalie',test:r=>statValue(r,'saves')>=30},
 {key:'saves35',title:'35+ saves',role:'goalie',test:r=>statValue(r,'saves')>=35},
 {key:'shutout',title:'Goaltender shutout',role:'goalie',test:r=>statValue(r,'shutouts')>=1},
 {key:'savepct950',title:'.950+ save percentage (20+ shots faced)',role:'goalie',test:r=>statValue(r,'shots_against')>=20&&statValue(r,'save_pct')>=.950}
];
const rowLine=r=>r.role==='goalie'
 ?showValue(statValue(r,'saves'),'saves')+' SV · '+showValue(statValue(r,'shots_against'),'shots_against')+' SA · '+showValue(statValue(r,'save_pct'),'save_pct')+' SV%'
 :showValue(statValue(r,'goals'),'goals')+' G · '+showValue(statValue(r,'assists'),'assists')+' A · '+showValue(statValue(r,'points'),'points')+' PTS';
const table=(headings,rows,message='No qualifying verified performances yet.')=>
 '<div class="nhl-rec-scroll"><table><thead><tr>'+headings.map(h=>'<th scope="col">'+esc(h)+'</th>').join('')+'</tr></thead><tbody>'
 +(rows.length?rows.map(cells=>'<tr>'+cells.map(cell=>'<td>'+cell+'</td>').join('')+'</tr>').join(''):'<tr><td colspan="'+headings.length+'" class="nhl-rec-empty">'+esc(message)+'</td></tr>')
 +'</tbody></table></div>';
function render(games){
 const all=games.flatMap(g=>(g.players||[]).filter(p=>p.skater||p.goalie).map(p=>({player:p,game:g,role:p.goalie?'goalie':'skater',stats:p.goalie||p.skater})));
 const skaters=all.filter(r=>r.role==='skater'),goalies=all.filter(r=>r.role==='goalie');
 const gameScore=g=>esc(g.away)+' '+g.away_score+'–'+g.home_score+' '+esc(g.home);
 const sorted=games.slice().sort((a,b)=>a.date.localeCompare(b.date)||a.id.localeCompare(b.id));
 const coverage=sorted.length+' '+(sorted.length===1?'game':'games')+' attended · '+new Set(all.map(r=>r.player.id)).size+' participating players · '+date(sorted[0].date)+(sorted.length>1?' – '+date(sorted[sorted.length-1].date):'');
 el('app').innerHTML='<div class="nhl-records-page">'
  +'<header class="nhl-rec-hero"><div class="nhl-rec-eyebrow">NHL · YOUR PERSONAL RECORD BOOK</div><h1>The best I&#39;ve witnessed.</h1><p>Official single-game records, statistical milestones, team achievements and legendary performances from your attended NHL history.</p><div class="nhl-rec-coverage">'+esc(coverage)+'</div></header>'
  +'<div class="nhl-rec-tabs" id="nhl-rec-tabs" role="tablist" aria-label="NHL Records sections">'
  +[['records','Record Book'],['milestones','Milestones'],['teams','Team & Game Records'],['legendary','Legendary Performances']].map(([key,label],i)=>'<button type="button" role="tab" id="nhl-rec-tab-'+key+'" aria-controls="nhl-rec-panel-'+key+'" data-tab="'+key+'" aria-selected="'+(i===0)+'" tabindex="'+(i===0?'0':'-1')+'">'+label+'</button>').join('')
  +'</div>'
  +'<section class="nhl-rec-tabpanel" id="nhl-rec-panel-records" role="tabpanel" aria-labelledby="nhl-rec-tab-records"><div class="nhl-rec-heading"><h2>Single-game record holders</h2><span>Individual games, not career totals</span></div>'
   +'<div class="nhl-rec-subtabs" id="nhl-rec-roles" role="group" aria-label="Position group"><button type="button" data-role="skater" aria-pressed="true">Skaters</button><button type="button" data-role="goalie" aria-pressed="false">Goaltenders</button></div>'
   +'<div class="nhl-rec-grid" id="nhl-rec-cards"></div>'
   +'<section class="nhl-rec-panel"><h2>Top 10 single-game performances</h2><p>Rank the best individual performances by statistic. Tied games and repeat appearances are listed separately.</p>'
    +'<div class="nhl-rec-filter"><label for="nhl-rec-stat">Statistic<select id="nhl-rec-stat"></select></label><span class="nhl-rec-caption" id="nhl-rec-result-count"></span></div><div id="nhl-rec-top"></div></section>'
  +'</section>'
  +'<section class="nhl-rec-tabpanel" id="nhl-rec-panel-milestones" role="tabpanel" aria-labelledby="nhl-rec-tab-milestones" hidden><section class="nhl-rec-panel"><h2>Statistical milestones</h2><p>Choose a hockey benchmark, then see individual qualifying games or how frequently each player achieved it.</p>'
   +'<div class="nhl-rec-filter"><label for="nhl-rec-milestone">Milestone<select id="nhl-rec-milestone">'+milestones.map(m=>'<option value="'+m.key+'">'+esc(m.title)+'</option>').join('')+'</select></label></div>'
   +'<div class="nhl-rec-metrics"><div class="nhl-rec-metric"><strong id="nhl-rec-qualifying">0</strong><small>Qualifying performances</small></div><div class="nhl-rec-metric"><strong id="nhl-rec-unique">0</strong><small>Unique players</small></div></div>'
   +'<div class="nhl-rec-subtabs" id="nhl-rec-milestone-modes" role="group" aria-label="Milestone rankings"><button type="button" data-mode="performances" aria-pressed="true">Individual performances</button><button type="button" data-mode="players" aria-pressed="false">Player frequency rankings</button></div><div id="nhl-rec-milestone-table"></div></section></section>'
  +'<section class="nhl-rec-tabpanel" id="nhl-rec-panel-teams" role="tabpanel" aria-labelledby="nhl-rec-tab-teams" hidden><div class="nhl-rec-heading"><h2>Team &amp; game records</h2><span>Official scores and period-by-period results</span></div>'
   +'<div class="nhl-rec-grid" id="nhl-rec-team-cards"></div>'
   +'<section class="nhl-rec-panel"><h2>Every attended NHL game</h2><div class="nhl-rec-filter"><label for="nhl-rec-game-sort">Sort games<select id="nhl-rec-game-sort"><option value="oldest">Date · oldest first</option><option value="recent">Date · newest first</option><option value="goals">Most combined goals</option><option value="margin">Largest winning margin</option></select></label></div><div id="nhl-rec-games"></div></section></section>'
  +'<section class="nhl-rec-tabpanel" id="nhl-rec-panel-legendary" role="tabpanel" aria-labelledby="nhl-rec-tab-legendary" hidden><div class="nhl-rec-heading"><h2>Legendary performances</h2><span>Verified hockey feats and memorable moments</span></div>'
   +'<section class="nhl-rec-panel"><h2>Statistical feats</h2><p>Automatically qualified using box-score thresholds; a single player-game can achieve more than one feat.</p><div class="nhl-rec-subtabs" id="nhl-rec-feat-roles" role="group" aria-label="Feat position group"><button type="button" data-role="all" aria-pressed="true">All</button><button type="button" data-role="skater" aria-pressed="false">Skaters</button><button type="button" data-role="goalie" aria-pressed="false">Goaltenders</button></div><div id="nhl-rec-feats"></div></section>'
   +'<section class="nhl-rec-panel"><h2>Iconic game moments</h2><p>Verified shutouts, standout scoring periods and overtime finishes—not unverified historical claims.</p><div id="nhl-rec-moments"></div></section></section>'
  +'<p class="nhl-rec-foot">Only official statistics from games in this archive count. Career NHL award totals and statistics are not included in record rankings. Rankings expand as additional attended games are entered.</p></div>';

 el('nhl-rec-tabs').addEventListener('click',event=>{
  const btn=event.target.closest('button[data-tab]');if(!btn)return;
  el('nhl-rec-tabs').querySelectorAll('button').forEach(b=>{const active=b===btn;b.setAttribute('aria-selected',String(active));b.tabIndex=active?0:-1});
  ['records','milestones','teams','legendary'].forEach(k=>el('nhl-rec-panel-'+k).hidden=k!==btn.dataset.tab);
 });
 const setPressed=(container,key,callback)=>{
  el(container).addEventListener('click',event=>{
   const chosen=event.target.closest('button[data-'+key+']');if(!chosen)return;
   el(container).querySelectorAll('button').forEach(b=>b.setAttribute('aria-pressed',String(b===chosen)));
   callback(chosen.dataset[key]);
  });
 };
 const ranked=(rows,key)=>rows.map(r=>({...r,value:statValue(r,key)}))
  .filter(r=>r.value!==null&&(key==='plus_minus'||r.value>0))
  .sort((a,b)=>b.value-a.value||a.game.date.localeCompare(b.game.date)||a.player.name.localeCompare(b.player.name));
 const recordCard=(title,top,key)=>{
  if(!top.length)return '<article class="nhl-rec-card"><span>'+esc(title)+'</span><strong>—</strong><small>Awaiting verified data</small></article>';
  const best=top[0],tied=top.filter(r=>r.value===best.value);
  const detail=tied.slice(0,3).map(r=>playerLink(r)).join(' · ')+(tied.length>3?' · +'+(tied.length-3)+' tied':'');
  return '<article class="nhl-rec-card"><span>'+esc(title)+'</span><strong>'+esc(showValue(best.value,key))+'</strong><div class="nhl-rec-owner">'+detail+'</div><small>'+esc(date(best.game.date))+'</small>'+gameLink(best.game)+'</article>';
 };
 let role='skater',recordKey='points';
 const drawRecords=()=>{
  const defs=stats[role],rows=role==='skater'?skaters:goalies;
  el('nhl-rec-stat').innerHTML=defs.map(d=>'<option value="'+d.key+'">'+esc(d.label)+'</option>').join('');
  if(!defs.some(d=>d.key===recordKey))recordKey=role==='skater'?'points':'saves';
  el('nhl-rec-stat').value=recordKey;
  el('nhl-rec-cards').innerHTML=defs.slice(0,6).map(d=>recordCard(d.title,ranked(rows,d.key),d.key)).join('');
  drawTop();
 };
 const drawTop=()=>{
  recordKey=el('nhl-rec-stat').value;
  const rankedRows=ranked(role==='skater'?skaters:goalies,recordKey);
  const def=stats[role].find(d=>d.key===recordKey);
  el('nhl-rec-result-count').textContent=Math.min(10,rankedRows.length)+' of '+rankedRows.length+' verified performances';
  el('nhl-rec-top').innerHTML=table(['Rank','Player','Team','Date',def.label,'Game'],rankedRows.slice(0,10).map((r,i)=>[
   String(i+1),playerLink(r),esc(r.player.team),esc(date(r.game.date)),
   '<strong class="nhl-rec-highlight">'+esc(showValue(r.value,recordKey))+'</strong>',gameLink(r.game)
  ]));
 };
 setPressed('nhl-rec-roles','role',value=>{role=value;recordKey=role==='goalie'?'saves':'points';drawRecords()});
 el('nhl-rec-stat').addEventListener('change',drawTop);drawRecords();
 let milestoneMode='performances';
 function drawMilestone(){
  const def=milestones.find(m=>m.key===el('nhl-rec-milestone').value)||milestones[0];
  const matches=all.filter(r=>r.role===def.role&&def.test(r)).sort((a,b)=>a.game.date.localeCompare(b.game.date)||a.player.name.localeCompare(b.player.name));
  const identities=new Set(matches.map(r=>r.player.id));
  el('nhl-rec-qualifying').textContent=matches.length;
  el('nhl-rec-unique').textContent=identities.size;
  if(milestoneMode==='performances'){
   el('nhl-rec-milestone-table').innerHTML=table(['Player','Team','Date','Stat line','Game'],matches.map(r=>[
    playerLink(r),esc(r.player.team),esc(date(r.game.date)),esc(rowLine(r)),gameLink(r.game)
   ]),'No recorded player-games meet this milestone.');
  }else{
   const counts=new Map();for(const r of matches){const id=r.player.id;const existing=counts.get(id)||{row:r,times:0};existing.times++;counts.set(id,existing)}
   const rankedPeople=[...counts.values()].sort((a,b)=>b.times-a.times||a.row.player.name.localeCompare(b.row.player.name));
   el('nhl-rec-milestone-table').innerHTML=table(['Player','Team','Times reached','Profile'],rankedPeople.map(r=>[
    playerLink(r.row),esc(r.row.player.team),'<strong class="nhl-rec-highlight">'+r.times+'</strong>',playerLink(r.row)
   ]),'No players meet this milestone.');
  }
 }
 setPressed('nhl-rec-milestone-modes','mode',v=>{milestoneMode=v;drawMilestone()});
 el('nhl-rec-milestone').addEventListener('change',drawMilestone);drawMilestone();
 const teamRows=games.flatMap(g=>[{'game':g,'name':g.away,'goals':num(g.away_score),'shots':num(g.team_stats?.away?.shots_on_goal),'periods':g.periods?.away||[],'side':'away'},
                                   {'game':g,'name':g.home,'goals':num(g.home_score),'shots':num(g.team_stats?.home?.shots_on_goal),'periods':g.periods?.home||[],'side':'home'}]);
 const descending=(rows,fn)=>rows.slice().filter(r=>Number.isFinite(fn(r))).sort((a,b)=>fn(b)-fn(a)||a.game.date.localeCompare(b.game.date));
 const teamCard=(title,value,detail,g)=>'<article class="nhl-rec-card"><span>'+esc(title)+'</span><strong>'+esc(value??'—')+'</strong><div class="nhl-rec-owner">'+esc(detail||'')+'</div>'+(g?gameLink(g):'')+'</article>';
 const highGoals=descending(teamRows,r=>r.goals)[0],highShots=descending(teamRows,r=>r.shots)[0];
 const combined=descending(games,g=>num(g.away_score)+num(g.home_score))[0];
 const margin=descending(games,g=>Math.abs(num(g.away_score)-num(g.home_score)))[0];
 const shutouts=games.filter(g=>g.home_score===0||g.away_score===0);
 const periodRows=teamRows.flatMap(r=>r.periods.map((v,i)=>({...r,period:i+1,periodGoals:num(v)})));
 const bigPeriod=descending(periodRows,r=>r.periodGoals)[0];
 el('nhl-rec-team-cards').innerHTML=[
  teamCard('Most team goals',highGoals?.goals,highGoals?.name,highGoals?.game),
  teamCard('Most combined goals',combined?combined.away_score+combined.home_score:null,combined?combined.away+' at '+combined.home:'',combined),
  teamCard('Largest winning margin',margin?Math.abs(margin.away_score-margin.home_score):null,margin?margin.away+' at '+margin.home:'',margin),
  teamCard('Most team shots on goal',highShots?.shots,highShots?.name,highShots?.game),
  teamCard('Most goals in a period',bigPeriod?.periodGoals,bigPeriod?bigPeriod.name+' · Period '+bigPeriod.period:'',bigPeriod?.game),
  teamCard('Shutout games',shutouts.length,'Across '+games.length+' attended '+(games.length===1?'game':'games'))
 ].join('');
 const drawGames=()=>{
  const kind=el('nhl-rec-game-sort').value;
  const ordered=games.slice().sort((a,b)=>kind==='recent'?b.date.localeCompare(a.date):kind==='goals'?(b.away_score+b.home_score)-(a.away_score+a.home_score):kind==='margin'?Math.abs(b.away_score-b.home_score)-Math.abs(a.away_score-a.home_score):a.date.localeCompare(b.date));
  el('nhl-rec-games').innerHTML=table(['Date','Matchup','Final','Total goals','Margin','Shutout','Game'],ordered.map(g=>[
   esc(date(g.date)),esc(g.away+' at '+g.home),esc(g.away_score+'–'+g.home_score),
   String(g.away_score+g.home_score),String(Math.abs(g.away_score-g.home_score)),
   g.away_score===0||g.home_score===0?'Yes':'No',gameLink(g)
  ]),'No official NHL game results are available.');
 };
 el('nhl-rec-game-sort').addEventListener('change',drawGames);drawGames();
 const feats=[];
 const feat=(r,title)=>feats.push({r,title,line:rowLine(r)});
 for(const r of all){
  if(r.role==='skater'){
   if(statValue(r,'points')>=3)feat(r,'3+ points');
   if(statValue(r,'goals')>=3)feat(r,'Hat trick');
   else if(statValue(r,'goals')>=2)feat(r,'Multi-goal game');
   if(statValue(r,'assists')>=3)feat(r,'3+ assists');
   if(statValue(r,'shots_on_goal')>=7)feat(r,'7+ shots on goal');
  }else{
   if(statValue(r,'shutouts')>=1)feat(r,'Goaltender shutout');
   if(statValue(r,'saves')>=35)feat(r,'35+ saves');
   if(statValue(r,'save_pct')>=.950&&statValue(r,'shots_against')>=20)feat(r,'.950+ save percentage');
  }
 }
 feats.sort((a,b)=>a.r.game.date.localeCompare(b.r.game.date)||a.r.player.name.localeCompare(b.r.player.name)||a.title.localeCompare(b.title));
 let featRole='all';
 const drawFeats=()=>{
  const rows=feats.filter(f=>featRole==='all'||featRole===f.r.role);
  el('nhl-rec-feats').innerHTML=table(['Achievement','Player','Stat line','Date','Game'],rows.map(f=>[
   '<span class="nhl-rec-pill">'+esc(f.title)+'</span>',playerLink(f.r),esc(f.line),esc(date(f.r.game.date)),gameLink(f.r.game)
  ]),'No verified legendary feats in this category yet.');
 };
 setPressed('nhl-rec-feat-roles','role',v=>{featRole=v;drawFeats()});drawFeats();
 const moments=[];
 const moment=(g,title,detail)=>moments.push({g,title,detail});
 for(const g of games){
  const winner=g.home_score>g.away_score?g.home:g.away_score>g.home_score?g.away:null;
  const loserGoals=Math.min(g.away_score,g.home_score);
  if(winner&&loserGoals===0)moment(g,'Shutout victory',winner+' won '+Math.max(g.home_score,g.away_score)+'–0'); 
  if(g.periods){
   for(const r of [{name:g.away,values:g.periods.away},{name:g.home,values:g.periods.home}]){
    (r.values||[]).forEach((goals,i)=>{if(num(goals)>=3)moment(g,'3+ goal period',r.name+' scored '+goals+' goals in Period '+(i+1))});
   }
   if((g.periods.away||[]).length>3||(g.periods.home||[]).length>3)moment(g,'Overtime finish',g.away+' at '+g.home);
  }
  if(g.away_score+g.home_score>=9)moment(g,'High-scoring game',g.away_score+g.home_score+' combined goals');
 }
 el('nhl-rec-moments').innerHTML=moments.length?'<div class="nhl-rec-moments">'+moments.map(m=>
  '<article class="nhl-rec-moment"><span>'+esc(m.title)+'</span><strong>'+esc(m.detail)+'</strong><small>'+esc(date(m.g.date))+' · '+gameScore(m.g)+'</small>'+gameLink(m.g)+'</article>').join('')+'</div>':'<p class="nhl-rec-caption">No qualifying iconic moments have been recorded yet.</p>';
}
window.NHLRecords={render};
})();