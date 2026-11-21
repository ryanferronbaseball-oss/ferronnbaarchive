/* Future MLB draftees witnessed in college. Uses the same verified draft tags as the player profiles. */
(()=>{
"use strict";
const $=id=>document.getElementById(id);
const esc=v=>String(v??"").replace(/[&<>"']/g,c=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[c]));
let picks=[];
function draw(){
 const query=$("futureDraftSearch").value.trim().toLowerCase();
 const years=picks.filter(p=>[p.name,p.draft_year,p.draft_round,p.draft_pick,p.draft_team].join(" ").toLowerCase().includes(query))
  .reduce((groups,p)=>{(groups[p.draft_year]??=[]).push(p);return groups},{});
 const order=Object.keys(years).map(Number).sort((a,b)=>a-b);
 const total=order.reduce((n,y)=>n+years[y].length,0);
 $("futureDraftCount").textContent=total.toLocaleString("en-US")+" of "+picks.length.toLocaleString("en-US")+" MLB draftees";
 $("futureDraftYears").innerHTML=order.length?order.map(y=>{
  const rows=years[y].sort((a,b)=>Number(a.draft_pick)-Number(b.draft_pick)||a.name.localeCompare(b.name));
  return '<section class="future-draft-year" aria-label="'+y+' MLB Draft"><h3>'+y+' MLB Draft <span>'+rows.length+' players</span></h3><div class="future-draft-table-wrap"><table class="future-draft-table"><thead><tr><th scope="col">Overall pick</th><th scope="col">Player</th><th scope="col">Round</th><th scope="col">Drafted by</th></tr></thead><tbody>'+rows.map(p=>'<tr><td class="future-draft-pick">#'+Number(p.draft_pick).toLocaleString("en-US")+'</td><td><a href="./player.html?id='+encodeURIComponent(p.college_player_id)+'">'+esc(p.name)+'</a></td><td>'+esc(p.draft_round)+'</td><td>'+esc(p.draft_team)+'</td></tr>').join("")+'</tbody></table></div></section>';
 }).join(""):'<p class="alumni-empty">No matching draftees.</p>';
}
async function init(){
 try{
  const response=await fetch("./data/draft_profile_tags.json",{cache:"no-store"});
  if(!response.ok)throw Error("Draft tags unavailable");
  const registry=await response.json();
  if(!Array.isArray(registry.picks))throw Error("Invalid draft tag registry");
  const seen=new Set();
  picks=registry.picks.filter(p=>{
   if(!p.college_player_id||!p.name||!Number.isInteger(Number(p.draft_year))||!Number.isInteger(Number(p.draft_pick))||!p.draft_team)return false;
   if(seen.has(p.college_player_id))return false;seen.add(p.college_player_id);return true;
  });
  $("futureDraftSummary").textContent=picks.length.toLocaleString("en-US")+" draft selections across "+new Set(picks.map(p=>p.draft_year)).size+" draft classes, pulled from the verified draft tags on college player profiles.";
  draw();
 }catch(error){
  $("futureDraftCount").textContent="Draft registry unavailable";
  $("futureDraftYears").innerHTML='<p class="alumni-empty">The draft list could not be loaded. Other MLB alumni records are unaffected.</p>';
  console.warn("Future draftees",error);
 }
}
$("futureDraftSearch").addEventListener("input",draw);
if(document.readyState==="loading")document.addEventListener("DOMContentLoaded",init,{once:true});else init();
})();