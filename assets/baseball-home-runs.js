/* Game-specific batting home runs, shared by the three baseball archives. */
(function(){
"use strict";
const esc=v=>String(v??"").replace(/[&<>"']/g,c=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[c]));
function render(rows,opts){
 const seen=new Map();
 for(const r of rows){
  const raw=opts.hr(r),n=Number(raw),id=r.player_id,name=opts.name(r);
  if(raw==null||String(raw).trim()===""||!Number.isInteger(n)||n<1||id==null||String(id).trim()===""||!name)continue;
  // These archives use one aggregated player batting line per game. Do not
  // double-count a duplicate imported line.
  const key=String(id),prior=seen.get(key);
  if(!prior||n>prior.hr)seen.set(key,{r,hr:n,name});
 }
 const hitters=[...seen.values()].sort((a,b)=>b.hr-a.hr||a.name.localeCompare(b.name)||String(a.r.player_id).localeCompare(String(b.r.player_id)));
 if(!hitters.length)return "";
 const total=hitters.reduce((s,x)=>s+x.hr,0);
 const card=({r,hr,name})=>{
  const href=opts.href(r),urls=[...new Set((opts.portraits(r)||[]).filter(u=>typeof u==="string"&&/^https:\/\/[^\s"'<>]+$/.test(u)))];
  const initials=name.trim().split(/\s+/).slice(0,2).map(w=>w[0]).join("").toUpperCase();
  const photo='<a class="ca-hr-portrait" href="'+esc(href)+'" aria-label="View '+esc(name)+' player profile"><span aria-hidden="true">'+esc(initials)+'</span>'+(urls.length?'<img src="'+esc(urls[0])+'" data-remaining="'+esc(JSON.stringify(urls.slice(1)))+'" alt="" loading="lazy" decoding="async" onload="if(this.naturalWidth>5&amp;&amp;this.naturalHeight>5)this.classList.add(\'is-loaded\');else this.onerror()" onerror="this.classList.remove(\'is-loaded\');const rest=JSON.parse(this.dataset.remaining);if(rest.length){this.dataset.remaining=JSON.stringify(rest.slice(1));this.src=rest[0]}else this.remove()">':'')+'</a>';
  return '<article class="ca-hr-card"><div class="ca-hr-main">'+photo+'<div class="ca-hr-copy"><strong class="ca-hr-count">'+hr+' <span>HR</span></strong><a class="ca-hr-player" href="'+esc(href)+'">'+esc(name)+'</a><small>'+esc(r.team||"")+'</small>'+(opts.credit?opts.credit(r):"")+'</div></div></article>';
 };
 return '<section class="panel ca-home-runs" aria-label="Home runs in this game"><div class="ca-hr-heading"><h2>Home Runs</h2><span>'+total+' recorded HR · '+hitters.length+' '+(hitters.length===1?"hitter":"hitters")+'</span></div><div class="ca-hr-grid">'+hitters.map(card).join("")+'</div></section>';
}
window.CABaseballHomeRuns={render};
})();
