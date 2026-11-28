/* Reuse established profile photo identities in the existing Player of the Game sections. */
(()=>{"use strict";
const sport=document.currentScript?.dataset.sport;
const selectors={nba:".pog .pog-head",college:".pog .pog-head","college-women":".pog .pog-head",nfl:"#playerOfGame .pog-head",cfb:"#playerOfGame .pog-head","college-baseball":"#cb-player-of-game",nhl:"#playerOfGame .nhl-game-pog-head"};
if(!selectors[sport])return;
const read=async path=>{try{const r=await fetch(path,{cache:"no-store"});return r.ok?await r.json():{}}catch{return {}}};
const espnId=id=>/^espn:(\d+)$/.exec(id)?.[1]||null;
const espn=(league,id)=>id?"https://a.espncdn.com/i/headshots/"+league+"/players/full/"+id+".png":null;
let headshots={},baseballPortraits={},baseballRows=new Map(),nhlPortraits={},cfbPortraits={};
function collegeCandidates(id){
 const mapped=headshots[id]||{},mappedId=mapped.espn_athlete_id;
 const photoId=espnId(id)||(typeof mappedId==="string"&&/^\d+$/.test(mappedId)?mappedId:null);
 const schoolPhoto=(()=>{if(sport==="college-women"){if(mapped.provider==="official school"&&/^\.\/assets\/portraits\/utsa\/[a-z0-9-]+\.jpg$/.test(mapped.image_url))return mapped.image_url;}try{const u=new URL(mapped.image_url),s=new URL(mapped.source_url);const schools=["cubuffs.com","gohofstra.com","emueagles.com","santaclarabroncos.com","usdtoreros.com","fullertontitans.com","gopoly.com","utahstateaggies.com","denverpioneers.com","siuecougars.com","fightingirish.com","pacifictigers.com","goutsa.com","hawaiiathletics.com","goairforcefalcons.com","lipscombsports.com"];if(sport==="college-women")schools.push("gocards.com");const host=h=>h.replace(/^www\./,'');if(u.protocol!=='https:'||s.protocol!=='https:'||!schools.includes(host(s.hostname)))return null;const h=host(u.hostname);return (schools.includes(h)||/(^|\.)(sidearmsports\.com|sidearmdev\.com|sidearmnextgen\.com|und\.com|cloudfront\.net|amazonaws\.com|storage\.googleapis\.com|wmt\.digital|wmtcdn\.com|imgix\.net)$/.test(h))?u.href:null}catch{return null}})()
 return [schoolPhoto,espn(sport==="college-women"?"womens-college-basketball":"mens-college-basketball",photoId)].filter(Boolean);
}

function candidates(id){
 if(sport==="college"||sport==="college-women")return collegeCandidates(id);
 if(sport==="nba")return [espn("nba",espnId(id))].filter(Boolean);
 if(sport==="cfb"){const u=cfbPortraits[id]?.url;return [typeof u==="string"&&/^https:\/\/a\.espncdn\.com\/i\/headshots\/(?:college-football|cfb|nfl)\/players\/full\/\d+\.png$/.test(u)?u:null,espn("college-football",/^\d+$/.test(id)?id:null)].filter(Boolean)}
 if(sport==="nfl")return [espn("nfl",/^\d+$/.test(id)?id:null)].filter(Boolean);
 if(sport==="college-baseball")return window.CollegeBaseballArchive?.playerPortraitCandidates?.(baseballPortraits[id],baseballRows.get(id)||[])||[];
 if(sport==="nhl")return [nhlPortraits[id]?.url].filter(Boolean);
 return [];
}
function attachImage(portrait,id){
  const urls=[...new Set(candidates(id).filter(Boolean))];if(!urls.length)return;
  const img=document.createElement("img");img.alt="";img.className="ca-potg-headshot";img.loading="lazy";img.decoding="async";
  let index=0;const next=()=>{portrait.classList.remove("has-portrait");if(index>=urls.length){img.remove();return}img.src=urls[index++]};
  img.addEventListener("error",next);
  img.addEventListener("load",()=>{if(img.naturalWidth<=1||img.naturalHeight<=1){next();return}portrait.classList.add("has-portrait")});
  portrait.append(img);next();
}
function decorateStandouts(){
 if(!["nba","college","college-women"].includes(sport))return;
 for(const portrait of document.querySelectorAll(".ca-standout-portrait[data-standout-id]")){
  if(portrait.dataset.portraitReady==="1")continue;
  portrait.dataset.portraitReady="1";
  attachImage(portrait,portrait.dataset.standoutId);
 }
}
function decorate(){
 decorateStandouts();
 for(const section of document.querySelectorAll(selectors[sport])){
  if(section.querySelector(".ca-potg-portrait"))continue;
  const link=section.querySelector('a[href*="player.html?id="]');if(!link)continue;
  const id=new URL(link.href,location.href).searchParams.get("id");if(!id)continue;
  const name=link.textContent.trim();
  const portrait=document.createElement("a");portrait.className="ca-potg-portrait";portrait.href=link.href;portrait.setAttribute("aria-label","View "+name+" player profile");
  const fallback=document.createElement("span");fallback.className="ca-potg-initials";fallback.setAttribute("aria-hidden","true");fallback.textContent=name.split(/\s+/).filter(Boolean).slice(0,2).map(s=>s[0]).join("").toUpperCase();portrait.append(fallback);
  if(sport==="college-baseball"){
   const header=document.createElement("div");header.className="ca-potg-identity";
   const copy=document.createElement("div");copy.className="ca-potg-copy";
   const role=section.querySelector(".mlb-decision-role"),title=section.querySelector("h3");
   if(!role||!title)continue;
   role.before(header);header.append(portrait,copy);copy.append(role,title);
  }else{
   const copy=section.firstElementChild;if(!copy)continue;
   const header=document.createElement("div");header.className="ca-potg-identity";
   copy.before(header);header.append(portrait,copy);copy.classList.add("ca-potg-copy");
  }
  attachImage(portrait,id);
 }
}
async function init(){
 if(sport==="cfb")cfbPortraits=await read("./data/player_portraits.json");
 if(sport==="nhl")nhlPortraits=await read("./data/player_portraits.json");
 if(sport==="college"||sport==="college-women")headshots=(await read("./data/player_headshots.json")).players||{};
 if(sport==="college-baseball"){
  // The archive script is deferred on some pages.
  if(document.readyState==="loading")await new Promise(resolve=>document.addEventListener("DOMContentLoaded",resolve,{once:true}));
  const [registry,archive]=await Promise.all([read("./data/player_portraits.json"),window.CollegeBaseballArchive?.load().catch(()=>null)]);
  baseballPortraits=registry;
  for(const r of archive?.rows||[]){const id=String(r.player_id);if(!baseballRows.has(id))baseballRows.set(id,[]);baseballRows.get(id).push(r)}
 }
 new MutationObserver(decorate).observe(document.body,{childList:true,subtree:true});decorate();
}
init().catch(err=>console.warn("Player of the Game portraits unavailable",err));
})();