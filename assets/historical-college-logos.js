/* Historical school logos: visual quality first; conservative date windows.
 * SportsLogos.Net timelines are the primary reference; visual quality comes first.
 * Team trademarks remain property of their respective owners.
 */
(function(){
"use strict";
const approved={
 "2463":{from:"2014-06-02",until:"2023-06-01",src:"https://content.sportslogos.net/logos/30/628/full/cal_state_northridge_matadors_logo_primary_2014sportslogosnet9689.png",credit:"SportsLogos.Net"},
 "238":{from:"2022-03-22",until:"2025-01-01",src:"https://content.sportslogos.net/logos/35/895/full/vanderbilt_commodores_logo_primary_2022sportslogosnet9393.png",credit:"SportsLogos.Net"},
 "278":{from:"2016-07-01",until:"2019-12-11",src:"https://content.sportslogos.net/logos/31/681/full/fresno_state_bulldogs_logo_primary_20066867.png",credit:"SportsLogos.Net"},
 "2253":{from:"2015-07-16",until:"2023-06-30",src:"https://content.sportslogos.net/logos/31/5050/full/grand_canyon_antelopes_logo_primary_20157043.png",credit:"SportsLogos.Net"},
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