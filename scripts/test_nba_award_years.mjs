// Player-year award details must exactly reconcile to reviewed badge counts.
import assert from "node:assert/strict";
import fs from "node:fs";
import path from "node:path";
import vm from "node:vm";
import { fileURLToPath } from "node:url";

const root=path.resolve(path.dirname(fileURLToPath(import.meta.url)),"..");
const read=filename=>JSON.parse(fs.readFileSync(path.join(root,"data",filename),"utf8"));
const years=read("nba_award_years.json"),titles=read("nba_championships.json"),awards=read("nba_career_awards.json"),olympics=read("nba_olympic_representation.json");
const boxscores=read("player_boxscores_espn.json");
const known=new Set(boxscores.map(p=>p.player_id.replace(/^espn:/,"")));
for(const id of Object.keys(years.players))assert(known.has(id),`Unknown player ID ${id}`);

const testYearRecords=(arr,format)=>{
  assert(Array.isArray(arr)&&arr.length>0);
  const values=arr.map(r=>typeof r==="number"?r:r.season);
  assert.equal(new Set(values).size,values.length,"Duplicate year in award history");
  for(const v of values)assert(format.test(String(v)),`Invalid award year ${v}`);
};

for(const [id,player] of Object.entries(titles.players)){
  const rows=years.players[id]?.championships;
  assert.equal(rows?.length,player.championships,`${player.name} championship years`);
  testYearRecords(rows,/^\d{4}$/);
}
for(const [id,player] of Object.entries(awards.players)){
  for(const [key,flag] of [["mvp","mvp"],["all_nba","all_nba"],["all_star","all_star"]]){
    if(!player[flag])continue;
    const rows=years.players[id]?.[key];
    assert(rows,`${player.name} missing ${key} years`);
    testYearRecords(rows,key==="all_star"?/^\d{4}$/:/^\d{4}-\d{2}$/);
    const count=key==="all_star"?player.all_star:player[key+"_count"];
    if(Number.isInteger(count))assert.equal(rows.length,count,`${player.name} ${key} count`);
    if(key==="all_nba")for(const row of rows)assert(["First Team","Second Team","Third Team"].includes(row.selection));
  }
}
assert.deepEqual(years._meta.unreconciled_championships,[]);
assert.deepEqual(years._meta.unreconciled_awards,[]);
assert.deepEqual(years._meta.counts,{championships:91,mvp:11,all_nba:51,all_star:49});

assert.deepEqual(years.players["110"].championships,[2000,2001,2002,2009,2010],"Kobe title years");
assert.deepEqual(years.players["614"].championships,[2000,2001,2002,2006],"Shaq title years");
assert.deepEqual(years.players["1966"].championships,[2012,2013,2016,2020],"LeBron title years");
assert.deepEqual(years.players["138"].championships,[1994,1995,2008],"Exclude Sam Cassell coaching ring (2024)");
assert.deepEqual(years.players["2166"].championships,[2015],"Exclude Leandro Barbosa coaching ring (2022)");
assert.equal(years.players["3992"].all_nba.length,8,"James Harden's 2025 All-NBA return");
assert(years.players["3992"].all_nba.some(r=>r.season==="2024-25"));
assert.equal(years.players["110"].all_star.length,18,"Kobe All-Star selections including missed games");
assert.deepEqual(years.players["25"].all_star,[2004],"Ron Artest/Metta World Peace identity");

const page=fs.readFileSync(path.join(root,"nba/player.html"),"utf8");
const hallPage=fs.readFileSync(path.join(root,"nba/hall-of-fame.html"),"utf8");
const hallRoster=JSON.parse(hallPage.match(/const members=(\[[^;]+\]);/)?.[1]||"[]");
for(const [id,name,year] of hallRoster)assert(page.includes(`"${id}":${year}`),`Hall-of-Fame induction year mismatch for ${name}`);
const inline=page.match(/<script src="\.\.\/assets\/site\.js[^>]*><\/script><script>([\s\S]*?)<\/script>/)?.[1];
assert(inline);
new vm.Script(inline,{filename:"nba/player.html"});
assert(page.includes("nba_award_years.json?v=years-20261101"));

const begin=page.indexOf("function renderCareerHonors("),end=page.indexOf("\nif(id){",begin);
assert(begin>0&&end>begin);
const elements=new Map(),makeElement=()=>({
  classList:{seen:new Set(),add(s){this.seen.add(s)},contains(s){return this.seen.has(s)}},
  innerHTML:"",textContent:"",style:{},hidden:true,title:"",tabIndex:-1,
  addEventListener(){},setAttribute(){},querySelectorAll(){return []},scrollIntoView(){}
});
const get=id=>{if(!elements.has(id))elements.set(id,makeElement());return elements.get(id)};
const document={getElementById:get,querySelector:s=>s===".accolade-row"?get("row"):null};
const esc=v=>String(v??"").replace(/[&<>"']/g,c=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[c]));
const ctx={document,esc,$:get};
vm.runInNewContext(page.slice(begin,end),ctx);
ctx.renderCareerHonors({...awards.players["110"],...titles.players["110"]},years.players["110"],olympics.players["110"],olympics.countries,2020);
let details=get("honorDetails").innerHTML;
assert.match(details,/2000<\/li>/);
assert.match(details,/2010<\/li>/);
assert.match(details,/2007-08/);
assert.match(details,/First Team/);
assert.match(details,/1998<\/li>/);
assert.match(details,/2008 · 5-on-5 basketball/);
assert.match(details,/Basketball Hall of Fame in 2020/);
assert.match(get("championBadge").title,/2000, 2001, 2002, 2009, 2010/);
assert.equal(get("olympicBadge").tabIndex,0);
assert(get("olympicBadge").classList.contains("visible"));
elements.clear();
ctx.renderCareerHonors({...awards.players["3992"]},years.players["3992"]);
assert.match(get("honorDetails").innerHTML,/2024-25/);
assert.match(get("allNbaBadge").textContent,/· 8/);

console.log("PASS 91 championships, 11 MVPs, 51 All-NBA and 49 All-Star year histories with clickable detail rendering");
