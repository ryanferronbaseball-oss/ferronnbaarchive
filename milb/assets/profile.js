/* MiLB player profiles, MLB visual parity. MiLB data is independently sourced. */
(()=>{"use strict";
const $=id=>document.getElementById(id);
const esc=v=>String(v??"").replace(/[&<>"']/g,c=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[c]));
const number=v=>v===null||v===undefined||v===""?null:Number.isFinite(Number(v))?Number(v):null;
const n=v=>number(v)??0;
const sum=(rows,key)=>rows.reduce((a,r)=>a+n(r[key]),0);
const complete=(rows,keys)=>rows.length>0&&rows.every(r=>keys.every(k=>number(r[k])!==null));
const count=(rows,key)=>complete(rows,[key])?sum(rows,key):null;
const dt=v=>v?new Date(String(v)+"T12:00:00").toLocaleDateString("en-US",{month:"short",day:"numeric",year:"numeric"}):"—";
const outOf=ip=>{const m=/^(\d+)(?:\.([012]))?$/.exec(String(ip??""));return m?Number(m[1])*3+Number(m[2]||0):null;};
const ipOf=outs=>outs===null?"—":Math.floor(outs/3)+"."+(outs%3);
const ratio=(a,b,places=3)=>b>0?Number((a/b).toFixed(places)):null;
const decimal=(v,d=3)=>v===null?"—":Number(v).toFixed(d).replace(d===3?/^0(?=\.)/:/^$a/,"");
const value=v=>v===null||v===undefined||v===""?"—":String(v);
const fmt=v=>v===null?"—":Number(v).toLocaleString("en-US");
const urlId=id=>encodeURIComponent(String(id));
const statBoxes=items=>items.map(([key,val])=>'<div class="mlb-profile-stat"><small>'+esc(key)+'</small><strong>'+esc(value(val))+'</strong></div>').join("");
const totals=(items,klass="")=>'<div class="mlb-profile-total-grid '+klass+'">'+items.map(([k,v])=>'<div class="mlb-profile-total"><small>'+esc(k)+'</small><strong>'+esc(value(v))+'</strong></div>').join("")+'</div>';
const gameUrl=id=>'./game.html?id='+urlId(id);
const badge=(text,href)=>'<a class="milb-crossover-badge" href="'+href+'">'+text+' ↗</a>';
function battingStats(rows){
 const data=rows.map(r=>r.batting).filter(Boolean);
 const ab=count(data,"ab"), hits=count(data,"h"), bb=count(data,"bb"),
  doubles=count(data,"doubles"), triples=count(data,"triples"),hr=count(data,"hr"),
  hbp=count(data,"hbp"),sf=count(data,"sf");
 const base=hits!==null&&doubles!==null&&triples!==null&&hr!==null?hits+doubles+2*triples+3*hr:null;
 const obp=ab!==null&&hits!==null&&bb!==null&&hbp!==null&&sf!==null?ratio(hits+bb+hbp,ab+bb+hbp+sf):null;
 const avg=ab!==null&&hits!==null?ratio(hits,ab):null;
 const slg=ab!==null&&base!==null?ratio(base,ab):null;
 return {data,games:new Set(rows.filter(r=>r.batting).map(r=>String(r.game_id))).size,
  ab,hits,bb,doubles,triples,hr,hbp,sf,
  pa:count(data,"pa"),r:count(data,"r"),rbi:count(data,"rbi"),so:count(data,"so"),
  sb:count(data,"sb"),cs:count(data,"cs"),avg,obp,slg,
  ops:obp!==null&&slg!==null?Number((obp+slg).toFixed(3)):null};
}
function pitchingStats(rows){
 const data=rows.map(r=>r.pitching).filter(Boolean);
 const validOuts=data.length>0&&data.every(r=>outOf(r.ip)!==null);
 const outs=validOuts?data.reduce((a,r)=>a+outOf(r.ip),0):null;
 const h=count(data,"h"),er=count(data,"er"),bb=count(data,"bb"),so=count(data,"so"),
  hr=count(data,"hr"),bf=count(data,"bf"),hbp=count(data,"hbp"),
  wins=count(data,"w"),losses=count(data,"l"),saves=count(data,"sv");
 return {data,games:new Set(rows.filter(r=>r.pitching).map(r=>String(r.game_id))).size,outs,
  ip:ipOf(outs),h,er,bb,so,hr,bf,hbp,wins,losses,saves,
  era:outs!==null&&er!==null?ratio(er*27,outs,2):null,
  whip:outs!==null&&h!==null&&bb!==null?ratio((h+bb)*3,outs,2):null,
  k9:outs!==null&&so!==null?ratio(so*27,outs,2):null};
}
function impact(row){
 const b=row.batting,p=row.pitching;let hitter=null,pitcher=null,parts=[];
 if(b){
  const hits=n(b.h),dbl=n(b.doubles),tri=n(b.triples),hr=n(b.hr);
  const singles=Math.max(0,hits-dbl-tri-hr);
  hitter=singles+2*dbl+3*tri+4*hr+0.9*n(b.rbi)+0.7*n(b.r)+0.7*(n(b.bb)+n(b.hbp))+1.1*n(b.sb)-0.8*n(b.cs)-0.15*n(b.so);
  if(number(b.ab)!==null)parts.push(hits+"-for-"+b.ab);
  if(hr)parts.push(hr+" HR");if(n(b.rbi))parts.push(b.rbi+" RBI");
  if(n(b.sb))parts.push(b.sb+" SB");
 }
 if(p){
  const outs=outOf(p.ip);
  if(outs!==null){
   pitcher=1.5*outs/3+0.65*n(p.so)-1.8*n(p.er)-0.35*n(p.h)-0.35*n(p.bb)-0.5*n(p.hr)-0.2*n(p.hbp);
   if(outs>=27&&n(p.h)===0&&n(p.r)===0)pitcher+=2;
   parts.push(p.ip+" IP",n(p.so)+" K",n(p.er)+" ER");
  }
 }
 if(hitter===null&&pitcher===null)return null;
 return {score:Number((n(hitter)+n(pitcher)).toFixed(1)),battingScore:hitter,pitchingScore:pitcher,row,line:parts.join(" · ")};
}
function tabTable(rows,kind,gamesById){
 const keys=kind==="batting"?[["AB","ab"],["R","r"],["H","h"],["2B","doubles"],["3B","triples"],["HR","hr"],["RBI","rbi"],["BB","bb"],["SO","so"],["SB","sb"]]:[["IP","ip"],["H","h"],["ER","er"],["BB","bb"],["SO","so"],["HR","hr"],["W","w"],["L","l"],["SV","sv"],["BF","bf"]];
 const relevant=rows.filter(r=>r[kind]).slice().sort((a,b)=>String(b.date).localeCompare(String(a.date))||String(a.game_id).localeCompare(String(b.game_id)));
 if(!relevant.length)return '<div class="empty">No verified '+kind+' appearances in attended MiLB games.</div>';
 return '<div class="table-wrap"><table class="mlb-profile-game-table"><thead><tr><th>Date</th><th>Team</th><th>Match</th>'+keys.map(x=>'<th>'+x[0]+'</th>').join("")+'</tr></thead><tbody>'
 +relevant.map(r=>{const g=gamesById.get(String(r.game_id)),v=r[kind];return '<tr><td><a href="'+gameUrl(r.game_id)+'">'+dt(r.date)+'</a></td><td>'+esc(r.team||"—")+'</td><td>'+esc(g?g.away_team+" @ "+g.home_team:"—")+'</td>'+keys.map(([,key])=>'<td>'+esc(value(v[key]))+'</td>').join("")+'</tr>';}).join("")+'</tbody></table></div>';
}
function renderProfile(playerId,rows,games,links,collegeLinks){
 const entries=rows.filter(r=>String(r.player_id)===String(playerId));
 if(!entries.length){$("app").innerHTML='<div class="eyebrow">MiLB · Player profile</div><h1>Player not found.</h1><p><a href="./stats.html">← Player leaderboards</a></p>';return;}
 const name=entries.find(r=>r.name)?.name||"Unknown player";
 const byGame=new Map(games.map(g=>[String(g.id),g]));
 const gamesSeen=[...new Set(entries.map(r=>String(r.game_id)))].map(id=>byGame.get(id)).filter(Boolean).sort((a,b)=>a.date.localeCompare(b.date));
 const teams=[...new Set(entries.map(r=>r.team).filter(Boolean))];
 const positions=[...new Set(entries.map(r=>r.position).filter(Boolean))];
 const batting=battingStats(entries),pitching=pitchingStats(entries);
 const hasB=batting.data.length>0,hasP=pitching.data.length>0;
 const realTwoWay=hasP&&hasB&&batting.ab!==null&&batting.ab>0&&positions.some(v=>v!=="P");
 const rolePitcher=hasP&&(!hasB||batting.ab===null||batting.ab===0);
 const years=[...new Set(gamesSeen.map(g=>g.date.slice(0,4)))].sort();
 const span=years.length?(years[0]===years[years.length-1]?years[0]:years[0]+"–"+years[years.length-1]):"—";
 const initials=name.trim().split(/\s+/).map(s=>s.charAt(0)).slice(0,2).join("").toUpperCase();
 const linked=links.find(x=>String(x.milb_id)===String(playerId)&&x.verified===true&&x.mlb_debut);
 const collegeLink=collegeLinks.find(x=>String(x.milb_id)===String(playerId)&&x.verified===true&&x.college_player_id);
 const tripleLevel=Boolean(linked&&linked.mlb_seen===true&&collegeLink);
 const tags=[
  ...(tripleLevel?[badge("★ SEEN IN COLLEGE + MiLB + MLB","../college-baseball/player.html?id="+urlId(collegeLink.college_player_id))]:[]),
  ...(linked?[badge("★ REACHED MLB","https://www.mlb.com/player/"+urlId(linked.mlb_id))]:[]),
  ...(linked&&linked.mlb_seen===true?[badge("★ SEEN IN MiLB + MLB","../mlb/player.html?id="+urlId(linked.mlb_id))]:[]),
  ...(collegeLink?[badge("★ SEEN IN COLLEGE + MiLB","../college-baseball/player.html?id="+urlId(collegeLink.college_player_id))]:[])
 ];
 const linksHtml=tags.length?'<div class="mlb-profile-achievements" aria-label="Verified baseball pathways">'+tags.join("")+'</div>':"";
 const impacts=entries.map(impact).filter(Boolean).sort((a,b)=>b.score-a.score);
 const best=impacts[0];
 const bestB=impacts.filter(x=>x.battingScore!==null).sort((a,b)=>b.battingScore-a.battingScore)[0];
 const performance=best?'<div class="mlb-profile-signature"><small>BEST WITNESSED PERFORMANCE</small><strong>'+best.score.toFixed(1)+' Impact Score</strong><span>'+esc(best.line)+' · '+dt(best.row.date)+'</span><a href="'+gameUrl(best.row.game_id)+'">View game ↗</a></div>':"";
 const cardB=[["Games",gamesSeen.length],["Batting Average",decimal(batting.avg)],["Home Runs",batting.hr],["RBI",batting.rbi],["OPS",decimal(batting.ops)],["Best Performance",bestB?bestB.battingScore.toFixed(1):"—"]];
 const cardP=[["Games",pitching.games],["W–L",pitching.wins===null||pitching.losses===null?"—":pitching.wins+"–"+pitching.losses],["Saves",pitching.saves],["Innings",pitching.ip],["Strikeouts",pitching.so],["ERA",decimal(pitching.era,2)]];
 const groups=role=>
  '<div class="mlb-profile-role-group" data-role="'+role+'"><div class="mlb-profile-role-label">'+role.toUpperCase()+'</div><div class="mlb-profile-stat-grid">'+statBoxes(role==="batting"?cardB:cardP)+'</div></div>';
 const headline=realTwoWay?'<div class="mlb-profile-two-way">'+groups("batting")+groups("pitching")+'</div>':statBoxes(rolePitcher?cardP:cardB);
 const battingItems=[["Games",batting.games],["Plate Appearances",batting.pa],["At-bats",batting.ab],["Hits",batting.hits],["Doubles",batting.doubles],["Triples",batting.triples],["Home Runs",batting.hr],["RBI",batting.rbi],["Runs",batting.r],["Walks",batting.bb],["Stolen Bases",batting.sb]];
 const pitchingItems=[["Games",pitching.games],["Wins",pitching.wins],["Losses",pitching.losses],["Saves",pitching.saves],["Innings",pitching.ip],["Hits",pitching.h],["Earned Runs",pitching.er],["Walks",pitching.bb],["Strikeouts",pitching.so],["Home Runs",pitching.hr],["Batters Faced",pitching.bf]];
 const rateBat=[["Batting Average",decimal(batting.avg)],["On-Base Percentage",decimal(batting.obp)],["Slugging Percentage",decimal(batting.slg)],["OPS",decimal(batting.ops)],["Extra-Base Hits",batting.doubles===null||batting.triples===null||batting.hr===null?null:batting.doubles+batting.triples+batting.hr],["Isolated Power",batting.slg===null||batting.avg===null?null:decimal(batting.slg-batting.avg)],["Walk Rate",batting.bb===null||batting.pa===null||!batting.pa?null:(100*batting.bb/batting.pa).toFixed(1)+"%"],["Strikeout Rate",batting.so===null||!batting.pa?null:(100*batting.so/batting.pa).toFixed(1)+"%"]];
 const kbb=pitching.bb>0&&pitching.so!==null?ratio(pitching.so,pitching.bb,2):null;
 const kPct=pitching.bf>0&&pitching.so!==null?(100*pitching.so/pitching.bf).toFixed(1)+"%":null;
 const bbPct=pitching.bf>0&&pitching.bb!==null?(100*pitching.bb/pitching.bf).toFixed(1)+"%":null;
 const fip=pitching.outs>0&&pitching.hr!==null&&pitching.bb!==null&&pitching.hbp!==null&&pitching.so!==null?
  Number(((13*pitching.hr+3*(pitching.bb+pitching.hbp)-2*pitching.so)*3/pitching.outs+3.2).toFixed(2)):null;
 const ratePitch=[["ERA",decimal(pitching.era,2)],["Estimated FIP",decimal(fip,2)],["WHIP",decimal(pitching.whip,2)],["K/BB",decimal(kbb,2)],["K%",kPct],["BB%",bbPct]];
 const runs=entries.map(r=>r.batting||{}),pitches=entries.map(r=>r.pitching||{});
 const milestones=[
  ["3+ hit games",entries.filter(r=>number(r.batting?.h)>=3).length],
  ["Multi-HR games",entries.filter(r=>number(r.batting?.hr)>=2).length],
  ["3+ RBI games",entries.filter(r=>number(r.batting?.rbi)>=3).length],
  ["2+ stolen-base games",entries.filter(r=>number(r.batting?.sb)>=2).length],
  ["10+ strikeout outings",entries.filter(r=>number(r.pitching?.so)>=10).length],
  ["7+ inning outings",entries.filter(r=>(outOf(r.pitching?.ip)??-1)>=21).length],
  ["Scoreless 5+ IP",entries.filter(r=>(outOf(r.pitching?.ip)??-1)>=15&&number(r.pitching?.er)===0).length]
 ];
 $("app").innerHTML='<p class="mlb-player-back"><a href="./stats.html">← Player leaderboards</a></p>'
  +'<section class="mlb-profile-hero mlb-profile-head">'
  +'<div class="mlb-profile-photo" id="playerPortrait">'+esc(initials)+'</div>'
  +'<div class="mlb-profile-identity"><div class="mlb-profile-team-name">'+esc(teams.join(" / "))+'</div><h1>'+esc(name)+'</h1>'+linksHtml
  +'<p class="mlb-profile-seen">'+gamesSeen.length+' attended '+(gamesSeen.length===1?"game":"games")+' · '+esc(span)
  +(positions.length?" · "+esc(positions.join(" / ")):"")+'</p></div></section>'
  +'<div class="mlb-profile-headline-stats'+(realTwoWay?" is-two-way":"")+'">'+headline+'</div>'
  +'<div class="mlb-profile-tabs" id="profileTabs" role="tablist" aria-label="Player profile sections">'
  +[["overview","Overview"],["advanced","Advanced"],["games","Game Log"],["milestones","Milestones"]].map(([key,title],i)=>'<button type="button" class="mlb-profile-tab" role="tab" data-profile-tab="'+key+'" aria-controls="profile-'+key+'" aria-selected="'+(i===0)+'">'+title+'</button>').join("")+'</div>'
  +'<section class="panel mlb-profile-panel" id="profile-overview" role="tabpanel"><h2>Player overview</h2>'+performance
  +(rolePitcher&&hasP?'<h3>Pitching statistics from games you attended</h3>'+totals(pitchingItems,"mlb-profile-pitching-grid"):"")
  +(hasB?'<h3>Batting statistics from games you attended</h3>'+totals(battingItems):"")
  +(!rolePitcher&&hasP?'<h3>Pitching statistics from games you attended</h3>'+totals(pitchingItems,"mlb-profile-pitching-grid"):"")
  +'<p class="mlb-note">All totals come exclusively from the MiLB games you attended. MLB and college baseball lines never contribute to these statistics. Win, loss, and save totals are credited only from verified attended MiLB games, not from career or MLB statistics. Official career awards are not included.</p></section>'
  +'<section class="panel mlb-profile-panel" id="profile-advanced" role="tabpanel" hidden><h2>Advanced statistics</h2><p class="mlb-note">Rate statistics are recomputed from complete available MiLB box-score fields; a dash means data needed for the calculation is missing.</p>'
  +(hasB?'<h3>Batting efficiency</h3>'+totals(rateBat):"")
  +(hasP?'<h3>Pitching efficiency</h3>'+totals(ratePitch,"mlb-profile-pitching-advanced-grid")+'<p class="mlb-note">Estimated FIP uses a fixed 3.20 constant; actual FIP uses a league- and season-specific constant. Only the innings you witnessed are counted.</p>':"")+'</section>'
  +'<section class="panel mlb-profile-panel" id="profile-games" role="tabpanel" hidden><h2>Every game you witnessed</h2><div class="mlb-profile-log-tabs" role="tablist" aria-label="Game log stat group"><button type="button" role="tab" data-side="batting" aria-selected="'+(!rolePitcher)+'">Batting</button><button type="button" role="tab" data-side="pitching" aria-selected="'+rolePitcher+'">Pitching</button></div><div id="logs"></div></section>'
  +'<section class="panel mlb-profile-panel" id="profile-milestones" role="tabpanel" hidden><h2>Milestones you witnessed</h2>'+totals(milestones)
  +'<p class="mlb-note">These are single-game statistics from your attended MiLB games, not full-career accomplishments. <a href="./records.html">Explore MiLB records ↗</a></p></section>';
 function showTab(key){
  document.querySelectorAll("#profileTabs [data-profile-tab]").forEach(b=>b.setAttribute("aria-selected",String(b.dataset.profileTab===key)));
  document.querySelectorAll(".mlb-profile-panel").forEach(panel=>panel.hidden=panel.id!=="profile-"+key);
 }
 document.querySelectorAll("#profileTabs [data-profile-tab]").forEach(b=>b.addEventListener("click",()=>showTab(b.dataset.profileTab)));
 function logs(kind){
  document.querySelectorAll("[data-side]").forEach(b=>b.setAttribute("aria-selected",String(b.dataset.side===kind)));
  $("logs").innerHTML=tabTable(entries,kind,byGame);
 }
 document.querySelectorAll("[data-side]").forEach(b=>b.addEventListener("click",()=>logs(b.dataset.side)));
 logs(rolePitcher?"pitching":"batting");
 const portrait=$("playerPortrait");
 const image=new Image();image.alt="";image.loading="eager";
 image.src="https://img.mlbstatic.com/mlb-photos/image/upload/w_213,q_85/v1/people/"+urlId(playerId)+"/headshot/67/current";
 image.onload=()=>{if(image.naturalWidth>5){portrait.textContent="";portrait.append(image);}};
 document.title=name+" | MiLB Courtside Archive";
}
async function load(){
 try{
  const id=new URLSearchParams(location.search).get("id");
  if(!id){$("app").innerHTML='<div class="eyebrow">MiLB · Player profile</div><h1>Choose a player.</h1><p><a href="./stats.html">← Player leaderboards</a></p>';return;}
  const [r,g,l,c]=await Promise.all(["player_stats","games","player_links","college_links"].map(name=>fetch("./data/"+name+".json",{cache:"no-store"}).then(async res=>{if(!res.ok)throw Error(name+" unavailable");return res.json();})));
  if(!Array.isArray(r)||!Array.isArray(g)||!Array.isArray(l)||!Array.isArray(c))throw Error("Unexpected MiLB data");
  renderProfile(id,r,g,l,c);
 }catch(e){$("app").innerHTML='<div class="empty">Unable to load MiLB player profile: '+esc(e.message)+'</div>';}
}
document.addEventListener("DOMContentLoaded",load);
})();
