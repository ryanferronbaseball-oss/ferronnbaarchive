import assert from 'node:assert/strict';
import fs from 'node:fs';
import path from 'node:path';

const repo=path.resolve(import.meta.dirname,'../..');
const file=path.join(repo,'venues/data/venues.json');
const data=JSON.parse(fs.readFileSync(file,'utf8'));
const venues=data.venues;
const photos=JSON.parse(fs.readFileSync(path.join(repo,'venues/data/photos.json'),'utf8')).photos;
assert.equal(data.venueCount,129);
assert.equal(venues.length,129);
assert.equal(data.mappedGames,705);
assert.equal(data.excludedUnassignedGames,7);
assert.equal(new Set(venues.map(v=>v.id)).size,129);
assert.equal(new Set(venues.map(v=>v.name)).size,129);
assert.equal(new Set(venues.map(v=>v.sport)).size,7);
assert.equal(Object.keys(photos).length,6);
for(const [id,photo] of Object.entries(photos)){
  assert.ok(venues.some(v=>v.id===id),`${id}: photo venue missing`);
  assert.ok(photo.alt&&photo.credit,`${id}: photo metadata incomplete`);
  assert.ok(/^[a-z0-9-]+\.jpeg$/.test(photo.file),`${id}: photo filename is not safe`);
  const asset=path.join(repo,'venues/photos',photo.file);
  assert.ok(fs.existsSync(asset),`${id}: photo asset missing`);
  assert.ok(fs.statSync(asset).size>100_000,`${id}: photo asset unexpectedly small`);
}
const expected={'College Baseball':84,'College Basketball':18,'MLB':18,'College Football':3,'NBA':2,'NFL':2,'Soccer':2};
for(const [sport,count] of Object.entries(expected))assert.equal(venues.filter(v=>v.sport===sport).length,count);
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
    assert.ok(fs.existsSync(path.join(repo,url.pathname.slice(1))),`${g.id}: missing game detail page`);
    assert.equal(url.searchParams.get('id'),g.id,g.id);
  }
  total+=v.visits;
}
assert.equal(total,705);
assert.equal(venues.filter(v=>v.opened.startsWith('Original')).length,2);
const home=fs.readFileSync(path.join(repo,'index.html'),'utf8');
assert.ok(home.indexOf('id="venues"')>home.indexOf('class="portal-hero"'));
assert.ok(home.indexOf('id="venues"')<home.indexOf('id="archives"'));
assert.ok(home.includes('assets/venue-map.js'));
console.log('PASS: 129 venues, 705 source game links, seven sports, 2 qualified opening dates, homepage map placement');
