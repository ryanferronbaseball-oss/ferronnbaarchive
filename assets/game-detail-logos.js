/* Game-date logo adapters. Professional historical overrides from SportsLogos.Net.
 * College standard marks are a visual-quality fallback, not a claim of full era verification.
 * Source references and limitations are documented in game-detail-logo-audit.md.
 */
(function(){
"use strict";
const norm=s=>String(s??"").toLowerCase().replace(/[^a-z0-9]/g,"");
const mlb={"losangelesangels":108,"anaheimangels":108,"losangelesangelsofanaheim":108,"arizonadiamondbacks":109,"baltimoreorioles":110,"bostonredsox":111,"chicagocubs":112,"cincinnatireds":113,"clevelandindians":114,"clevelandguardians":114,"coloradorockies":115,"detroittigers":116,"houstonastros":117,"kansascityroyals":118,"losangelesdodgers":119,"montrealexpos":120,"washingtonnationals":120,"newyorkmets":121,"oaklandathletics":133,"athletics":133,"pittsburghpirates":134,"sandiegopadres":135,"seattlemariners":136,"sanfranciscogiants":137,"stlouiscardinals":138,"tampabayrays":139,"tampabaydevilrays":139,"texasrangers":140,"torontobluejays":141,"minnesotatwins":142,"philadelphiaphillies":143,"atlantabraves":144,"chicagowhitesox":145,"miamimarlins":146,"floridamarlins":146,"newyorkyankees":147,"milwaukeebrewers":158};
const school={"angelostate":"https://www.ncaa.com/sites/default/files/images/logos/schools/bgl/angelo-st.svg","austinpeay":"2046","barton":"https://www.collegecod.com/media/team-logos/BARTON_COLLEGE.png","bellarmine":"91","bryant":"2803","bucknell":"2083","butler":"2086","centralarkansas":"2110","connecticut":"41","dallasbaptist":"2164","delaware":"48","easttennesseestate":"2193","easternkentucky":"2198","georgemason":"2244","georgewashington":"45","georgetown":"46","indianastate":"282","indianapolis":"https://www.ncaa.com/sites/default/files/images/logos/schools/bgl/indianapolis.svg","lenoirrhyne":"https://www.ncaa.com/sites/default/files/images/logos/schools/bgl/lenoir-rhyne.svg","longbeachstate":"299","louisiana":"309","marist":"2368","marshall":"276","missouristate":"2623","monmouth":"2405","newmexicostate":"166","nicholls":"2447","northalabama":"2453","northwesternstate":"2466","ohio":"195","oklahomastate":"197","pointlomanazarene":"https://www.ncaa.com/sites/default/files/images/logos/schools/bgl/point-loma.svg","queens":"2511","quinnipiac":"2514","rhodeisland":"227","samhoustonstate":"2534","siena":"2561","southernillinois":"79","stjoes":"2603","stonehill":"284","tampa":"https://www.ncaa.com/sites/default/files/images/logos/schools/bgl/tampa.svg","tcu":"2628","tennesseetech":"2635","uab":"5","utmartin":"2630","villanova":"222","vmi":"2678","wagner":"2681","washington":"264","westernmichigan":"2711","westernnewmexico":"2703","alabama":"333","arizona":"12","arkansas":"8","auburn":"2","byu":"252","baylor":"239","binghamton":"2066","calbaptist":"2856","calpoly":"13","calstatebakersfield":"2934","calstatenorthridge":"2463","california":"25","campbell":"2097","cincinnati":"2132","clemson":"228","coastalcarolina":"324","cornell":"172","davidson":"2166","duke":"150","eastcarolina":"151","easternmichigan":"2199","florida":"57","floridastate":"52","fresnostate":"278","gardnerwebb":"2241","georgia":"61","georgiasouthern":"290","georgiastate":"2247","georgiatech":"59","gonzaga":"2250","grandcanyon":"2253","hawaii":"62","highpoint":"2272","illinois":"356","indiana":"84","iowa":"2294","jamesmadison":"256","kansasstate":"2306","kennesawstate":"338","kentucky":"96","lsu":"99","liberty":"2335","louisville":"97","loyolamarymount":"2351","maryland":"120","mercer":"2382","miami":"2390","michiganstate":"127","middletennesseestate":"2393","milwaukee":"270","minnesota":"135","mississippistate":"344","missouri":"142","ncstate":"152","nebraska":"158","northcarolina":"153","northeastern":"111","notredame":"87","oklahoma":"201","olddominion":"295","oregon":"2483","oregonstate":"204","pacific":"279","pepperdine":"2492","pittsburgh":"221","portland":"2501","presbyterian":"2506","princeton":"163","purdue":"2509","richmond":"257","rutgers":"164","saintmarys":"2608","sandiego":"301","sandiegostate":"21","sanfrancisco":"2539","santaclara":"2541","southalabama":"6","southcarolina":"2579","southerncalifornia":"30","southernmississippi":"2572","stbonaventure":"179","stjohns":"2599","stlouis":"139","stanford":"24","stonybrook":"2619","tennessee":"2633","texas":"251","texasam":"245","troy":"2653","tulane":"2655","ucriverside":"27","ucsandiego":"28","ucf":"2116","uncasheville":"2427","uncgreensboro":"2430","uncwilmington":"350","utah":"254","vcu":"2670","vanderbilt":"238","virginia":"258","virginiatech":"259","wakeforest":"154","westvirginia":"277","westernkentucky":"98","wichitastate":"2724","williamandmary":"2729","winthrop":"2737","xavier":"2752","olemiss":"145","seattle":"2547","southeasternlouisiana":"2545","thecitadel":"2643","calstatenorthrdige":"2463","calstatefullerton":"2239","ucirvine":"300","westernnewmexicomustangs":"2703","sandiegotoreros":"301","butlerbulldogs":"2086","davidsonwildcats":"2166","ucdavisaggies":"302","ncstatewolfpack":"152","wakeforestdemondeacons":"154","delawarefightinbluehens":"48","westernkentuckyhilltoppers":"98","usc":"30","ucla":"26","csun":"2463","northcarolinastate":"152","arizonastate":"9","coloradostate":"36","colorado":"38","hartford":"42","boisestate":"68","northernkentucky":"94","holycross":"107","harvard":"108","michigan":"130","newmexico":"167","collegeofcharleston":"232","northtexas":"249","utarlington":"250","lipscomb":"288","ucdavis":"302","maine":"311","utahstate":"328","floridagulfcoast":"526","littlerock":"2031","belmont":"2057","callutheran":"2094","centralmichigan":"2117","denver":"2172","drake":"2181","easternillinois":"2197","hofstra":"2275","laverne":"2318","longwood":"2344","unlv":"2439","nevada":"2440","norfolkstate":"2450","northerncolorado":"2458","northernarizona":"2464","portlandstate":"2502","robertmorris":"2523","siuedwardsville":"2565","tennesseestate":"2634","weberstate":"2692","grambling":"2755","sandiegochristian":"3096","lifepacific":"109670"};
const lookup=(m,name)=>m[norm(name)];
const espn=(league,id,name)=>id?{src:"https://a.espncdn.com/i/teamlogos/"+league+"/500/"+encodeURIComponent(id)+".png",name}:null;
const source=(url,name,credit="SportsLogos.Net")=>({src:url,name,credit});
const nfl={
 "sanfrancisco49ers":[[2005,2008,"https://content.sportslogos.net/logos/7/179/full/san-francisco-49ers-logo-primary-2005-17936602005.png"]],
 "arizonacardinals":[[2005,2022,"https://content.sportslogos.net/logos/7/177/full/arizona_cardinals_logo_primary_20058304.png"]],
 "stlouisrams":[[2000,2015,"https://content.sportslogos.net/logos/7/178/full/1029.png"]],
 "indianapoliscolts":[[2004,2099,"https://content.sportslogos.net/logos/7/158/full/indianapolis_colts_logo_primary_20043652.png"]],
 "tennesseetitans":[[2002,2025,"https://content.sportslogos.net/logos/7/160/full/tennessee-titans-logo-primary-1999-6125.png"]]
};
const nhl={
 "phoenixcoyotes":[[2003,2013,"https://content.sportslogos.net/logos/1/23/full/phoenix_coyotes-primary_20048241.png"]],
 "losangeleskings":[[2002,2010,"https://content.sportslogos.net/logos/1/14/full/los_angeles_kings_logo_primary_20038964.png"]]
};
const soccer={
 "sandiegoloyal":[[2020,2023,"https://content.sportslogos.net/logos/124/6728/full/4139_san_diego_loyal_sc-primary-2020.png"]]
};
const soccerIds={"nashvillesc":18986,"fccincinnati":18267,"sportingkansascity":186,"oaklandroots":20687};
function era(m,name,year){const row=lookup(m,name)?.find(x=>year>=x[0]&&year<=x[1]);return row?source(row[2],name):null;}
// Explicit game-ID overrides, not changes to the normal franchise era timelines.
const throwbacks={
 "234959":{date:"2008-06-27",year:1978,teams:{
  seattlemariners:"https://content.sportslogos.net/logos/53/75/full/seattle_mariners_logo_primary_19779169.png",
  sandiegopadres:"https://content.sportslogos.net/logos/54/73/full/x5qgaefxmvbsmrkzw3k8qggwr.png"}},
 "319319":{date:"2012-08-03",year:1989,teams:{
  newyorkmets:"https://content.sportslogos.net/logos/54/67/full/new_york_mets_logo_primary_1962sportslogosnet5793.png",
  sandiegopadres:"https://content.sportslogos.net/logos/54/73/full/16ijawjyoq2m75gmdxhgdbwjk.png"}}
};
const nationalCrests={
 haiti:"https://assets.footylogos.com/logos/haiti-national-team/haiti-national-team-logo-footylogos.svg",
 morocco:"https://assets.footylogos.com/logos/morocco-national-team/morocco-national-team-logo-footylogos.svg"
};
function resolve(league,name,date,id,gameId){
 const y=Number(String(date).slice(0,4));if(!/^\d{4}-\d{2}-\d{2}$/.test(String(date)))return null;
 if(league==="mlb"){
  const event=throwbacks[String(gameId)],url=event?.date===date?lookup(event.teams,name):null;
  if(url)return source(url,name+" · "+event.year+" Turn Back the Clock");
  return window.CAHistoricalLogos?.resolve("mlb",lookup(mlb,name),date)||null;
 }
 if(league==="college"){
  const key=id||lookup(school,name);
  if(!key)return null;
  if(/^https:\/\//i.test(String(key)))return source(key,name,"School logo registry");
  return window.CACollegeLogos?.resolve(key,date)?{...window.CACollegeLogos.resolve(key,date),name}:espn("ncaa",key,name);
 }
 if(league==="nfl")return era(nfl,name,y);
 if(league==="nhl")return era(nhl,name,y-(Number(date.slice(5,7))<7?1:0));
 if(league==="soccer"){
  const crest=lookup(nationalCrests,name);
  if(crest)return source(crest,name+" national team crest","FootyLogos.com");
  return era(soccer,name,y)||(y>=2020?espn("soccer",lookup(soccerIds,name),name):null);
 }
 if(league==="milb"){
  if(norm(name)==="lakeelsinorestorm"&&y>=2002&&y<=2023)return source("https://content.sportslogos.net/logos/41/2138/full/gatxy5ed07vg6nghave0.gif",name);
  // Owner-approved: complex league clubs use their MLB parent mark for the actual game date.
  const aclParents={aclroyals:118,aclrangers:140,aclcubs:112,aclpadres:135};
  const parent=aclParents[norm(name)];
  if(parent){const mark=window.CAHistoricalLogos?.resolve("mlb",parent,date);return mark?{...mark,name:name+" · "+mark.name+" parent logo"}:null;}
  if(!id||/^ACL /i.test(name))return null;
  return {src:"https://www.mlbstatic.com/team-logos/"+encodeURIComponent(id)+".svg",name,credit:"MiLB standard mark"};
 }
 return null;
}
window.CAGameLogos={resolve};
})();