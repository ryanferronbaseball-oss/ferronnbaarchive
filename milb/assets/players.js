/* MiLB Players & Leaderboards: separate attendance-only statistics, MLB layout parity. */
(()=>{"use strict";
const $=id=>document.getElementById(id);
const esc=value=>String(value??"").replace(/[&<>"']/g,ch=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[ch]));
const displayNum=x=>Number(x||0).toLocaleString("en-US");
const number=v=>v===null||v===undefined||v===""?null:Number.isFinite(Number(v))?Number(v):null;
const sum=(rows,key)=>rows.reduce((n,r)=>n+(number(r[key])||0),0);
const any=(rows,key)=>rows.some(r=>number(r[key])!==null);
const sumIf=(rows,key)=>any(rows,key)?sum(rows,key):null;
const frac=(top,bottom)=>bottom>0?top/bottom:null;
const pitchOuts=v=>{
 if(v===null||v===undefined||v==="")return null;
 const m=/^(\d+)(?:\.([012]))?$/.exec(String(v).trim());
 return m?Number(m[1])*3+Number(m[2]||0):null;
};
const innings=outs=>outs==null?null:Math.floor(outs/3)+"."+(outs%3);
const rate=(top,bottom,prec=3)=>bottom>0?Number((top/bottom).toFixed(prec)):null;
const pLink=p=>'./player.html?id='+encodeURIComponent(p.id);
const bKeys=[["Games","games"],["Plate appearances","plateAppearances"],["At-bats","atBats"],["Hits","hits"],["Home runs","homeRuns"],["RBI","rbi"],["Runs","runs"],["Doubles","doubles"],["Triples","triples"],["Walks","baseOnBalls"],["Strikeouts","strikeOuts"],["Stolen bases","stolenBases"],["Average","average"],["OBP","onBasePercentage"],["SLG","sluggingPercentage"],["OPS","ops"]];
const pKeys=[["Games","games"],["Wins","wins"],["Losses","losses"],["Saves","saves"],["Outs recorded","outs"],["Strikeouts","strikeOuts"],["Innings pitched","inningsPitched"],["ERA","era"],["WHIP","whip"],["K/9","k9"],["Earned runs","earnedRuns"],["Walks","baseOnBalls"],["Hits allowed","hits"]];
const pretty=(v,key)=>{
 if(v===null||v===undefined||!Number.isFinite(Number(v)))return "—";
 if(key==="inningsPitched")return String(v);
 if(["average","onBasePercentage","sluggingPercentage","ops"].includes(key))return Number(v).toFixed(3).replace(/^0(?=\.)/,"");
 if(["era","whip","k9"].includes(key))return Number(v).toFixed(2);
 return Number(v).toLocaleString("en-US",{maximumFractionDigits:0});
};
function buildPlayers(rows){
 const index=new Map();
 for(const r of rows){
  if(r.player_id==null||!r.name||r.game_id==null)continue;
  const id=String(r.player_id);
  if(!index.has(id))index.set(id,{id,name:r.name,teams:new Set(),games:new Set(),bat:[],pit:[]});
  const p=index.get(id);
  if(r.team)p.teams.add(r.team);
  p.games.add(String(r.game_id));
  if(r.batting&&typeof r.batting==="object")p.bat.push(r);
  if(r.pitching&&typeof r.pitching==="object")p.pit.push(r);
 }
 return [...index.values()].map(p=>{
  const b=p.bat.map(r=>r.batting), pit=p.pit.map(r=>r.pitching);
  const ab=sum(b,"ab"), hits=sum(b,"h"), doubles=sum(b,"doubles"), triples=sum(b,"triples"), homers=sum(b,"hr");
  const walks=sum(b,"bb"), hbp=sum(b,"hbp"), sf=sum(b,"sf");
  const completeOBP=b.length&&b.every(r=>["ab","h","bb","hbp","sf"].every(k=>number(r[k])!==null));
  const totalBases=hits+doubles+2*triples+3*homers;
  const pa=sumIf(b,"pa");
  const outs=pit.reduce((n,r)=>n+(pitchOuts(r.ip)||0),0);
  const seenOuts=pit.some(r=>pitchOuts(r.ip)!==null);
  const er=sum(pit,"er"), bb=sum(pit,"bb"), allowed=sum(pit,"h"), strikeouts=sum(pit,"so");
  return {...p,teams:[...p.teams].sort(),gamesSeen:p.games.size,
   batting:{
    games:new Set(p.bat.map(r=>String(r.game_id))).size,plateAppearances:pa,atBats:sumIf(b,"ab"),
    hits:sumIf(b,"h"),homeRuns:sumIf(b,"hr"),rbi:sumIf(b,"rbi"),runs:sumIf(b,"r"),
    doubles:sumIf(b,"doubles"),triples:sumIf(b,"triples"),baseOnBalls:sumIf(b,"bb"),
    strikeOuts:sumIf(b,"so"),stolenBases:sumIf(b,"sb"),
    average:b.length&&any(b,"ab")?rate(hits,ab):null,
    onBasePercentage:completeOBP?rate(hits+walks+hbp,ab+walks+hbp+sf):null,
    sluggingPercentage:b.length&&["h","doubles","triples","hr"].every(k=>any(b,k))?rate(totalBases,ab):null,
    ops:completeOBP&&ab>0&&["h","doubles","triples","hr"].every(k=>any(b,k))?Number(((hits+walks+hbp)/(ab+walks+hbp+sf)+totalBases/ab).toFixed(3)):null
   },
   pitching:{
    games:new Set(p.pit.map(r=>String(r.game_id))).size,outs:seenOuts?outs:null,
    strikeOuts:sumIf(pit,"so"),inningsPitched:seenOuts?innings(outs):null,
    era:seenOuts&&any(pit,"er")?rate(er*27,outs,2):null,
    whip:seenOuts&&any(pit,"h")&&any(pit,"bb")?rate((allowed+bb)*3,outs,2):null,
    k9:seenOuts&&any(pit,"so")?rate(strikeouts*27,outs,2):null,
    wins:sumIf(pit,"w"),losses:sumIf(pit,"l"),saves:sumIf(pit,"sv"),
    earnedRuns:sumIf(pit,"er"),baseOnBalls:sumIf(pit,"bb"),hits:sumIf(pit,"h")
   }
  };
 });
}
function leaderboard(players,category,key,limit,search){
 const source=players.filter(p=>(category==="batting"?p.bat.length:p.pit.length)>0)
  .filter(p=>!search||p.name.toLowerCase().includes(search)||(p.teams.join(" ")).toLowerCase().includes(search));
 const valid=source.filter(p=>{
  const v=p[category][key];
  return v!==null&&v!==undefined&&(key==="inningsPitched"?(p.pitching.outs||0)>0:Number(v)>0);
 });
 const asc=key==="era"||key==="whip";
 valid.sort((a,b)=>{
  const na=key==="inningsPitched"?a.pitching.outs:Number(a[category][key]);
  const nb=key==="inningsPitched"?b.pitching.outs:Number(b[category][key]);
  return (asc?na-nb:nb-na)||a.name.localeCompare(b.name);
 });
 const shown=valid.slice(0,limit);
 const header='<thead><tr><th>Rank</th><th>Player</th><th>Club(s)</th><th>Games</th><th>'+(category==="batting"?"H":"SO")+'</th><th>'+(category==="batting"?"HR":"IP")+'</th><th>'+esc((category==="batting"?bKeys:pKeys).find(x=>x[1]===key)?.[0]||key)+'</th></tr></thead>';
 const body=shown.map((p,i)=>{
  const s=p[category];
  return '<tr><td>'+(i+1)+'</td><td><a href="'+pLink(p)+'">'+esc(p.name)+'</a></td><td>'+esc(p.teams.join(", "))+'</td><td>'+displayNum(s.games)+'</td><td>'+pretty(s[category==="batting"?"hits":"strikeOuts"],"")+'</td><td>'+pretty(s[category==="batting"?"homeRuns":"inningsPitched"],category==="batting"?"":"inningsPitched")+'</td><td><strong>'+pretty(s[key],key)+'</strong></td></tr>';
 }).join("");
 return '<p class="mlb-note" aria-live="polite">Showing '+shown.length+' of '+valid.length+' qualifying '+(category==="batting"?"batters":"pitchers")+'.</p><div class="table-wrap"><table>'+header+'<tbody>'+body+'</tbody></table></div>'+(shown.length?"":'<div class="empty">No verified MiLB player statistics currently qualify for this selection.</div>');
}
function playerSearchResults(players,query){
 if(!query)return '<p class="mlb-note">Search by player name or club to open any MiLB player profile, even if the player does not qualify for the current leaderboard.</p>';
 const matches=players.filter(p=>p.name.toLowerCase().includes(query)||p.teams.join(" ").toLowerCase().includes(query))
  .sort((a,b)=>a.name.localeCompare(b.name));
 const shown=matches.slice(0,25);
 return '<p class="mlb-note" role="status">'+matches.length+' matching player'+(matches.length===1?'':'s')+(matches.length>25?' · showing first 25':'')+'</p>'+
  (matches.length?'<div class="milb-search-results">'+shown.map(p=>'<a href="'+pLink(p)+'"><strong>'+esc(p.name)+'</strong><span>'+esc(p.teams.join(', '))+' · '+displayNum(p.gamesSeen)+' attended game'+(p.gamesSeen===1?'':'s')+'</span></a>').join('')+'</div>':'<p class="empty">No matching MiLB player. Try another name or club.</p>');
}
async function main(){
 const app=$("app");
 try{
  const [gRes,rRes]=await Promise.all([fetch("./data/games.json",{cache:"no-store"}),fetch("./data/player_stats.json",{cache:"no-store"})]);
  if(!gRes.ok||!rRes.ok)throw Error("MiLB games or player statistics unavailable");
  const [games,rows]=await Promise.all([gRes.json(),rRes.json()]);
  if(!Array.isArray(games)||!Array.isArray(rows))throw Error("Invalid MiLB data shape");
  const players=buildPlayers(rows);
  const gameIds=new Set(rows.map(r=>String(r.game_id)));
  const verified=games.filter(g=>g.box_score_status==="verified"&&g.source_game_id!=null&&gameIds.has(String(g.id)));
  const batters=players.filter(p=>p.bat.length>0),pitchers=players.filter(p=>p.pit.length>0);
  app.innerHTML='<div class="eyebrow">MiLB · Player statistics</div><h1>Players & leaderboards.</h1><p class="intro">Find the minor-league players you have watched, with statistics aggregated only from MiLB games you personally attended. MLB and college baseball totals are never combined here.</p>'+
   '<div class="metrics">'+[["Unique MiLB players",players.length],["Matched games",verified.length],["Batter records",batters.length],["Pitcher records",pitchers.length]].map(x=>'<div class="metric"><strong>'+displayNum(x[1])+'</strong><small>'+esc(x[0])+'</small></div>').join("")+'</div>'+
   '<section class="milb-player-search" role="search" aria-label="Find a MiLB player"><label for="query">Search all MiLB players</label><input id="query" type="search" autocomplete="off" placeholder="Type a player name or club…" aria-controls="playerResults"><div id="playerResults" aria-live="polite"></div></section>'+
   '<div class="mlb-filters"><label for="category">Statistical group<select id="category"><option value="batting">Batting</option><option value="pitching">Pitching</option></select></label><label for="stat">Leaderboard statistic<select id="stat"></select></label><label for="limit">Show<select id="limit"><option>25</option><option>50</option><option>100</option><option>1000</option></select></label></div>'+
   '<section class="panel"><h2 id="boardHeading"></h2><p class="mlb-note">Aggregate counting statistics include only imported attended MiLB games. Rate statistics are recomputed from the underlying MiLB totals. W/L/S totals are official pitching decisions from only the MiLB games you attended; they exclude full-season or MLB statistics.</p><div id="board"></div></section>';
  const category=$("category"),stat=$("stat");
  const draw=()=>{
   const key=stat.value,cat=category.value;
   const query=$("query").value.trim().toLowerCase();
   const label=(cat==="batting"?bKeys:pKeys).find(x=>x[1]===key)?.[0]||key;
   $("boardHeading").textContent=label+" · "+(cat==="batting"?"Batting":"Pitching");
   $("board").innerHTML=leaderboard(players,cat,key,Number($("limit").value),query);
   $("playerResults").innerHTML=playerSearchResults(players,query);
  };
  const change=()=>{
   stat.innerHTML=(category.value==="batting"?bKeys:pKeys).map(([label,key])=>'<option value="'+key+'">'+esc(label)+'</option>').join("");
   stat.value=category.value==="batting"?"hits":"strikeOuts";
   draw();
  };
  category.addEventListener("change",change);
  ["stat","query","limit"].forEach(id=>$(id).addEventListener("input",draw));
  change();
 }catch(error){
  app.innerHTML='<div class="empty">Unable to load MiLB leaderboards: '+esc(error.message)+'</div>';
 }
}
document.addEventListener("DOMContentLoaded",main);
})();
