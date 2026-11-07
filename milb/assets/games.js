/* MiLB Games — MLB-style game picker, scoreboard, lineups and box scores.
   All data requests stay within milb/data, independently of MLB. */
(()=>{"use strict";
const $=id=>document.getElementById(id);
const esc=v=>String(v??"").replace(/[&<>"']/g,c=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[c]));
const num=v=>v==null||v===""?null:Number.isFinite(Number(v))?Number(v):null;
const n=v=>num(v)||0;
const dt=s=>s?new Date(String(s)+"T12:00:00").toLocaleDateString("en-US",{year:"numeric",month:"short",day:"numeric"}):"Date pending";
const encode=v=>encodeURIComponent(String(v));
const playerUrl=r=>"./player.html?id="+encode(r.player_id);
const gameUrl=g=>"./game.html?id="+encode(g.id);
const fmt=(v,key)=>v===null||v===undefined||v===""?"—":String(v);
const recordedOuts=ip=>{const m=/^(\d+)(?:\.([012]))?$/.exec(String(ip??""));return m?Number(m[1])*3+Number(m[2]||0):null};
const labels={ab:"AB",pa:"PA",r:"R",h:"H",doubles:"2B",triples:"3B",hr:"HR",rbi:"RBI",bb:"BB",so:"SO",hbp:"HBP",sb:"SB",cs:"CS",ip:"IP",er:"ER",pitches:"Pitches",bf:"BF",putOuts:"PO",assists:"A",errors:"E"};
const battingFields=["ab","r","h","doubles","triples","hr","rbi","bb","so"];
const pitchingFields=["ip","h","er","bb","so","hr","pitches"];
const fieldingFields=["putOuts","assists","errors"];
const official=g=>g.source_game_id!=null&&g.box_score_status==="verified";
const scores=g=>g.away_score!=null&&g.home_score!=null?g.away_score+" – "+g.home_score:"—";
function impact(r){
 const b=r.batting,p=r.pitching;let hitter=null,pitcher=null,parts=[];
 if(b){
  const hits=n(b.h),dbl=n(b.doubles),tri=n(b.triples),hr=n(b.hr);
  const singles=Math.max(0,hits-dbl-tri-hr);
  if(["ab","h","r","rbi","bb","hbp","sb"].some(k=>n(b[k])>0)){
   hitter=singles+2*dbl+3*tri+4*hr+0.9*n(b.rbi)+0.7*n(b.r)+0.7*(n(b.bb)+n(b.hbp))+1.1*n(b.sb)-0.8*n(b.cs)-0.15*n(b.so);
   if(num(b.ab)!==null)parts.push(hits+"-for-"+b.ab);
   if(hr)parts.push(hr+" HR");if(n(b.rbi))parts.push(b.rbi+" RBI");if(n(b.sb))parts.push(b.sb+" SB");
  }
 }
 if(p){
  const outs=recordedOuts(p.ip);
  if(outs!==null){
   pitcher=1.5*outs/3+0.65*n(p.so)-1.8*n(p.er)-0.35*n(p.h)-0.35*n(p.bb)-0.5*n(p.hr)-0.2*n(p.hbp);
   if(outs>=27&&n(p.h)===0&&n(p.r)===0)pitcher+=2;
   parts.push(p.ip+" IP",n(p.so)+" K",n(p.er)+" ER");
  }
 }
 if(hitter===null&&pitcher===null)return null;
 return {row:r,role:hitter!==null&&pitcher!==null?"Two-way":pitcher!==null?"Pitching":"Batting",score:Number((n(hitter)+n(pitcher)).toFixed(2)),pitchingScore:pitcher||0,line:parts.join(" · ")};
}
function potg(rows){
 return rows.map(impact).filter(Boolean).sort((a,b)=>b.score-a.score||b.pitchingScore-a.pitchingScore||String(a.row.player_id).localeCompare(String(b.row.player_id)))[0]||null;
}
function table(headers,lines,emptyText){
 return '<div class="table-wrap"><table class="mlb-sticky"><thead><tr>'+headers.map(h=>'<th>'+esc(h)+'</th>').join("")+'</tr></thead><tbody>'
 +(lines.join("")||'<tr><td colspan="'+headers.length+'">'+esc(emptyText)+'</td></tr>')+'</tbody></table></div>';
}
function decisionPanel(g,decisions){
 const d=decisions[String(g.source_game_id)]||null;
 const found=d&&d.status==="verified";
 const values=[["WIN","Winner","winner"],["LOSS","Loser","loser"],["SAVE","Save","save"]];
 const card=([short,label,key])=>{
  const person=found?d[key]:null;
  const name=person?.name||person?.fullName;
  return '<div class="mlb-decision-card" data-decision="'+key+'"><div class="mlb-decision-type">'+short+'</div><div class="mlb-decision-role">'+label+'</div>'
   +(person?.id&&name?'<a class="mlb-decision-name" href="./player.html?id='+encode(person.id)+'">'+esc(name)+'</a>'
    :'<span class="mlb-decision-unavailable">'+(found&&key==="save"?"No save":"Not verified")+'</span>')+'</div>';
 };
 return '<section class="panel mlb-decisions-panel" id="pitchingDecisions"><div class="mlb-pregame-eyebrow">OFFICIAL MiLB GAME DECISIONS</div>'
 +'<h2>Win, Loss & Save</h2><div class="mlb-decision-grid">'+values.map(card).join("")+'</div>'
 +'<p class="mlb-note">Win, loss and save credits appear only when independently available in the official MiLB game record. They are not inferred from the final score or impact ranking.</p></section>';
}
function performancePanel(rows){
 const x=potg(rows);
 const fallback=x?x.row.name.trim().split(/\s+/).slice(0,2).map(k=>k[0]).join("").toUpperCase():"";
 const body=x?'<div class="mlb-potg-body"><div class="mlb-potg-portrait" id="potgPortrait">'+esc(fallback)+'</div>'
  +'<div class="mlb-potg-info"><div class="mlb-potg-category">'+esc(x.role)+' · '+esc(x.row.team)+'</div>'
  +'<h3><a href="'+playerUrl(x.row)+'">'+esc(x.row.name)+'</a></h3>'
  +'<div class="mlb-potg-statline">'+esc(x.line)+'</div>'
  +'<div class="mlb-potg-impact"><strong>'+x.score.toFixed(1)+'</strong><span>Impact Score</span></div>'
  +'<a class="mlb-potg-profile" href="'+playerUrl(x.row)+'">View player profile ↗</a></div></div>'
  :'<div class="empty">No verified individual box scores are currently available for this game.</div>';
 return {html:'<section class="panel mlb-potg-panel" id="playerOfGame"><div class="mlb-pregame-eyebrow">SIGNATURE PERFORMANCE</div><h2>Player of the Game</h2>'
  +body+'<p class="mlb-note">Custom, unofficial one-player impact score, calculated exclusively from players in this MiLB game. This does not represent an official league award.</p></section>',
  best:x};
}
function lineScore(g,innings){
 const data=innings[String(g.source_game_id)]||[];
 if(!data.length)return '<section class="panel" id="innings"><h2>Line score by inning</h2><div class="empty">Official inning-by-inning scoring has not been imported for this game.</div></section>';
 const row=(side,team,total)=>'<tr><td>'+esc(team)+'</td>'+data.map(i=>'<td>'+fmt(i[side])+'</td>').join("")+'<td><strong>'+fmt(total)+'</strong></td></tr>';
 return '<section class="panel" id="innings"><h2>Line score by inning</h2><div class="table-wrap"><table class="mlb-innings"><thead><tr><th>Club</th>'+data.map(i=>'<th>'+esc(i.inning)+'</th>').join("")+'<th>R</th></tr></thead><tbody>'
 +row("away",g.away_team,g.away_score)+row("home",g.home_team,g.home_score)+'</tbody></table></div></section>';
}
function boxTables(g,rows,category){
 const fields=category==="batting"?battingFields:category==="pitching"?pitchingFields:fieldingFields;
 const teamRows=(side,team)=>{
  const members=rows.filter(r=>r.side===side&&(
   category==="batting"?r.batting&&((r.batting_order!=null)||["ab","pa","h","r"].some(k=>n(r.batting[k])>0)):
   category==="pitching"?r.pitching&&recordedOuts(r.pitching.ip)!==null:
   r.fielding&&(["putOuts","assists","errors","chances","gamesStarted"].some(k=>num(r.fielding[k])!==null))
  )).slice().sort((a,b)=>{
   if(category==="pitching")return (a.pitching_appearance_index??999)-(b.pitching_appearance_index??999)||(a.player_id-b.player_id);
   const slot=r=>{
    const v=num(r.batting_order),x=v!==null?Math.floor(v/100):null;
    return x>=1&&x<=9?x:999;
   };
   const aSlot=slot(a),bSlot=slot(b);
   return aSlot-bSlot+(aSlot===bSlot?((num(a.batting_order)??999)-(num(b.batting_order)??999)):0)||String(a.name).localeCompare(String(b.name));
  });
  const numbered=category!=="fielding";
  const line=members.map(r=>{
   const orderRaw=num(r.batting_order),slot=orderRaw!==null&&orderRaw>=100&&orderRaw<1000?Math.floor(orderRaw/100):null;
   const isSub=category==="batting"&&slot!=null&&(orderRaw%100)>0;
   const order=category==="batting"?(slot==null?"—":isSub?"↳":String(slot)):
    category==="pitching"?(r.pitching_appearance_index==null?"—":String(r.pitching_appearance_index+1)):"";
   const sub=(isSub?" · entered batting slot "+slot:"");
   return '<tr class="mlb-lineup-row'+(isSub?" mlb-substitute":"")+'" data-player-id="'+esc(r.player_id)+'"'
    +(category==="batting"?' data-slot="'+esc(slot??"")+'" data-sub="'+(slot==null?0:orderRaw%100)+'"':"")
    +(category==="pitching"?' data-pitcher-index="'+esc(r.pitching_appearance_index??"")+'"':"")+'>'
    +(numbered?'<td class="mlb-order">'+esc(order)+'</td>':"")
    +'<td><a href="'+playerUrl(r)+'">'+esc(r.name||"Player #"+r.player_id)+'</a><small>'+esc(r.position||"")+esc(sub)+'</small></td>'
    +fields.map(k=>'<td>'+fmt(category==="fielding"?r.fielding?.[k]:r[category]?.[k],k)+'</td>').join("")+'</tr>';
  });
  const caption=category==="batting"?"Official batting order (↳ denotes a substitute in that lineup spot); unnumbered players have no verified batting slot":
   category==="pitching"?"Official appearance order where imported; — means order not verified":"Fielding statistics from the official MiLB box score";
  return '<section class="mlb-team-box" data-side="'+side+'" data-category="'+category+'"><div class="mlb-team-heading"><h3>'+esc(team)+'</h3><span>'+side.toUpperCase()+'</span></div><p class="mlb-team-caption">'+caption+'</p>'
   +table([...(numbered?["Order"]:[]),"Player",...fields.map(k=>labels[k]||k)],line,"No verified "+category+" entries for "+team)+ '</section>';
 };
 return teamRows("away",g.away_team)+teamRows("home",g.home_team);
}
function scoringPanel(g,plays){
 const events=plays[String(g.source_game_id)]||[];
 return '<section class="panel" id="scoringSection"><h2>Scoring plays</h2><div id="scoring">'
  +(events.length?'<div class="scoring-list">'+events.map(p=>'<div class="play"><div class="play-time">'+(p.half==="top"?"Top":"Bot")+' '+esc(p.inning??"")+'</div>'
    +'<div><div class="play-label">'+esc(p.event||"Scoring play")+'</div><div class="play-description">'+esc(p.description||"")+'</div></div></div>').join("")+'</div>'
    :'<div class="empty">Full scoring-play chronology is not available for this game yet. See the official box score and inning line.</div>')
  +'</div></section>';
}
function show(g,all,rows,innings,plays,decisions){
 const selected=rows.filter(r=>String(r.game_id)===String(g.id));
 $("gameSelect").value=g.id;
 const scoreboard='<div class="mlb-score"><div class="side">'+esc(g.away_team)+'</div>'
  +'<div class="final">'+esc(scores(g))+'</div><div class="side">'+esc(g.home_team)+'</div></div>'
  +'<p class="mlb-note">'+dt(g.date)+' · '+(g.venue_id?'<a href="../venues/venue.html?id='+encode(g.venue_id)+'">'+esc(g.venue||"Ballpark pending")+' ↗</a>':esc(g.venue||"Ballpark pending"))+' · '+esc(g.level||"MiLB")
  +' · '+(official(g)?"MiLB game #"+esc(g.source_game_id):"Awaiting official game match")+'</p>';
 const perf=performancePanel(selected);
 $("scoreboard").innerHTML=scoreboard+decisionPanel(g,decisions)+perf.html+lineScore(g,innings);
 if(perf.best){
  const best=perf.best.row,pic=$("potgPortrait"),img=new Image();
  img.alt="";img.loading="lazy";
  img.src="https://img.mlbstatic.com/mlb-photos/image/upload/w_213,q_85/v1/people/"+encode(best.player_id)+"/headshot/67/current";
  img.onload=()=>{if(pic&&img.naturalWidth>5){pic.textContent="";pic.append(img);}};
 }
 $("gameStats").innerHTML='<div class="mlb-nav-tabs" role="tablist" aria-label="Box score category">'
  +[["batting","Batting"],["pitching","Pitching"],["fielding","Fielding"]].map(([type,name],index)=>'<button type="button" role="tab" data-cat="'+type+'" aria-selected="'+(index===0)+'">'+name+'</button>').join("")+'</div>'
  +'<section class="panel"><h2 id="statTitle">Batting box score</h2><div id="box"></div></section>'
  +scoringPanel(g,plays)
  +'<p class="mlb-note">Official data: '+(official(g)?'<a target="_blank" rel="noopener" href="'+esc(g.source_url||"https://www.milb.com/gameday/"+g.source_game_id)+'">MiLB game record ↗</a>'
    :"Unmatched attendance entry. No individual statistics are invented.")+'</p>';
 function selectTab(category){
  document.querySelectorAll("#gameStats [data-cat]").forEach(btn=>btn.setAttribute("aria-selected",String(btn.dataset.cat===category)));
  $("statTitle").textContent=category[0].toUpperCase()+category.slice(1)+" box score";
  $("box").innerHTML=boxTables(g,selected,category);
 }
 document.querySelectorAll("#gameStats [data-cat]").forEach(btn=>btn.addEventListener("click",()=>selectTab(btn.dataset.cat)));
 selectTab("batting");
 document.title=g.away_team+" at "+g.home_team+" · "+g.date+" | MiLB Archive";
}
async function load(){
 const app=$("app");try{
  const get=async(name,optional=false)=>{
   const r=await fetch("./data/"+name+".json",{cache:"no-store"});
   if(!r.ok){if(optional&&r.status===404)return {};throw Error(name+" data unavailable");}
   return r.json();
  };
  const [games,rows,innings,plays,decisions]=await Promise.all([
   get("games"),get("player_stats"),get("inning_scores",true),get("scoring_plays",true),get("pitching_decisions",true)]);
  if(!Array.isArray(games)||!Array.isArray(rows))throw Error("Invalid MiLB game data");
  const ordered=games.slice().sort((a,b)=>String(b.date).localeCompare(String(a.date))||String(b.id).localeCompare(String(a.id)));
  if(!ordered.length){app.innerHTML='<div class="eyebrow">MiLB · Games & box scores</div><h1>Game details.</h1><div class="empty">No attended MiLB games have been imported yet.</div>';return;}
  const id=new URLSearchParams(location.search).get("id");
  let current=ordered.find(g=>String(g.id)===String(id))||ordered[0];
  app.innerHTML='<div class="eyebrow">MiLB · Games & box scores</div><h1>Game details.</h1>'
   +'<p class="lead">Official MiLB game results, inning scoring, batting, pitching, fielding, and scoring-play history where recorded. All player statistics belong exclusively to your attended MiLB games.</p>'
   +'<div class="toolbar"><label class="filter-label" for="gameSelect">Attended game</label><select id="gameSelect">'
   +ordered.map(g=>'<option value="'+esc(g.id)+'">'+dt(g.date)+' · '+esc(g.away_team)+' @ '+esc(g.home_team)+' · '+esc(scores(g))+'</option>').join("")+'</select></div>'
   +'<section id="scoreboard"></section><div id="gameStats"></div>';
  const run=g=>show(g,ordered,rows,innings,plays,decisions);
  $("gameSelect").addEventListener("change",()=>{
   const g=ordered.find(x=>String(x.id)===$("gameSelect").value);if(!g)return;
   history.replaceState(null,"",gameUrl(g));current=g;run(g);
  });
  run(current);
 }catch(e){app.innerHTML='<div class="empty">Unable to load MiLB game details: '+esc(e.message)+'</div>';}
}
document.addEventListener("DOMContentLoaded",load);
})();
