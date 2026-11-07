/* Verified College Baseball + MiLB + MLB attendance crossover gallery. */
document.addEventListener("DOMContentLoaded",async()=>{
 "use strict";
 const app=document.getElementById("app");
 const A=window.MLBArchive;
 document.getElementById("navigation").innerHTML=A.nav("three-level");
 const esc=A.esc;
 const get=async path=>{
  const response=await fetch(path,{cache:"no-store"});
  if(!response.ok)throw Error("Unable to load verified attendance registry");
  const data=await response.json();
  if(!Array.isArray(data))throw Error("Invalid attendance registry");
  return data;
 };
 try{
  const [mlb,collegeMiLB,miMLB,collegeMLB]=await Promise.all([
   A.load(),get("../milb/data/college_links.json"),get("../milb/data/player_links.json"),
   get("../college-baseball/data/mlb_crosswalk.json")
  ]);
  const professional=new Map(miMLB.filter(x=>x.verified===true&&x.mlb_seen===true&&x.mlb_debut&&x.milb_id!=null)
   .map(x=>[String(x.milb_id),x]));
  const collegePros=new Set(collegeMLB.filter(x=>x.verified===true&&x.college_player_id&&x.mlb_player_id!=null)
   .map(x=>String(x.college_player_id)+"|"+String(x.mlb_player_id)));
  const witnessedMLB=new Map(mlb.players.map(p=>[String(p.player_id),p]));
  const eligible=collegeMiLB.filter(x=>{
   const pro=professional.get(String(x.milb_id));
   return x.verified===true&&x.college_player_id&&pro&&
    String(pro.mlb_id)===String(x.milb_id)&&
    collegePros.has(String(x.college_player_id)+"|"+String(pro.mlb_id))&&
    witnessedMLB.has(String(pro.mlb_id));
  }).map(x=>({link:x,pro:professional.get(String(x.milb_id)),mlb:witnessedMLB.get(String(x.milb_id))}))
   .sort((a,b)=>a.link.name.localeCompare(b.link.name));
  const cards=eligible.map(({link,pro,mlb:p})=>{
   const initials=String(link.name).split(/\s+/).map(n=>n[0]).slice(0,2).join("").toUpperCase();
   return '<article class="triple-player-card">'
    +'<div class="triple-player-head"><div class="triple-initials" aria-hidden="true">'+esc(initials)+'</div>'
    +'<div><span class="triple-achievement">★ SEEN IN COLLEGE + MiLB + MLB</span><h2>'+esc(link.name)+'</h2><p>'+esc((link.college_schools||[]).join(" / "))+'</p></div></div>'
    +'<div class="triple-journey" aria-label="Three-level journey"><span>COLLEGE</span><b>→</b><span>MiLB</span><b>→</b><span>MLB</span></div>'
    +'<div class="triple-player-details"><div><small>College program(s)</small><strong>'+esc((link.college_schools||[]).join(" / ")||"Verified college attendee")+'</strong></div>'
    +'<div><small>First MiLB game attended</small><strong>'+esc(pro.first_attended_milb||"See player profile")+'</strong></div>'
    +'<div><small>MLB games attended</small><strong>'+A.fmt(p.game_count)+'</strong></div></div>'
    +'<div class="triple-player-links"><a href="../college-baseball/player.html?id='+encodeURIComponent(link.college_player_id)+'">College profile ↗</a>'
    +'<a href="../milb/player.html?id='+encodeURIComponent(link.milb_id)+'">MiLB profile ↗</a>'
    +'<a href="./player.html?id='+encodeURIComponent(pro.mlb_id)+'">MLB profile ↗</a></div></article>';
  }).join("");
  app.innerHTML='<section class="triple-hero"><div class="triple-eyebrow">COURTSIDE ARCHIVE · MLB</div>'
   +'<h1>The Three-Level Club.</h1>'
   +'<p>A rare personal baseball milestone: players you witnessed compete in <strong>college baseball</strong>, <strong>Minor League Baseball</strong>, and <strong>Major League Baseball</strong>.</p>'
   +'<div class="triple-hero-bottom"><span class="triple-count">'+eligible.length+'</span><span>verified three-level player'+(eligible.length===1?'':'s')+'<small>Every level is backed by an attended game and a confirmed player identity.</small></span></div></section>'
   +'<div class="triple-section-heading"><h2>Members of the club</h2><p>The list updates as new verified crossover records are added to the archives.</p></div>'
   +(eligible.length?'<div class="triple-player-grid">'+cards+'</div>':'<div class="empty">No player has a fully verified three-level attendance journey yet.</div>')
   +'<p class="triple-method">Eligibility requires a verified college-to-MiLB identity link, an MLB debut with an attended MLB game, and a matching college-to-MLB identity record. Similar names alone never qualify.</p>';
 }catch(error){
  app.innerHTML='<section class="empty">Unable to load the verified Three-Level Club: '+esc(error.message)+'</section>';
 }
});
