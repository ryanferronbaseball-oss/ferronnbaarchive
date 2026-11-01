// Championship badge and source-identity regression checks.
import assert from "node:assert/strict";
import fs from "node:fs";
import path from "node:path";
import vm from "node:vm";
import { fileURLToPath } from "node:url";

const root=path.resolve(path.dirname(fileURLToPath(import.meta.url)),"..");
const titles=JSON.parse(fs.readFileSync(path.join(root,"data/nba_championships.json"),"utf8"));
const boxscores=JSON.parse(fs.readFileSync(path.join(root,"data/player_boxscores_espn.json"),"utf8"));
const archiveNames=new Map(boxscores.map(p=>[p.player_id.replace(/^espn:/,""),p.player.trim()]));
const awardData=JSON.parse(fs.readFileSync(path.join(root,"data/nba_career_awards.json"),"utf8"));
const champions=Object.entries(titles.players);
assert.equal(champions.length,91);
assert.equal(titles._meta.reviewed_players,91);
for(const [id,player] of champions){
  assert.equal(archiveNames.get(id),player.name,`Player ID mismatch: ${id}`);
  assert(Number.isInteger(player.championships)&&player.championships>0,`Invalid title count: ${id}`);
}
for(const [id,count] of Object.entries({"347":7,"110":5,"215":5,"1966":4,"2450":2,"3112335":1,"3936299":1,"3442":1,"3449":1,"3213":1,"2528426":1}))
  assert.equal(titles.players[id].championships,count,`Incorrect count for ${id}`);
assert(!titles.players["592"],"Steve Nash must not have a championship badge");

const page=fs.readFileSync(path.join(root,"nba/player.html"),"utf8");
const inlineScript=page.match(/<script src="\.\.\/assets\/site\.js[^>]*><\/script><script>([\s\S]*?)<\/script>/)?.[1];
assert(inlineScript,"NBA profile inline script found");
new vm.Script(inlineScript,{filename:"nba/player.html"});
const start=page.indexOf("function renderCareerHonors(awards){"),end=page.indexOf("\nif(id){",start);
assert(start>=0&&end>start,"Career honors renderer found");
const elements=new Map(),makeElement=()=>({
  classList:{values:new Set(),add(x){this.values.add(x)},contains(x){return this.values.has(x)}},
  innerHTML:"",textContent:"",style:{},hidden:true,
  addEventListener(){},querySelectorAll(){return []},scrollIntoView(){}
});
const getElement=id=>{if(!elements.has(id))elements.set(id,makeElement());return elements.get(id)};
const document={getElementById:getElement,querySelector:selector=>selector===".accolade-row"?getElement("accoladeRow"):null};
const esc=v=>String(v??"").replace(/[&<>"']/g,c=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[c]));
const ctx={document,esc,$:getElement};
vm.runInNewContext(page.slice(start,end),ctx);
ctx.renderCareerHonors({...awardData.players["110"],championships:titles.players["110"].championships});
assert.equal(getElement("championBadge").textContent,"🏆 NBA CHAMPION · 5");
assert(getElement("championBadge").classList.contains("visible"));
assert.match(getElement("honorDetails").innerHTML,/5 career NBA championships/);
assert(getElement("mvpBadge").classList.contains("visible"),"Existing MVP badge remains");
assert(getElement("allNbaBadge").classList.contains("visible"),"Existing All-NBA badge remains");
elements.clear();
ctx.renderCareerHonors({championships:titles.players["2528426"].championships});
assert.equal(getElement("championBadge").textContent,"🏆 NBA CHAMPION · 1");
assert.match(getElement("honorDetails").innerHTML,/1 career NBA championship\./);
assert.equal(getElement("careerHonors").hidden,false,"Championship-only players show career honors");
elements.clear();
ctx.renderCareerHonors({championships:0});
assert.equal(getElement("championBadge").classList.contains("visible"),false,"No badge for non-champions");
console.log("PASS 91 championship counts, archive IDs, existing awards, and badge rendering");
