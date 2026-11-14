import assert from 'node:assert/strict';
import fs from 'node:fs';
import path from 'node:path';

const repo=path.resolve(import.meta.dirname,'../..');
const file=path.join(repo,'venues/data/venues.json');
const data=JSON.parse(fs.readFileSync(file,'utf8'));
const venues=data.venues;
const photos=JSON.parse(fs.readFileSync(path.join(repo,'venues/data/photos.json'),'utf8')).photos;
const games=JSON.parse(fs.readFileSync(path.join(repo,'milb/data/games.json'),'utf8'));
assert.equal(data.venueCount,venues.length);
assert.ok(venues.length>=141);
assert.equal(data.mappedGames,venues.reduce((sum,v)=>sum+v.games.length,0));
assert.equal(data.excludedUnassignedGames,7);
assert.equal(new Set(venues.map(v=>v.id)).size,venues.length);
assert.equal(new Set(venues.map(v=>v.name)).size,venues.length);
assert.equal(new Set(venues.map(v=>v.sport)).size,8);
const expected={'College Baseball':84,'College Basketball':21,'MLB':18,'College Football':3,'NBA':2,'NFL':2,'Soccer':2};
const venueSports=v=>Array.isArray(v.sports)&&v.sports.length?v.sports:[v.sport];
assert.ok(venues.filter(v=>venueSports(v).includes('MiLB')).length>=4);
for(const [sport,count] of Object.entries(expected))assert.equal(venues.filter(v=>v.sport===sport).length,count,sport);
for(const [id,photo] of Object.entries(photos)){
 assert.ok(venues.some(v=>v.id===id),id+': photo venue missing');
 assert.ok(photo.alt&&photo.credit,id+': photo metadata incomplete');
 assert.ok(/^[a-z0-9-]+\.(?:jpeg|jpg|png|webp)$/.test(photo.file),id+': unsafe photo filename');
 const asset=path.join(repo,'venues/photos',photo.file);
 assert.ok(fs.existsSync(asset),id+': photo asset missing');
 assert.ok(fs.statSync(asset).size>500,id+': photo asset unexpectedly small');
}
let total=0;
for(const v of venues){
 assert.ok(v.name&&v.city&&v.address&&v.occupants&&v.history&&v.opened&&v.capacity,v.id);
 assert.ok(Number.isFinite(v.lat)&&v.lat>=-90&&v.lat<=90&&Number.isFinite(v.lon)&&v.lon>=-180&&v.lon<=180,v.name);
 assert.equal(v.games.length,v.visits,v.name);
 assert.equal(v.games[0].date,v.firstVisit,v.name);
 assert.equal(v.games.at(-1).date,v.lastVisit,v.name);
 for(const g of v.games){
  assert.ok(/^\d{4}-\d{2}-\d{2}$/.test(g.date),g.id);
  assert.ok(g.away&&g.home&&g.url,g.id);
  const url=new URL(g.url,'https://courtside.example/venues/venue.html');
  assert.ok(fs.existsSync(path.join(repo,url.pathname.slice(1))),g.id+': missing game detail page');
  assert.equal(url.searchParams.get('id'),g.id,g.id);
 }
 total+=v.visits;
}
assert.equal(total,data.mappedGames);
const milbVenues=venues.filter(v=>venueSports(v).includes('MiLB'));
const counts={'venue-0131':1,'venue-0132':1,'venue-0133':7,'venue-0134':1,'venue-0005':7};
assert.ok(milbVenues.length>=4);
assert.ok(games.length>=10);
const seen=new Set();
for(const v of milbVenues){
 assert.ok(v.visits>=(counts[v.id]??1));
 for(const vg of v.games){
  if(!vg.id.startsWith('milb-'))continue; // Shared stadium also contains college game records.
  const game=games.find(g=>g.id===vg.id);
  assert.ok(game,'Orphan MiLB game '+vg.id);
  assert.equal(game.venue_id,v.id,vg.id);
  assert.equal(game.date,vg.date,vg.id);
  assert.equal(game.away_team,vg.away,vg.id);
  assert.equal(game.home_team,vg.home,vg.id);
  assert.equal(game.away_score,vg.awayScore,vg.id);
  assert.equal(game.home_score,vg.homeScore,vg.id);
  assert.equal(vg.url,'../milb/game.html?id='+encodeURIComponent(vg.id));
  assert.ok(!seen.has(vg.id),'MiLB game linked to multiple venues '+vg.id);
  seen.add(vg.id);
 }
}
assert.equal(seen.size,games.length);
assert.ok(venues.some(v=>v.id==='venue-0005'&&v.name==='Banner Island Ballpark'));
const allen=venues.find(v=>v.name==='Allen Arena');
assert.ok(allen&&allen.sport==='College Basketball'&&allen.firstVisit==='2026-11-07');
assert.ok(allen.games.some(g=>g.id==='96'&&g.awayScore===77&&g.homeScore===78));
assert.equal(venues.filter(v=>v.name==='Banner Island Ballpark').length,1);
if(games.length>10){
 const venue=venues.find(v=>v.id==='venue-0005');
 assert.ok(venueSports(venue).includes('MiLB'));
 assert.ok(venue.games.some(g=>g.id.startsWith('cb-')));
 assert.ok(venue.games.some(g=>g.id.startsWith('milb-')));
}
const richmond=venues.find(v=>v.name==='The Diamond');
assert.ok(richmond&&richmond.city.startsWith('Richmond'));
assert.notEqual(richmond.id,'venue-0133');
const home=fs.readFileSync(path.join(repo,'index.html'),'utf8');
const directory=fs.readFileSync(path.join(repo,'venues/index.html'),'utf8');
const mapJS=fs.readFileSync(path.join(repo,'assets/venue-map.js'),'utf8');
const directoryJS=fs.readFileSync(path.join(repo,'venues/venues.js'),'utf8');
const gamesJS=fs.readFileSync(path.join(repo,'milb/assets/games.js'),'utf8');
assert.ok(home.indexOf('id="venues"')>home.indexOf('class="portal-hero"'));
assert.ok(home.indexOf('id="venues"')<home.indexOf('id="archives"'));
assert.ok(home.includes('id="venueCount">'+data.venueCount));
assert.ok(home.includes('id="venueSportCount">9'));
assert.ok(home.includes('id="venueGameCount">'+data.mappedGames));
assert.ok(directory.includes(data.venueCount+' physical stadiums'));
assert.ok(directory.includes('nine sports'));
assert.ok(mapJS.includes("'MiLB':'#831738'"));
assert.ok(directoryJS.includes("'MiLB':'../milb/'"));
assert.ok(gamesJS.includes('../venues/venue.html?id='));
console.log('PASS: '+data.venueCount+' venues, '+data.mappedGames+' linked games, nine sports, '+milbVenues.length+' MiLB ballparks, '+games.length+' linked MiLB games');
