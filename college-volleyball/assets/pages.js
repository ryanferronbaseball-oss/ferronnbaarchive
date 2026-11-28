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
 const options=active=>'<div class="soccer-filters vb-match-selector"><label for="vbGameSelect">Select a match<select id="vbGameSelect"><option value="">All attended matches</option>'+games.map(g=>'<option value="'+e(g.id)+'"'+(g.id===active?' selected':'')+'>'+e(g.date+' · '+g.away+' @ '+g.home)+'</option>').join("")+'</select></label></div>';
 const bind=()=>{$("vbGameSelect").addEventListener("change",()=>{const next=$("vbGameSelect").value;location.href=next?'./game.html?id='+encodeURIComponent(next):'./game.html';});};
 if(!id){out.innerHTML=hero("Match history.","All attended matches.")+options("")+cards()+history();bind();return;}
 const g=byGame.get(id);if(!g)throw Error("Match not found");
 const rs=rows.filter(p=>p.game_id===g.id);
 if(rs.some(p=>p.team!==g.away&&p.team!==g.home))throw Error("Player records do not safely match this game");
 const ids={"Texas":"251","San Diego":"301","Nebraska":"158","BYU":"252","San Diego State":"21"};
 const logo=s=>window.CAGameLogos?.resolve("college",g[s],g.date,ids[g[s]])||{src:"https://a.espncdn.com/i/teamlogos/ncaa/500/"+ids[g[s]]+".png",name:g[s]};
 const meta=[g.attendance!=null?Number(g.attendance).toLocaleString("en-US")+" announced attendance":"",rs.length+" player appearances",'<a href="'+e(g.source_url)+'" target="_blank" rel="noopener noreferrer">Official box score ↗</a>'].filter(Boolean).join(" · ");
 const score=window.CAGameScore.render({date:g.date,venue:g.venue,away:team(g,"away"),home:team(g,"home"),awayScore:g.away_score,homeScore:g.home_score,awayLogo:logo("away"),homeLogo:logo("home"),status:"FINAL · SETS",metaHtml:meta});
 const setRows=["away","home"].map(s=>'<tr><td><strong>'+e(team(g,s))+'</strong></td>'+g[s+"_sets"].map((v,i)=>'<td class="'+(v>g[(s==="away"?"home":"away")+"_sets"][i]?"vb-set-won":"")+'">'+e(v)+'</td>').join("")+'<td><strong>'+e(g[s+"_score"])+'</strong></td></tr>');
 const setTable='<div class="table-wrap"><table class="soccer-stat-table vb-set-table"><thead><tr><th>Team</th>'+g.away_sets.map((_,i)=>'<th>Set '+(i+1)+'</th>').join("")+'<th>Final</th></tr></thead><tbody>'+setRows.join("")+'</tbody></table></div>';
 const ts=[["Kills","k"],["Errors","e"],["Attempts","ta"],["Hitting %","hit"],["Assists","ast"],["Aces","sa"],["Service errors","se"],["Digs","dig"],["Team blocks","blocks"],["Points","pts"]];
 const comparison=table(["Statistic",g.away,g.home],ts.map(([l,k])=>tr([e(l),...["away","home"].map(s=>e(k==="hit"?hit(g.team_totals[s]):g.team_totals[s][k]))])));
 const playerLink=p=>'<a class="vb-player-link" href="'+e(pl(p))+'">'+e(p.player)+'</a>';
 const box=s=>'<section class="soccer-panel vb-box-panel"><div class="vb-team-heading"><img src="'+e(logo(s).src||"")+'" alt="" onerror="this.remove()"><h3>'+e(team(g,s))+' <small>· '+(s==="away"?"Away":"Home")+'</small></h3></div><div class="table-wrap vb-box-scroll"><table class="soccer-stat-table vb-table vb-player-box"><thead><tr>'+heads.map(h=>'<th scope="col">'+e(h)+'</th>').join("")+'</tr></thead><tbody>'+rs.filter(p=>p.team===g[s]).map(p=>tr([playerLink(p),...cells(p)])).join("")+'<tr class="vb-totals">'+["<strong>Official team total</strong>",...cells({...g.team_totals[s],sp:"—"})].map(x=>'<td>'+x+'</td>').join("")+'</tr></tbody></table></div></section>';
 const k=rank(rs,"k")[0],ast=rank(rs,"ast")[0],dig=rank(rs,"dig")[0];
 const recap='<section class="soccer-panel game-recap vb-recap"><div class="recap-kicker">Every game has a story</div><h2>Game recap</h2><p>'+e(g.home_score>g.away_score?g.home:g.away)+" won "+Math.max(g.away_score,g.home_score)+"–"+Math.min(g.away_score,g.home_score)+". "+playerLink(k)+" led with "+k.k+" kills; "+playerLink(ast)+" had "+ast.ast+" assists and "+playerLink(dig)+" recorded "+dig.dig+" digs.</p></section>";
 const highlights='<div class="vb-highlights">'+defs.map(([l,key])=>{const p=rank(rs,key)[0];return '<article class="soccer-tile vb-highlight"><small>'+e(l)+'</small><div class="soccer-feature"><a class="soccer-avatar" href="'+e(pl(p))+'" aria-label="'+e(p.player)+' profile">'+portrait(p)+'</a><div class="data"><strong>'+e(p[key])+'</strong><div>'+playerLink(p)+'</div><small>'+e(p.team)+'</small></div></div></article>'}).join("")+'</div>';
 const idx=games.findIndex(x=>x.id===g.id);
 const pagination='<nav class="vb-pagination" aria-label="Adjacent matches">'+(idx>0?a(gl(games[idx-1]),"← Previous match"):"<span></span>")+a("./game.html","All matches")+(idx<games.length-1?a(gl(games[idx+1]),"Next match →"):"<span></span>")+'</nav>';
 document.title=g.away+" @ "+g.home+" · "+g.date+" | Courtside Archive";
 out.innerHTML=hero("Match details.","Revisit every attended volleyball match with verified set scores and individual statistics.")+options(g.id)+score+panel("Set-by-set scoring",setTable)+recap+panel("Standout performances",highlights+'<p class="soccer-note">Category leaders; Player of the Match scoring criteria pending.</p>')+'<div class="vb-box-heading"><h2>Player box score</h2></div>'+box("away")+box("home")+panel("Team statistics",comparison)+'<p class="soccer-note">Points = K + SA + BS + ½ BA. Hitting % = (K − E) / TA. No attempts are shown as —. Official team totals are preserved separately. Player rows follow source order; starting lineups are not inferred.</p>'+(g.date==="2019-09-07"?'<p class="soccer-note">USD official assists: 61; individual rows total 62.</p>':"")+pagination;
 bind();return;
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
