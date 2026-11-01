// NBA career-award and legacy-tag data integrity and profile rendering checks.
import assert from "node:assert/strict";
import fs from "node:fs";
import path from "node:path";
import vm from "node:vm";
import { fileURLToPath } from "node:url";

const root=path.resolve(path.dirname(fileURLToPath(import.meta.url)),"..");
const legacy=JSON.parse(fs.readFileSync(path.join(root,"data/nba_legacy_honors.json"),"utf8"));
const games=JSON.parse(fs.readFileSync(path.join(root,"data/player_boxscores_espn.json"),"utf8"));
const names=new Map(games.map(p=>[p.player_id.replace(/^espn:/,""),p.player]));
const awardKeys=["finals_mvp","dpoy","all_defensive","rookie","sixth","improved"];
const allKeys=[...awardKeys,"nba75","retired_jersey"];

assert.equal(legacy._meta.matched_player_count,Object.keys(legacy.players).length);
for(const [id,player] of Object.entries(legacy.players)){
  assert.equal(names.get(id),player.name,`ESPN identity mismatch: ${id}`);
  for(const key of awardKeys){
    if(!(key in player))continue;
    const values=player[key];
    assert(Array.isArray(values)&&values.length>0,`${id} ${key}: must have award seasons`);
    assert.equal(new Set(values.map(v=>v.season)).size,values.length,`${id} ${key}: duplicated season`);
    for(const value of values){
      assert(/^\d{4}-\d{2}$/.test(value.season),`${id} ${key}: invalid season`);
      if(key==="all_defensive")assert(["First Team","Second Team"].includes(value.selection));
    }
  }
  if(player.nba75!==undefined)assert.equal(player.nba75,true);
  if(player.retired_jersey){
    assert(player.retired_jersey.length>0);
    for(const value of player.retired_jersey){
      assert(value.team&&value.number&&Number.isInteger(value.year)&&value.year<=2026);
    }
    assert.equal(new Set(player.retired_jersey.map(r=>r.team+":"+r.number)).size,player.retired_jersey.length,`${id}: duplicate retirement`);
  }
}
for(const key of allKeys)assert.equal(Object.values(legacy.players).filter(p=>p[key]).length,legacy._meta.category_counts[key],`${key} count`);

assert.equal(legacy.players["110"].finals_mvp.length,2,"Kobe's Finals MVPs");
assert.equal(legacy.players["110"].all_defensive.length,12,"Kobe's All-Defensive teams");
assert.equal(legacy.players["215"].all_defensive.length,15,"Duncan's All-Defensive teams");
assert.equal(legacy.players["1966"].finals_mvp.length,4,"LeBron's Finals MVPs");
assert.equal(legacy.players["885"].dpoy.length,4,"Ben Wallace's DPOYs");
assert.equal(legacy.players["2384"].dpoy.length,3,"Dwight Howard's DPOYs");
assert.equal(legacy.players["2799"].sixth.length,3,"Lou Williams' Sixth Man awards");
assert.equal(legacy.players["165"].sixth.length,3,"Jamal Crawford's Sixth Man awards");
assert.equal(legacy.players["336"].rookie[0].season,"1994-95","Grant Hill co-Rookie of the Year");
assert(legacy.players["614"].nba75,"Shaq belongs to NBA 75");
assert.equal(legacy.players["614"].retired_jersey.length,3,"Shaq's three NBA jersey retirements");
assert.equal(legacy.players["2184"].retired_jersey[0].number,"40","Udonis Haslem's retirement");
assert.equal(legacy.players["136"].retired_jersey.find(x=>x.team==="Brooklyn Nets")?.year,2025,"Vince Carter's Nets ceremony year");
assert(!legacy.players["592"]?.finals_mvp,"Steve Nash is not a Finals MVP");

const page=fs.readFileSync(path.join(root,"nba/player.html"),"utf8");
const script=page.match(/<script src="\.\.\/assets\/site\.js[^>]*><\/script><script>([\s\S]*?)<\/script>/)?.[1];
assert(script,"NBA profile inline script found");
new vm.Script(script,{filename:"nba/player.html"});
assert(page.includes("nba_legacy_honors.json?v=legacy-20261101"),"Profile fetches reviewed legacy awards");
for(const id of ["finalsMvpBadge","dpoyBadge","allDefenseBadge","rookieBadge","sixthBadge","improvedBadge","nba75Badge","retiredBadge"])
  assert(page.includes(`id="${id}"`),`Missing badge ${id}`);

const start=page.indexOf("function renderCareerHonors(awards){"),end=page.indexOf("\nif(id){",start);
assert(start>=0&&end>start);
const elements=new Map(),makeElement=()=>({
  classList:{values:new Set(),add(x){this.values.add(x)},contains(x){return this.values.has(x)}},
  innerHTML:"",textContent:"",title:"",style:{},hidden:true,
  addEventListener(){},querySelectorAll(){return []},scrollIntoView(){}
});
const getElement=id=>{if(!elements.has(id))elements.set(id,makeElement());return elements.get(id)};
const document={getElementById:getElement,querySelector:s=>s===".accolade-row"?getElement("accoladeRow"):null};
const esc=v=>String(v??"").replace(/[&<>"']/g,c=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[c]));
const ctx={document,esc,$:getElement};
vm.runInNewContext(page.slice(start,end),ctx);

ctx.renderCareerHonors(legacy.players["110"]);
assert.equal(getElement("finalsMvpBadge").textContent,"🏆 FINALS MVP · 2");
assert.equal(getElement("allDefenseBadge").textContent,"🛡️ ALL-DEFENSE · 12");
assert.equal(getElement("nba75Badge").textContent,"★ NBA 75");
assert.equal(getElement("retiredBadge").textContent,"🎽 JERSEY RETIRED · 1");
assert.match(getElement("honorDetails").innerHTML,/2008-09/);
assert.equal(getElement("careerHonors").hidden,false);
elements.clear();
ctx.renderCareerHonors(legacy.players["614"]);
assert.equal(getElement("retiredBadge").textContent,"🎽 JERSEY RETIRED · 3");
assert.match(getElement("honorDetails").innerHTML,/Orlando Magic · #32 · 2024/);
elements.clear();
ctx.renderCareerHonors(legacy.players["2799"]);
assert.equal(getElement("sixthBadge").textContent,"⚡ SIXTH MAN · 3");
assert(!getElement("nba75Badge").classList.contains("visible"));
elements.clear();
ctx.renderCareerHonors({});
assert(!getElement("accoladeRow").classList.contains("visible"),"Don't show empty honor badges");

console.log(`PASS ${Object.keys(legacy.players).length} reviewed player identities, 8 honors categories, and profile badges`);
