/* Shared portrait treatment for witnessed team/school journey directories. */
(()=>{"use strict";
const directory=document.getElementById("directory");
const sport=document.currentScript?.dataset.sport;
if(!directory||!["college","college-baseball","nba","mlb"].includes(sport))return;
const read=async path=>{try{const r=await fetch(path,{cache:"no-store"});return r.ok?await r.json():{}}catch{return {}}};
let headshots={},portraitFallbacks={},baseballPortraits={},baseballRows=new Map();
const espnId=id=>/^espn:(\d+)$/.exec(id)?.[1]||null;
const espn=(league,id)=>id?"https://a.espncdn.com/i/headshots/"+league+"/players/full/"+id+".png":null;
function collegeCandidates(id){
 const mapped=headshots[id]||{},mappedId=mapped.espn_athlete_id;
 const photoId=espnId(id)||(typeof mappedId==="string"&&/^\d+$/.test(mappedId)?mappedId:null);
 const schoolPhoto=(()=>{try{const u=new URL(mapped.image_url),s=new URL(mapped.source_url);const schools=["cubuffs.com","gohofstra.com","emueagles.com","santaclarabroncos.com","usdtoreros.com","fullertontitans.com","gopoly.com","utahstateaggies.com","denverpioneers.com","siuecougars.com","fightingirish.com"];const host=h=>h.replace(/^www\./,'');if(u.protocol!=='https:'||s.protocol!=='https:'||!schools.includes(host(s.hostname)))return null;const h=host(u.hostname);return (schools.includes(h)||/(^|\.)(sidearmsports\.com|sidearmdev\.com|sidearmnextgen\.com|und\.com|cloudfront\.net|amazonaws\.com)$/.test(h))?u.href:null}catch{return null}})()
 return [schoolPhoto,espn("mens-college-basketball",photoId)].filter(Boolean);
}
function mlbPortrait(id){
 const url=portraitFallbacks[String(id)]?.url;
 return typeof url==="string"&&(/^https:\/\/a\.espncdn\.com\/i\/headshots\/mlb\/players\/full\/\d+\.png$/.test(url)||/^https:\/\/upload\.wikimedia\.org\/wikipedia\/commons\//.test(url)|| (["historical","official"].includes(portraitFallbacks[String(id)]?.provider)&&/^https:\/\/(?:[a-z0-9.-]+\.)?(?:mlb\.com|mlbstatic\.com|espncdn\.com|baseball-reference\.com|sports-reference\.com|sr-logos\.com|sidearmsports\.com|sidearmdev\.com|sidearmnextgen\.com|gohofstra\.com|riceowls\.com|rolltide\.com|cloudfront\.net|amazonaws\.com)\/[^\s"'<>]+$/i.test(url)))
 ? url : "https://img.mlbstatic.com/mlb-photos/image/upload/w_213,q_85/v1/people/"+encodeURIComponent(id)+"/headshot/67/current";
}
function candidates(id){
 if(sport==="nba")return [espn("nba",espnId(id))].filter(Boolean);
 if(sport==="college")return collegeCandidates(id);
 if(sport==="mlb")return /^\d+$/.test(id)?[mlbPortrait(id),"https://img.mlbstatic.com/mlb-photos/image/upload/w_213,q_85/v1/people/"+id+"/headshot/67/current"]:[];
 return window.CollegeBaseballArchive?.playerPortraitCandidates?.(baseballPortraits[id],baseballRows.get(id)||[])||[];
}
function credit(card,id,url){
 card.querySelector(".journey-photo-credit")?.remove();
 if(sport!=="mlb")return;
 const r=portraitFallbacks[id];
 if(!r||r.url!==url)return;
 const safe=u=>typeof u==="string"&&/^https:\/\/[^\s"'<>]+$/.test(u);
 const small=document.createElement("small");small.className="journey-photo-credit";
 const link=(label,href)=>{const a=document.createElement("a");a.href=href;a.target="_blank";a.rel="noopener noreferrer";a.textContent=label;return a};
 if(["historical","official"].includes(r.provider)&&safe(r.source)){small.append(link("Photo source",r.source))}
 else if(r.provider==="commons"&&/^https:\/\/commons\.wikimedia\.org\/wiki\/File:/.test(r.source||"")&&/^https:\/\/(creativecommons\.org|commons\.wikimedia\.org)\//.test(r.license_url||"")){small.append("Photo: ",link(r.author||"Wikimedia Commons",r.source)," · ",link(r.license||"License",r.license_url))}
 if(small.childNodes.length)card.querySelector(".card-top,.multi-card-top")?.after(small);
}
function decorate(){
 for(const anchor of directory.querySelectorAll("a.player-name:not([data-journey-portrait])")){
  const id=new URL(anchor.href,location.href).searchParams.get("id");if(!id)continue;
  const name=anchor.textContent.trim();anchor.dataset.journeyPortrait=id;
  const frame=document.createElement("span");frame.className="journey-portrait";frame.setAttribute("aria-hidden","true");
  const fallback=document.createElement("span");fallback.className="journey-initials";fallback.textContent=name.split(/\s+/).filter(Boolean).slice(0,2).map(s=>s[0]).join("").toUpperCase();
  const label=document.createElement("span");label.className="journey-player-label";label.textContent=name;
  frame.append(fallback);anchor.replaceChildren(frame,label);
  const urls=[...new Set(candidates(id).filter(Boolean))];
  const card=anchor.closest("article");
  if(!urls.length)continue;
  const img=document.createElement("img");img.className="journey-headshot";img.alt="";img.loading="lazy";img.decoding="async";
  let index=0;
  const next=()=>{frame.classList.remove("has-portrait");if(index>=urls.length){img.remove();return}img.src=urls[index++]};
  img.addEventListener("load",()=>{if(img.naturalWidth<=1||img.naturalHeight<=1){next();return}frame.classList.add("has-portrait");if(card)credit(card,id,img.currentSrc||img.src)});
  img.addEventListener("error",next);
  frame.append(img);next();
 }
}
async function init(){
 if(sport==="college")headshots=(await read("./data/player_headshots.json")).players||{};
 if(sport==="mlb")portraitFallbacks=await read("./data/player_portrait_fallbacks.json");
 if(sport==="college-baseball"){
  const [registry,archive]=await Promise.all([read("./data/player_portraits.json"),window.CollegeBaseballArchive?.load().catch(()=>null)]);
  baseballPortraits=registry;
  for(const r of archive?.rows||[]){const id=String(r.player_id);if(!baseballRows.has(id))baseballRows.set(id,[]);baseballRows.get(id).push(r)}
 }
 // Observe only the directory; search and sort recreate cards. Decorating a card is idempotent.
 new MutationObserver(decorate).observe(directory,{childList:true,subtree:true});
 decorate();
}
init().catch(err=>console.warn("Journey portraits unavailable",err));
})();