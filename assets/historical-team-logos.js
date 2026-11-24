/* Courtside Archive historical primary marks. Season start years for NBA; calendar years for MLB.
 * Era references: https://logocdn.com/nba/ and https://logocdn.com/mlb/
 * Charlotte 2004–07: https://www.sportslogos.net/logos/view/8qy7zreof44lznm0kfwvjmvge/Charlotte-Bobcats-Logo/2005/Primary-Logo
 * Coverage begins in the archive's witnessed era (2003 MLB, 2005/06 NBA).
 * All marks remain the property of their respective teams/leagues.
 */
(function(){
"use strict";
const nba={
 "1":["atlanta-hawks",1995,2007,2015,2020],
 "2":["boston-celtics",1996],
 "3":["new-orleans-pelicans",[2002,"new-orleans-hornets","New Orleans Hornets"],[2005,"new-orleans-oklahoma-city-hornets","New Orleans/Oklahoma City Hornets"],[2007,"new-orleans-hornets","New Orleans Hornets"],[2008,"new-orleans-hornets","New Orleans Hornets"],2013,2023],
 "4":["chicago-bulls",1966],
 "5":["cleveland-cavaliers",2003,2010,2017,2022],
 "7":["denver-nuggets",2003,2008,2018],
 "9":["golden-state-warriors",1997,2010,2019],
 "10":["houston-rockets",2003,2019,2026],
 "12":["los-angeles-clippers",1984,2010,2015,2024],
 "13":["los-angeles-lakers",2001,2023],
 "14":["miami-heat",1999],
 "16":["minnesota-timberwolves",1996,2008,2017,2026],
 "18":["new-york-knicks",1995,2011,2022],
 "21":["phoenix-suns",2000,2013],
 "23":["sacramento-kings",1994,2016],
 "24":["san-antonio-spurs",2002,2017],
 "25":["oklahoma-city-thunder",[2001,"seattle-supersonics","Seattle SuperSonics"],2008],
 "26":["utah-jazz",1996,2004,2010,2016,2022,2025],
 "30":["charlotte-hornets",[2004,"charlotte-bobcats","Charlotte Bobcats","https://content.sportslogos.net/logos/6/258/full/8qy7zreof44lznm0kfwvjmvge.gif"],[2007,"charlotte-bobcats","Charlotte Bobcats"],[2012,"charlotte-bobcats","Charlotte Bobcats"],2014]
};
const mlb={
 "108":["los-angeles-angels",[2002,"anaheim-angels","Anaheim Angels"],[2005,"los-angeles-angels-of-anaheim","Los Angeles Angels of Anaheim"],2016],
 "109":["arizona-diamondbacks",1998,2007,2012,2024],
 "110":["baltimore-orioles",1999,2009,2019],
 "111":["boston-red-sox",1976,2009],
 "112":["chicago-cubs",1979],
 "113":["cincinnati-reds",1999,2013],
 "114":["cleveland-guardians",[1986,"cleveland-indians","Cleveland Indians"],[2014,"cleveland-indians","Cleveland Indians"],2022],
 "115":["colorado-rockies",1993,2017],
 "116":["detroit-tigers",1994,2006,2016],
 "117":["houston-astros",2000,2013],
 "118":["kansas-city-royals",2002,2019,2026],
 "119":["los-angeles-dodgers",1979,2012],
 "120":["washington-nationals",[1992,"montreal-expos","Montreal Expos"],2005,2011],
 "121":["new-york-mets",1999],
 "133":["athletics",[1993,"oakland-athletics","Oakland Athletics"],2025],
 "134":["pittsburgh-pirates",1997,2014],
 "135":["san-diego-padres",1992,2004,2011,2012,2015,2020],
 "136":["seattle-mariners",1993],
 "137":["san-francisco-giants",2000],
 "138":["st-louis-cardinals",1999],
 "139":["tampa-bay-rays",[2001,"tampa-bay-devil-rays","Tampa Bay Devil Rays"],2008,2019],
 "140":["texas-rangers",1994,2003],
 "141":["toronto-blue-jays",2003,2004,2012,2020],
 "142":["minnesota-twins",1987,2010,2023],
 "143":["philadelphia-phillies",1992,2019],
 "144":["atlanta-braves",1987,2018,2022],
 "145":["chicago-white-sox",1991],
 "146":["miami-marlins",[1993,"florida-marlins","Florida Marlins"],2012,2017,2019],
 "147":["new-york-yankees",1968],
 "158":["milwaukee-brewers",2000,2018,2020]
};
const esc=v=>String(v??"").replace(/[&<>"']/g,c=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[c]));
const title=s=>s.split("-").map(w=>w==="of"?"of":w==="st"?"St.":w.charAt(0).toUpperCase()+w.slice(1)).join(" ");
function season(league,date){
 if(!/^\d{4}-\d{2}-\d{2}$/.test(String(date)))return null;
 const y=Number(date.slice(0,4)),m=Number(date.slice(5,7));
 if(y<1900||y>2100||m<1||m>12)return null;
 if(league!=="nba")return y;
 if(date>="2020-07-01"&&date<="2020-10-11")return 2019;
 if(date>="2021-07-01"&&date<="2021-07-20")return 2020;
 return y-(m<7?1:0);
}
function resolve(league,id,date){
 const year=season(league,date),list=(league==="nba"?nba:league==="mlb"?mlb:{})[String(id)];
 if(year===null||!list)return null;
 const [slug,...eras]=list;
 const era=eras.map(e=>Array.isArray(e)?e:[e,slug]).filter(e=>e[0]<=year).at(-1);
 if(!era)return null;
 const [start,mark,name,override]=era;
 const root="https://assets.logocdn.com/images/sports/"+league+"/"+start+"/"+mark;
 return {year,start,name:name||title(mark),src:override||root+".svg",fallback:root+"@3x.png"};
}
function name(league,id,date,fallback){return resolve(league,id,date)?.name||fallback;}
function image(league,id,date,label){
 const r=resolve(league,id,date);if(!r)return "";
 return '<img src="'+esc(r.src)+'" data-era-fallback="'+esc(r.fallback)+'" alt="'+esc(label||r.name)+' logo" title="'+esc(r.name+' · '+(league==="nba"?r.year+"–"+String(r.year+1).slice(-2):r.year))+'" loading="lazy" onerror="if(this.dataset.eraFallback){this.src=this.dataset.eraFallback;delete this.dataset.eraFallback}else{this.remove()}">';
}
window.CAHistoricalLogos={resolve,season,name,image};
})();