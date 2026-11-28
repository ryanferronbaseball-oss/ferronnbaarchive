/* Six category leaders, shared by NBA and both college basketball archives. */
(function(){
"use strict";
const categories=[["Points","pts"],["Rebounds","reb"],["Assists","ast"],["Steals","stl"],["Blocks","blk"],["3PM","fg3m"]];
const esc=v=>String(v??"").replace(/[&<>"']/g,c=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[c]));
const known=v=>v!=null&&String(v).trim()!==""&&Number.isFinite(Number(v))&&Number(v)>=0;
const url=p=>"./player.html?id="+encodeURIComponent(p.player_id);
const link=p=>'<a class="player-link ca-standout-player" href="'+esc(url(p))+'">'+esc(p.player)+'</a>';
const initials=p=>String(p.player).trim().split(/\s+/).slice(0,2).map(w=>w[0]).join("").toUpperCase();
function render(players,teamNames,impact){
 const rows=players.filter(p=>p.player_id!=null&&p.player);
 const card=([label,key])=>{
  const available=rows.filter(p=>known(p[key]));
  const value=available.length?Math.max(...available.map(p=>Number(p[key]))):null;
  const heading='<article class="ca-standout-card"><h3>'+esc(label)+'</h3>';
  if(value==null||value===0)return heading+'<div class="ca-standout-empty"><strong>'+(value==null?"—":"0")+'</strong><span>'+(value==null?"Statistic unavailable":"No recorded "+(key==="fg3m"?"three-pointers":label.toLowerCase()))+'</span></div></article>';
  const winners=available.filter(p=>Number(p[key])===value).sort((a,b)=>(impact(b)??-Infinity)-(impact(a)??-Infinity)||String(a.player).localeCompare(String(b.player))||String(a.player_id).localeCompare(String(b.player_id)));
  const p=winners[0],team=teamNames[String(p.team_id)]||p.team||"";
  return heading+'<div class="ca-standout-main"><a class="ca-potg-portrait ca-standout-portrait" data-standout-id="'+esc(p.player_id)+'" href="'+esc(url(p))+'" aria-label="View '+esc(p.player)+' player profile"><span class="ca-potg-initials" aria-hidden="true">'+esc(initials(p))+'</span></a><div class="ca-standout-copy"><strong class="ca-standout-number">'+esc(value)+'</strong>'+link(p)+'<small>'+esc(team)+'</small></div></div>'+(winners.length>1?'<div class="ca-standout-ties"><span>Tied with </span>'+winners.slice(1).map(link).join(", ")+'</div>':"")+(available.length<rows.length?'<div class="ca-standout-partial">Available stats only</div>':"")+'</article>';
 };
 return '<section class="panel ca-standouts"><h2>Standout performers</h2><div class="ca-standout-grid">'+categories.map(card).join("")+'</div></section>';
}
window.CABasketballStandouts={render};
})();
