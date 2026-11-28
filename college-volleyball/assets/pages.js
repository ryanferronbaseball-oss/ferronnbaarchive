document.addEventListener("DOMContentLoaded",async function app(){
 const $=id=>document.getElementById(id),out=$("app"),mode=document.body.dataset.page;
 const e=x=>String(x??"—").replace(/[&<>"']/g,c=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[c]));
 const a=(u,t)=>`<a href="${e(u)}">${e(t)}</a>`;
 const gl=g=>"./game.html?id="+encodeURIComponent(g.id),pl=p=>"./player.html?id="+encodeURIComponent(p.id);
 const tr=c=>"<tr>"+c.map(x=>"<td>"+x+"</td>").join("")+"</tr>";
 const table=(h,r)=>'<div class="table-wrap"><table class="soccer-stat-table vb-table"><thead><tr>'+h.map(x=>"<th>"+e(x)+"</th>").join("")+"</tr></thead><tbody>"+r.join("")+"</tbody></table></div>";
 const panel=(h,b)=>'<section class="soccer-panel"><h2>'+e(h)+"</h2>"+b+"</section>";
 const hero=(h,b)=>'<div class="eyebrow">NCAA · Women’s college volleyball</div><h1>'+e(h)+'</h1><p class="lead">'+e(b)+"</p>";
 const metric=r=>'<section class="metrics">'+r.map(([k,v])=>'<div class="metric"><strong>'+e(v)+"</strong><small>"+e(k)+"</small></div>").join("")+"</section>";
 const hit=p=>p.ta?((p.k-p.e)/p.ta).toFixed(3).replace(/^(-?)0\./,"$1."):"—";
 const heads=["Player","SP","K","E","TA","HIT%","AST","SA","SE","DIG","BS","BA","BE","BHE","RE","PTS"];
 const cells=p=>[p.sp,p.k,p.e,p.ta,hit(p),p.ast,p.sa,p.se,p.dig,p.bs,p.ba,p.be,p.bhe,p.re,p.pts].map(e);
 const team=(g,s)=>(g[s+"_rank"]?"#"+g[s+"_rank"]+" ":"")+g[s];
 const load=async f=>{const r=await fetch("./data/"+f);if(!r.ok)throw Error(f);return r.json()};
 try{
 const [games,rows,portraits]=await Promise.all([load("matches.json"),load("player_boxscores.json"),load("player_portraits.json").catch(()=>({}))]);
 const portrait=p=>{const initials=e(p.player.split(" ").map(s=>s[0]).slice(0,2).join(""));const r=portraits[p.id];return r?.provider==="official"&&(/^[.]\/assets\/portraits\/(texas|sdsu|nebraska|byu)\/[a-z0-9-]+\.jpg$/.test(r.url||"")||/^https:\/\/[^\s"'<>]+$/.test(r.url||""))?'<img src="'+e(r.url)+'" alt="'+e(p.player)+'" onload="this.classList.add(\'is-loaded\')" onerror="this.remove()"><span>'+initials+'</span>':initials;};
 const photoCredit=p=>{const r=portraits[p.id];return r?.provider==="official"&&/^https:\/\/[^\s"'<>]+$/.test(r.source||"")?'<small class="archive-photo-credit"><a href="'+e(r.source)+'" target="_blank" rel="noopener noreferrer">Photo source ↗</a></small>':"";};
 games.sort((a,b)=>a.date.localeCompare(b.date));
 const byGame=new Map(games.map(g=>[g.id,g])),groups=new Map();
 for(const r of rows){if(!groups.has(r.id))groups.set(r.id,[]);groups.get(r.id).push(r);}
 function agg(rs){const p={id:rs[0].id,player:rs[0].player,teams:[...new Set(rs.map(r=>r.team))],matches:rs.length,logs:rs};for(const k of ["sp","k","e","ta","ast","sa","se","bs","ba","be","dig","bhe","re","pts"])p[k]=rs.reduce((n,r)=>n+r[k],0);p.blocks=p.bs+p.ba;p.hit=p.ta?(p.k-p.e)/p.ta:null;for(const k of ["k","ast","dig","blocks","sa","pts"])p[k+"ps"]=p[k]/p.sp;return p;}
 const players=[...groups.values()].map(agg),defs=[["Kills","k"],["Assists","ast"],["Digs","dig"],["Blocks","blocks"],["Aces","sa"],["Points","pts"]];
 const rank=(rs,k)=>rs.map(p=>({...p,blocks:p.bs+p.ba})).sort((a,b)=>b[k]-a[k]||a.player.localeCompare(b.player));
 const features=rs=>'<div class="soccer-grid">'+defs.map(([l,k])=>{const p=rank(rs,k)[0];return '<article class="soccer-tile"><small>'+l+"</small><h3>"+p[k]+"</h3>"+a(pl(p),p.player)+"<p>"+e(p.team)+"</p>"+a(gl(byGame.get(p.game_id)),"Match ↗")+"</article>";}).join("")+"</div>";
 const history=()=>table(["Date","Away","Home","Sets","Match"],games.slice().reverse().map(g=>tr([e(g.date),e(team(g,"away")),e(team(g,"home")),g.away_score+"–"+g.home_score,a(gl(g),"Box score ↗")])));
 const cards=()=>'<div class="game-grid">'+games.slice().reverse().map(g=>'<article class="game-card"><div class="eyebrow">'+e(g.date)+"</div><h3>"+e(team(g,"away"))+" "+g.away_score+"–"+g.home_score+" "+e(team(g,"home"))+"</h3><p>"+e(g.venue)+"</p>"+a(gl(g),"Match box score ↗")+"</article>").join("")+"</div>";
 const id=decodeURIComponent((location.search.match(/[?&]id=([^&]+)/)||[])[1]||"");
 if(mode==="index"){out.innerHTML=hero("Your volleyball history.","Official match results, box scores and witnessed player performances.")+metric([["Matches",games.length],["Sets witnessed",games.reduce((n,g)=>n+g.away_sets.length,0)],["Players",players.length],["Programs",new Set(games.flatMap(g=>[g.home,g.away])).size]])+panel("Recent matches",cards())+panel("Signature performances",features(rows))+panel("Match history",history());return;}
 if(mode==="game"){
 if(!id){out.innerHTML=hero("Match history.","All attended matches.")+cards()+history();return;}
 const g=byGame.get(id);if(!g)throw Error("Match not found");
 const rs=rows.filter(p=>p.game_id===g.id);
 const ids={"Texas":"251","San Diego":"301","Nebraska":"158","BYU":"252","San Diego State":"21"};
 const logo=s=>`<img class="vb-logo" src="https://a.espncdn.com/i/teamlogos/ncaa/500/${ids[g[s]]}.png" alt="" onerror="this.hidden=true">`;
 const score='<section class="soccer-panel vb-score"><div class="eyebrow">'+e(g.date+" · "+g.venue)+'</div><div class="vb-score-row"><div>'+logo("away")+"<h3>"+e(team(g,"away"))+"</h3><strong>"+g.away_score+"</strong></div><small>FINAL<br>SETS</small><div>"+logo("home")+"<h3>"+e(team(g,"home"))+"</h3><strong>"+g.home_score+"</strong></div></div><p>"+e(g.attendance)+" announced attendance · "+a(g.source_url,"Official box score ↗")+"</p></section>";
 const setRows=["away","home"].map(s=>tr([e(team(g,s)),...g[s+"_sets"].map((v,i)=>v>g[(s==="away"?"home":"away")+"_sets"][i]?'<strong class="vb-win">'+v+"</strong>":v),"<strong>"+g[s+"_score"]+"</strong>"]));
 const ts=[["Kills","k"],["Errors","e"],["Attempts","ta"],["Hitting %","hit"],["Assists","ast"],["Aces","sa"],["Service errors","se"],["Digs","dig"],["Team blocks","blocks"],["Points","pts"]];
 const comparison=table(["Statistic",g.away,g.home],ts.map(([l,k])=>tr([l,...["away","home"].map(s=>k==="hit"?hit(g.team_totals[s]):g.team_totals[s][k])])));
 const box=s=>panel(g[s]+" · Player box score",table(heads,[...rs.filter(p=>p.team===g[s]).map(p=>tr([a(pl(p),p.player),...cells(p)])),tr(["<strong>Official team total</strong>",...cells({...g.team_totals[s],sp:"—"})])]));
 const k=rank(rs,"k")[0],ast=rank(rs,"ast")[0],dig=rank(rs,"dig")[0];
 const recap="<p>"+e(g.home_score>g.away_score?g.home:g.away)+" won "+Math.max(g.away_score,g.home_score)+"–"+Math.min(g.away_score,g.home_score)+". "+a(pl(k),k.player)+" led with "+k.k+" kills; "+a(pl(ast),ast.player)+" had "+ast.ast+" assists and "+a(pl(dig),dig.player)+" recorded "+dig.dig+" digs.</p>";
 out.innerHTML=hero("Match details.",g.date)+a("./game.html","← All matches")+score+panel("Set-by-set scoring",table(["Team",...g.away_sets.map((_,i)=>"Set "+(i+1)),"Final"],setRows))+panel("Team statistics",comparison)+panel("Game recap",recap)+panel("Standout performances",features(rs)+"<p>Category leaders; Player of the Match criteria pending.</p>")+box("away")+box("home")+"<p>Points = K + SA + BS + ½ BA. Hitting % = (K − E) / TA. No attempts are shown as —. Official team totals are preserved separately.</p>"+(g.date==="2019-09-07"?"<p>USD official assists: 61; individual rows total 62.</p>":"");return;
 }
 if(mode==="stats"){
 const cols=[["Matches","matches"],["Sets","sp"],["Kills","k"],["K/set","kps"],["HIT%","hit"],["Assists","ast"],["AST/set","astps"],["Digs","dig"],["DIG/set","digps"],["Blocks","blocks"],["BLK/set","blocksps"],["Aces","sa"],["SA/set","saps"],["Points","pts"],["PTS/set","ptsps"]];
 out.innerHTML=hero("Player leaderboards.","Career totals and per-set averages.")+'<div class="vb-controls"><label>Search <input id="q"></label><label>Rank by <select id="sort">'+cols.map(([l,k])=>'<option value="'+k+'"'+(k==="ptsps"?" selected":"")+">"+l+"</option>").join("")+'</select></label><label>Minimum sets <select id="min"><option>1</option><option>3</option><option>5</option><option>8</option><option>10</option></select></label></div><div id="leaders"></div><p>Hitting percentage rankings require 10 attempts. Individual blocks = BS + BA; team blocks = BS + BA/2.</p>';
 const render=()=>{const k=$("sort").value||"ptsps",q=$("q").value.toLowerCase(),min=Number($("min").value)||1;const rs=players.filter(p=>p.sp>=min&&(p.player+" "+p.teams.join(" ")).toLowerCase().includes(q)&&(k!=="hit"||p.ta>=10)).sort((a,b)=>(b[k]??-Infinity)-(a[k]??-Infinity)||a.player.localeCompare(b.player));$("leaders").innerHTML=table(["Player","Programs",...cols.map(x=>x[0])],rs.map(p=>tr([a(pl(p),p.player),e(p.teams.join(" / ")),...cols.map(([l,k])=>k==="hit"?hit(p):k.endsWith("ps")?p[k].toFixed(2):p[k])])));};
 for(const k of ["q","sort","min"])$(k).oninput=render;render();return;
 }
 if(mode==="player"){
 const p=players.find(x=>x.id===id);if(!p)throw Error("Player not found");
 out.innerHTML=a("./stats.html","← Player leaderboards")+'<div class="soccer-profile-head"><div class="soccer-portrait vb-portrait">'+portrait(p)+"</div><div><h1>"+e(p.player)+'</h1>'+photoCredit(p)+'<p class="lead">'+e(p.teams.join(" / "))+"</p></div></div>"+metric([["Matches",p.matches],["Sets",p.sp],["Kills/set",p.kps.toFixed(2)],["Hitting %",hit(p)],["Assists/set",p.astps.toFixed(2)],["Digs/set",p.digps.toFixed(2)],["Blocks/set",p.blocksps.toFixed(2)],["Aces/set",p.saps.toFixed(2)],["Points/set",p.ptsps.toFixed(2)]])+panel("Career totals",table(heads,[tr([e(p.player),...cells(p)])]));
 if(p.teams.length>1)out.innerHTML+=panel("Seen at multiple schools",table(["School","Matches","Sets","Kills","K/set","HIT%"],p.teams.map(t=>{const x=agg(p.logs.filter(r=>r.team===t));return tr([e(t),x.matches,x.sp,x.k,x.kps.toFixed(2),hit(x)]);})));
 out.innerHTML+=panel("Individual match log",table(["Date","Team","Opponent",...heads.slice(1)],p.logs.map(r=>{const g=byGame.get(r.game_id);return tr([a(gl(g),r.date),e(r.team),e(r.team===g.home?g.away:g.home),...cells(r)]);})));return;
 }
 out.innerHTML=hero("The best I’ve witnessed.","Single-match records by category.")+defs.map(([l,k])=>panel(l,table(["Player","Team","Date",l,"Match"],rank(rows,k).filter(p=>p[k]>0).slice(0,10).map(p=>tr([a(pl(p),p.player),e(p.team),e(p.date),p[k],a(gl(byGame.get(p.game_id)),"Box score ↗")]))))).join("");
 }catch(err){out.innerHTML=panel("Unable to load volleyball archive",e(err.message));}
});
