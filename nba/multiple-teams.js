(()=>{"use strict";
const lib=window.NBAMultiTeams,$=id=>document.getElementById(id),esc=lib.esc;
let qualifying=[];
function table(teams){return '<div class="multi-table-wrap"><table class="multi-table"><thead><tr><th>Team</th><th>Games</th><th>MPG</th><th>PPG</th><th>RPG</th><th>APG</th></tr></thead><tbody>'+teams.map(t=>{const s=lib.stat(t);return '<tr><td class="team-name">'+lib.logo(t.id,t.name)+esc(t.name)+'</td><td>'+s.games+'</td><td>'+lib.fmt(s.mpg)+'</td><td>'+lib.fmt(s.ppg)+'</td><td>'+lib.fmt(s.rpg)+'</td><td>'+lib.fmt(s.apg)+'</td></tr>'}).join("")+'</tbody></table></div>';}
function draw(){
 const q=$("search").value.trim().toLowerCase(),sort=$("sort").value;
 const list=qualifying.filter(p=>(p.name+" "+p.teams.map(t=>t.name).join(" ")).toLowerCase().includes(q));
 list.sort((a,b)=>sort==="name"?a.name.localeCompare(b.name):sort==="teams"?b.teams.length-a.teams.length||b.games-a.games:b.games-a.games||a.name.localeCompare(b.name));
 $("directory").innerHTML=list.map(p=>'<article class="multi-card"><div class="multi-card-top"><a class="player-name" href="./player.html?id='+encodeURIComponent(p.id)+'">'+esc(p.name)+'</a><span class="multi-badge">'+p.teams.length+' teams witnessed</span></div><div class="multi-path">'+lib.journey(p.teams)+'</div>'+table(p.teams)+'<div class="multi-card-foot"><span>'+p.games+' attended player-games</span><a href="./player.html?id='+encodeURIComponent(p.id)+'">Full player profile →</a></div></article>').join("")||'<div class="multi-empty">No players match your search.</div>';
 $("shown").textContent=list.length+" of "+qualifying.length+" qualifying players";
}
fetch("../data/player_boxscores_espn.json",{cache:"no-store"})
 .then(r=>{if(!r.ok)throw Error("Unable to load verified NBA player box scores");return r.json()})
 .then(rows=>{
   qualifying=lib.group(rows).filter(p=>p.teams.length>=3);
   $("playerCount").textContent=qualifying.length;
   $("teamCount").textContent=qualifying.reduce((n,p)=>n+p.teams.length,0);
   $("gameCount").textContent=qualifying.reduce((n,p)=>n+p.games,0);
   draw();
 }).catch(err=>{$("directory").innerHTML='<p class="multi-empty">'+esc(err.message)+'</p>';});
$("search").addEventListener("input",draw);
$("sort").addEventListener("change",draw);
})();