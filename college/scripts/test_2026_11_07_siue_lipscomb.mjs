import assert from 'node:assert/strict';
import fs from 'node:fs';
import path from 'node:path';
import {fileURLToPath} from 'node:url';

const root=path.resolve(path.dirname(fileURLToPath(import.meta.url)),'../..');
const read=p=>fs.readFileSync(path.join(root,p),'utf8');
const csv=(p)=>{const [header,...rows]=read(p).trim().split(/\r?\n/);const keys=header.split(',');return rows.map(line=>Object.fromEntries(line.split(',').map((v,i)=>[keys[i],v])));};
const games=csv('college/data/games.csv'), attendance=csv('college/data/attendance.csv');
const sources=csv('college/data/verified_venues.csv');
const players=JSON.parse(read('college/data/player_boxscores_espn.json'));
const names=JSON.parse(read('college/data/team_names.json'));
const headshots=JSON.parse(read('college/data/player_headshots.json')).players;
const awards=JSON.parse(read('college/data/career_tags_high_priority.json')).players;
const venueData=JSON.parse(read('venues/data/venues.json'));

const g=games.find(x=>x.id==='96');
assert.ok(g,'Newly attended game missing');
assert.deepEqual([g.date,g.away,g.home,g.arena,g.espn_event_id,g.away_score,g.home_score,g.away_team_id,g.home_team_id,g.boxscore_status,g.site_type],
 ['2026-11-07','SIU Edwardsville','Lipscomb','Allen Arena','401920703','77','78','2565','288','complete','home']);
assert.equal(games.filter(x=>x.espn_event_id==='401920703').length,1);
assert.equal(attendance.filter(x=>x.attendance_id==='96').length,1);
assert.equal(sources.filter(x=>x.attendance_id==='96'&&x.arena==='Allen Arena').length,1);
assert.equal(names['2565'],'SIU Edwardsville');
assert.equal(names['288'],'Lipscomb');
const lines=players.filter(p=>p.game_id==='96');
assert.equal(lines.length,21,'Only 21 players actually played; exclude all DNPs');
assert.equal(new Set(lines.map(p=>p.player_id)).size,21);
for(const [id,score,count] of [['2565',77,11],['288',78,10]]){
 const team=lines.filter(p=>p.team_id===id);
 assert.equal(team.length,count);
 assert.equal(team.reduce((s,p)=>s+p.pts,0),score);
 assert.equal(team.reduce((s,p)=>s+Number(p.minutes),0),200);
 assert.ok(team.every(p=>Number.isInteger(Number(p.minutes))),'Player minutes must display as whole numbers');
}
assert.ok(lines.every(p=>p.source_url==='https://www.espn.com/mens-college-basketball/boxscore/_/gameId/401920703'));
assert.ok(lines.every(p=>!players.some(o=>o.game_id!=='96'&&o.player_id===p.player_id)),'No unverified previously attended player matches');
const impact=p=>p.pts+p.reb+p.ast+p.stl+p.blk-p.tov-(p.fga-p.fgm)-(p.fta-p.ftm);
const ranked=lines.slice().sort((a,b)=>impact(b)-impact(a)||b.pts-a.pts);
assert.equal(ranked[0].player,'Devyn Martin');
assert.equal(impact(ranked[0]),22);
assert.equal(awards['espn:5174937'].all_conference[0].team,2);
assert.equal(awards['espn:5174937'].all_conference[0].conference,'CAA');
assert.equal(awards['espn:5174937'].all_conference[0].school,'Elon');
assert.equal(awards['espn:5107530'].all_conference[0].team,3);
assert.equal(awards['espn:5107530'].all_conference[0].conference,'ASUN');
assert.equal(awards['espn:5175660'].all_freshman[0].conference,'Big South');
assert.ok(read('college/player.html').includes('tags.all_freshman||[]'));

for(const player of ['David Wilson','Brennan Miller','Belal Sohaib','Jayden Riley']){
 const found=lines.find(p=>p.player===player);
 assert.ok(found&&headshots[found.player_id]?.image_url?.startsWith('https://siuecougars.com/images/2026/10/30/'),player+' missing school photo');
}
assert.ok(read('college/player.html').includes('schoolPhoto||photoId'));
const allen=venueData.venues.find(v=>v.name==='Allen Arena');
assert.ok(allen&&allen.id==='venue-0141');
assert.equal(allen.visits,1);
assert.equal(allen.games[0].id,g.id);
assert.equal(allen.games[0].url,'../college/game.html?id=96');
assert.equal(venueData.venueCount,venueData.venues.length);
assert.equal(venueData.mappedGames,venueData.venues.reduce((s,v)=>s+v.games.length,0));
assert.ok(read('index.html').includes('id="venueCount">141'));
assert.ok(read('index.html').includes('id="venueGameCount">826'));
console.log('PASS: 2026-11-07 SIUE at Lipscomb; 21 complete performances, POG, photos, both schools and Allen Arena');
