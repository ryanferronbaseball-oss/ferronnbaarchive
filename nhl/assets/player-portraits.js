(()=>{"use strict";
const id=new URLSearchParams(location.search).get("id");
if(!id)return;
async function init(){
 let records={};try{const r=await fetch("./data/player_portraits.json",{cache:"no-store"});if(r.ok)records=await r.json()}catch{}
 const record=records[id];
 function decorate(){
  const frame=document.querySelector(".nhl-player-portrait");const name=document.querySelector(".nhl-player-hero h1")?.textContent?.trim();
  if(!frame||!name||frame.dataset.portraitReady)return;
  frame.dataset.portraitReady="true";
  const fallback=document.createElement("span");fallback.textContent=name.split(/\s+/).slice(0,2).map(s=>s[0]).join("").toUpperCase();
  frame.replaceChildren(fallback);frame.removeAttribute("aria-hidden");frame.setAttribute("aria-label","Portrait of "+name);
  if(!record?.url||!/^https:\/\/assets\.nhle\.com\/mugs\/nhl\//.test(record.url))return;
  const img=document.createElement("img");img.alt="Portrait of "+name;img.decoding="async";
  img.addEventListener("load",()=>{if(img.naturalWidth>1&&img.naturalHeight>1){frame.classList.add("has-portrait");fallback.hidden=true}});
  img.addEventListener("error",()=>img.remove());frame.append(img);img.src=record.url;
 }
 new MutationObserver(decorate).observe(document.body,{childList:true,subtree:true});decorate();
}
init();
})();