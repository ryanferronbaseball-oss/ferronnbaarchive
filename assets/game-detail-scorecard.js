/* Shared game-detail scorecard, modeled on the original NBA detail page. */
(function(){
"use strict";
const esc=v=>String(v??"").replace(/[&<>"']/g,c=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[c]));
const valid=v=>v!==null&&v!==undefined&&String(v).trim()!==""&&Number.isFinite(Number(v));
function render(o){
 const a=valid(o.awayScore),h=valid(o.homeScore),complete=a&&h;
 const winner=complete?(Number(o.awayScore)>Number(o.homeScore)?"away":Number(o.homeScore)>Number(o.awayScore)?"home":""):"";
 const logo=mark=>mark&&(/^https:\/\//i.test(mark.src)||mark.src==="../assets/logos/padres-pcl-1948-cap-recreation.svg")?'<img class="ca-game-score-logo" src="'+esc(mark.src)+'"'+(mark.fallback&&/^https:\/\//i.test(mark.fallback)?' data-logo-fallback="'+esc(mark.fallback)+'"':'')+' alt="" title="'+esc(mark.name||"Historical team logo")+'" width="80" height="80" decoding="async" onerror="if(this.dataset.logoFallback){this.src=this.dataset.logoFallback;delete this.dataset.logoFallback}else{this.remove()}">':"";
 const side=(key,name,value,known)=>'<div class="ca-game-score-side ca-game-score-'+key+'"><div class="ca-game-score-label">'+key.toUpperCase()+'</div><div class="ca-game-score-team'+(winner===key?' ca-game-score-winner':'')+'">'+esc(name||"Unknown team")+'</div><div class="ca-game-score-line"><div class="ca-game-score-number">'+(known?esc(value):"—")+'</div>'+logo(key==="away"?o.awayLogo:o.homeLogo)+'</div></div>';
 return '<section class="ca-game-scorecard" aria-label="Game score"><div class="ca-game-score-kicker">'+(o.headingHtml||[o.date,o.venue,o.context].filter(Boolean).map(esc).join(" · "))+'</div><div class="ca-game-score-grid">'+side("away",o.away,o.awayScore,a)+'<div class="ca-game-score-status">'+esc(o.status||(complete?"FINAL":"SCORE PENDING"))+'</div>'+side("home",o.home,o.homeScore,h)+'</div>'+(o.metaHtml?'<div class="ca-game-score-meta">'+o.metaHtml+'</div>':'')+'</section>';
}
window.CAGameScore={render,esc};
})();