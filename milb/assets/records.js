/* Courtside Archive MiLB Records — same four-section structure as MLB.
   Stats are independently sourced from attended MiLB games ONLY. */
(()=>{"use strict";
const $=id=>document.getElementById(id);
const esc=v=>String(v??"").replace(/[&<>"']/g,c=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[c]));
const date=s=>s?new Date(String(s)+"T12:00:00").toLocaleDateString("en-US",{month:"short",day:"numeric",year:"numeric"}):"—";
const n=v=>v===null||v===undefined||v===""?null:Number.isFinite(Number(v))?Number(v):null;
const fmt=v=>Number(v||0).toLocaleString("en-US");
const inningsOuts=ip=>{const m=/^(\d+)(?:\.([012]))?$/.exec(String(ip??""));return m?Number(m[1])*3+Number(m[2]||0):null};
const gameLink=g=>"./game.html?id="+encodeURIComponent(g.id);
const playerLink=r=>"./player.html?id="+encodeURIComponent(r.player_id);
const official=g=>g.box_score_status==="verified"&&g.source_game_id!=null;
const defs=[
 ["Hits","batting","h","H"],["Home runs","batting","hr","HR"],["RBI","batting","rbi","RBI"],
 ["Stolen bases","batting","sb","SB"],["Pitching strikeouts","pitching","so","SO"],["Pitching outs","pitching","outs","Outs"],
 ["Doubles","batting","doubles","2B"],["Walks","batting","bb","BB"],["Runs","batting","r","R"]
];
const milestones=[
 ["3+ hits","batting","h",3],["4+ hits","batting","h",4],
 ["2+ home runs","batting","hr",2],["3+ RBI","batting","rbi",3],
 ["2+ stolen bases","batting","sb",2],["8+ pitcher Ks","pitching","so",8],
 ["10+ pitcher Ks","pitching","so",10],["7+ innings (21 outs)","pitching","outs",21]
];
function val(r,type,key){
 const data=r?.[type];if(!data)return null;
 return type==="pitching"&&key==="outs"?inningsOuts(data.ip):n(data[key]);
}
const gameText=g=>g.away_team+" @ "+g.home_team;
function table(headers,lines,empty){
 return '<div class="table-wrap"><table class="mlb-sticky"><thead><tr>'+headers.map(h=>'<th>'+esc(h)+'</th>').join("")+'</tr></thead><tbody>'
 +(lines.length?lines.join(""):'<tr><td colspan="'+headers.length+'">'+esc(empty||"No verified qualifying entries.")+'</td></tr>')+'</tbody></table></div>';
}
const tiles=items=>'<div class="metrics">'+items.map(([label,v])=>'<div class="metric"><strong>'+esc(fmt(v))+'</strong><small>'+esc(label)+'</small></div>').join("")+'</div>';
function record(label,v,details,g){
 return '<article class="mlb-record"><small>'+esc(label)+'</small><strong>'+esc(v===null||v===undefined?"—":v)+'</strong><p>'+esc(details)+'</p>'
 +(g?'<a href="'+gameLink(g)+'">Explore game ↗</a>':"")+'</article>';
}
function rankings(rows,byGame,type,key,threshold=1){
 return rows.map(r=>({r,g:byGame.get(String(r.game_id)),value:val(r,type,key)}))
  .filter(x=>x.g&&official(x.g)&&x.value!==null&&x.value>=threshold)
  .sort((a,b)=>b.value-a.value||String(a.r.date).localeCompare(String(b.r.date))||String(a.r.name).localeCompare(String(b.r.name))||String(a.r.player_id).localeCompare(String(b.r.player_id)));
}
function rankingTable(values,label){
 return table(["Rank","Player","Club","Date",label,"Game"],values.map((x,i)=>
  '<tr><td>'+(i+1)+'</td><td><a href="'+playerLink(x.r)+'">'+esc(x.r.name)+'</a></td><td>'+esc(x.r.team||"—")+'</td>'
  +'<td>'+date(x.r.date)+'</td><td><strong>'+esc(x.value)+'</strong></td><td><a href="'+gameLink(x.g)+'">Game ↗</a></td></tr>'),
  "No verified qualifying single-game performances.");
}
function gameRow(g){
 return '<tr><td><a href="'+gameLink(g)+'">'+date(g.date)+'</a></td><td>'+esc(gameText(g))+'</td>'
 +'<td>'+esc(g.venue||"—")+'</td><td>'+esc(g.away_score)+"–"+esc(g.home_score)+'</td>'
 +'<td><span class="mlb-pill verified">Matched</span></td><td><a href="'+gameLink(g)+'">View ↗</a></td></tr>';
}
function init(games,rows,inningScores){
 const officialGames=games.filter(official);
 const byGame=new Map(games.map(g=>[String(g.id),g]));
 const byPk=new Map(games.filter(g=>g.source_game_id!=null).map(g=>[String(g.source_game_id),g]));
 const eligible=rows.filter(r=>byGame.has(String(r.game_id))&&official(byGame.get(String(r.game_id)))&&r.player_id!=null);
 const sorted=officialGames.filter(g=>n(g.away_score)!==null&&n(g.home_score)!==null);
 // Extra innings is verified only when inning-by-inning data was imported.
 const getInnings=g=>inningScores[String(g.source_game_id)]||[];
 const extras=sorted.filter(g=>getInnings(g).some(i=>n(i.inning)>9));
 const longest=sorted.filter(g=>getInnings(g).length).slice().sort((a,b)=>{
  const count=g=>Math.max(...getInnings(g).map(i=>n(i.inning)||0),0);
  return count(b)-count(a)||a.date.localeCompare(b.date);
 })[0]||null;
 const first=defs.slice(0,6);
 $("app").innerHTML='<div class="eyebrow">MiLB · Your personal record book</div>'
  +'<h1>The best I&#39;ve witnessed.</h1>'
  +'<p class="lead">Official single-game records, individual milestones, team achievements and memorable performances from your attended Minor League Baseball history. These statistics never include MLB or college baseball games.</p>'
  +'<div class="mlb-nav-tabs" id="mainTabs" role="tablist" aria-label="MiLB records sections">'
  +[["records","Record Book"],["milestones","Milestones"],["teams","Team & Game Records"],["legendary","Legendary Performances"]]
    .map(([key,label],i)=>'<button type="button" role="tab" data-tab="'+key+'" aria-controls="'+key+'Tab" aria-selected="'+(i===0)+'">'+label+'</button>').join("")+'</div>'
  +'<section class="mlb-tab" id="recordsTab" role="tabpanel"><h2>Single-game record holders</h2><div class="mlb-records-grid" id="recordCards"></div>'
  +'<section class="panel"><h2>Top 10 single-game performances</h2><div class="mlb-filters"><label for="recordCategory">Statistic<select id="recordCategory">'
  +defs.map(([label,type,key])=>'<option value="'+type+':'+key+'">'+esc(label)+'</option>').join("")+'</select></label></div>'
  +'<div id="recordTop"></div></section></section>'
  +'<section class="mlb-tab" id="milestonesTab" role="tabpanel" hidden><section class="panel"><h2>Statistical milestones</h2>'
  +'<p class="mlb-note">Each threshold counts qualifying individual MiLB games. Switch to player frequency to identify repeats.</p>'
  +'<div class="mlb-filters"><label for="milestoneStat">Milestone<select id="milestoneStat">'
  +milestones.map(([label,type,key,min])=>'<option value="'+type+':'+key+':'+min+'">'+esc(label)+'</option>').join("")+'</select></label>'
  +'<label for="milestoneView">View<select id="milestoneView"><option value="games">Player-games</option><option value="players">Player frequency</option></select></label></div>'
  +'<div id="milestoneMetrics"></div><div id="milestoneTable"></div></section></section>'
  +'<section class="mlb-tab" id="teamsTab" role="tabpanel" hidden><h2>Team & Game Records</h2><div id="teamCards" class="mlb-records-grid"></div>'
  +'<section class="panel"><h2>Every officially matched game</h2><div id="teamGameTable"></div></section></section>'
  +'<section class="mlb-tab" id="legendaryTab" role="tabpanel" hidden>'
  +'<section class="panel"><h2>Statistical Feats</h2><p class="mlb-note">Achievements grounded in official attended-game box scores, not subjective league awards.</p><div id="feats"></div></section>'
  +'<section class="panel"><h2>Iconic Moments</h2><p class="mlb-note">High-scoring games, extra innings, shutouts, and other confirmed team achievements.</p><div id="moments"></div></section></section>'
  +'<p class="mlb-note">Coverage: '+officialGames.length+' of '+games.length+' attended MiLB games matched to official game IDs. Only imported player-game lines are ranked; missing statistics are never counted as zero.</p>';
 const tabKeys=["records","milestones","teams","legendary"];
 const tab=key=>{
  $("mainTabs").querySelectorAll("[data-tab]").forEach(b=>b.setAttribute("aria-selected",String(b.dataset.tab===key)));
  tabKeys.forEach(name=>$(name+"Tab").hidden=name!==key);
 };
 $("mainTabs").querySelectorAll("[data-tab]").forEach(b=>b.addEventListener("click",()=>tab(b.dataset.tab)));
 $("recordCards").innerHTML=first.map(([label,type,key])=>{
  const top=rankings(eligible,byGame,type,key)[0];
  return record("Most "+label.toLowerCase(),top?.value??null,top?top.r.name+" · "+date(top.r.date):"Awaiting verified player box scores",top?.g);
 }).join("");
 const drawRank=()=>{
  const [type,key]=$("recordCategory").value.split(":");
  const label=defs.find(d=>d[1]===type&&d[2]===key)?.[0]||key;
  $("recordTop").innerHTML=rankingTable(rankings(eligible,byGame,type,key).slice(0,10),label);
 };
 $("recordCategory").addEventListener("change",drawRank);drawRank();
 const drawMilestone=()=>{
  const [type,key,str]=$("milestoneStat").value.split(":");
  const found=rankings(eligible,byGame,type,key,Number(str));
  $("milestoneMetrics").innerHTML=tiles([
   ["Qualifying player-games",found.length],
   ["Unique players",new Set(found.map(x=>String(x.r.player_id))).size],
   ["Covered games",new Set(eligible.map(r=>String(r.game_id))).size],
   ["Games attended",games.length]
  ]);
  if($("milestoneView").value==="games"){
   $("milestoneTable").innerHTML=rankingTable(found,defs.find(d=>d[1]===type&&d[2]===key)?.[0]||key);return;
  }
  const grouped=new Map();
  for(const x of found){const id=String(x.r.player_id),o=grouped.get(id)||{r:x.r,count:0};o.count++;grouped.set(id,o);}
  const individuals=[...grouped.values()].sort((a,b)=>b.count-a.count||a.r.name.localeCompare(b.r.name));
  $("milestoneTable").innerHTML=table(["Player","Times reached","Profile"],individuals.map(x=>
   '<tr><td><a href="'+playerLink(x.r)+'">'+esc(x.r.name)+'</a></td><td>'+x.count+'</td><td><a href="'+playerLink(x.r)+'">View ↗</a></td></tr>'),"No player meets this threshold.");
 };
 ["milestoneStat","milestoneView"].forEach(id=>$(id).addEventListener("change",drawMilestone));drawMilestone();
 const byRuns=sorted.slice().sort((a,b)=>(b.away_score+b.home_score)-(a.away_score+a.home_score)||a.date.localeCompare(b.date));
 const byDiff=sorted.slice().sort((a,b)=>Math.abs(b.away_score-b.home_score)-Math.abs(a.away_score-a.home_score)||a.date.localeCompare(b.date));
 const topRuns=byRuns[0],topDiff=byDiff[0];
 const length=g=>getInnings(g).reduce((m,x)=>Math.max(m,n(x.inning)||0),0);
 $("teamCards").innerHTML=[
  record("Most combined runs",topRuns?topRuns.away_score+topRuns.home_score:null,topRuns?gameText(topRuns):"No verified scores",topRuns),
  record("Largest final run margin",topDiff?Math.abs(topDiff.away_score-topDiff.home_score):null,topDiff?gameText(topDiff):"No verified scores",topDiff),
  record("Extra-inning games",extras.length,"Verified inning-by-inning line scores"),
  record("Longest attended game",longest?length(longest)+" innings":null,"Official inning-level data only",longest),
  record("One-run games",sorted.filter(g=>Math.abs(g.home_score-g.away_score)===1).length,"Completed matched games"),
  record("Shutout games",sorted.filter(g=>g.home_score===0||g.away_score===0).length,"Completed matched games")
 ].join("");
 $("teamGameTable").innerHTML=table(["Date","Matchup","Ballpark","Final","Status","Game"],
  sorted.slice().sort((a,b)=>b.date.localeCompare(a.date)||String(a.id).localeCompare(String(b.id))).map(gameRow),"No officially verified game results.");
 const events=[];
 for(const [type,key,min,label] of [["batting","h",4,"Four-hit game"],["batting","hr",2,"Multi-home-run game"],
  ["batting","rbi",5,"Five-RBI game"],["pitching","so",10,"Double-digit Ks"],["pitching","outs",27,"Nine full innings pitched"]]){
  for(const x of rankings(eligible,byGame,type,key,min))events.push({...x,label});
 }
 events.sort((a,b)=>b.r.date.localeCompare(a.r.date)||a.r.name.localeCompare(b.r.name));
 $("feats").innerHTML=events.length?table(["Achievement","Player","Date","Value","Game"],events.map(x=>
  '<tr><td>'+esc(x.label)+'</td><td><a href="'+playerLink(x.r)+'">'+esc(x.r.name)+'</a></td><td>'+date(x.r.date)+'</td><td>'+x.value+'</td><td><a href="'+gameLink(x.g)+'">Game ↗</a></td></tr>'))
  :'<div class="empty">No verified qualifying statistical feats yet.</div>';
 $("moments").innerHTML=table(["Date","Match","Highlight","Score","Game"],byRuns.slice(0,25).map(g=>{
  const x=length(g),highlight=x>9?"Extra innings":g.home_score===0||g.away_score===0?"Shutout":"High-scoring / attended game";
  return '<tr><td>'+date(g.date)+'</td><td>'+esc(gameText(g))+'</td><td>'+esc(highlight)+'</td><td>'+g.away_score+'–'+g.home_score+'</td><td><a href="'+gameLink(g)+'">Game ↗</a></td></tr>';
 }),"No verified games available.");
 if(location.hash==="#milestones")tab("milestones");
}
document.addEventListener("DOMContentLoaded",async()=>{
 try{
  const get=async(name)=>{const r=await fetch("./data/"+name+".json",{cache:"no-store"});if(!r.ok)throw Error(name+" unavailable");return r.json();};
  const [games,rows,innings]=await Promise.all(["games","player_stats","inning_scores"].map(get));
  if(!Array.isArray(games)||!Array.isArray(rows)||!innings||typeof innings!=="object")throw Error("Unexpected MiLB data shape");
  init(games,rows,innings);
 }catch(err){$("app").innerHTML='<div class="empty">Unable to load MiLB records: '+esc(err.message)+'</div>';}
});
})();
