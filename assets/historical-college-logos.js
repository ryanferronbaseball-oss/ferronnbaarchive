/* Historical school logos: visual quality first; conservative date windows.
 * SportsLogos.Net (Fresno); Wikimedia Commons (GCU/UCR/LMU).
 * Team trademarks remain property of their respective owners.
 */
(function(){
"use strict";
const approved={
 "278":{from:"2016-07-01",until:"2019-12-11",src:"https://content.sportslogos.net/logos/31/681/full/fresno_state_bulldogs_logo_primary_20066867.png",credit:"SportsLogos.Net"},
 "2253":{from:"2015-07-01",until:"2023-06-30",src:"https://upload.wikimedia.org/wikipedia/commons/c/cf/Grand_Canyon_Antelopes_logo.svg",credit:"Wikimedia Commons / Grand Canyon University"},
 "27":{from:"2012-07-01",until:"2020-07-01",src:"https://upload.wikimedia.org/wikipedia/commons/f/f7/UC_Riverside_Highlanders_%28old%29_logo.svg",credit:"Wikimedia Commons / UC Riverside"},
 "2351":{from:"2008-07-01",until:"2019-01-01",src:"https://upload.wikimedia.org/wikipedia/commons/9/9c/Loyola_Marymount_Lions_logo.svg",credit:"Wikimedia Commons / Loyola Marymount University"}
};
const esc=v=>String(v??"").replace(/[&<>"']/g,c=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[c]));
function resolve(id,date){
 const key=String(id??"");if(!/^\d+$/.test(key))return null;
 const fallback="https://a.espncdn.com/i/teamlogos/ncaa/500/"+encodeURIComponent(key)+".png";
 const mark=approved[key],historical=/^\d{4}-\d{2}-\d{2}$/.test(String(date))&&mark&&date>=mark.from&&date<mark.until;
 return historical?{src:mark.src,fallback,credit:mark.credit}:{src:fallback,fallback:null};
}
function image(id,date,name){
 const r=resolve(id,date);if(!r)return "";
 return '<img src="'+esc(r.src)+'"'+(r.fallback?' data-logo-fallback="'+esc(r.fallback)+'" title="'+esc("Historical logo · "+r.credit)+'"':'')+' alt="'+esc(name)+' logo" loading="lazy" onerror="if(this.dataset.logoFallback){this.src=this.dataset.logoFallback;delete this.dataset.logoFallback}else{this.style.display=\'none\'}">';
}
window.CACollegeLogos={resolve,image};
})();