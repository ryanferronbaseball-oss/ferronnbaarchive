/* Run with: node coach-history/validate-nba-records.cjs
 * An attended-game coaching record is complete only when both final scores
 * and exactly one verified head coach for each team are present.
 */
const fs = require('node:fs');
const path = require('node:path');
const assert = require('node:assert/strict');
const root = path.resolve(__dirname, '..');
const lines = fs.readFileSync(path.join(root, 'data/games.csv'), 'utf8').trim().split(/\r?\n/);
const columns = lines.shift().split(',');
const games = lines.map(line => Object.fromEntries(line.split(',').map((value, i) => [columns[i], value])));
const rules = require('./data/verified-assignments.json').rules.filter(rule => rule.sport === 'NBA');
const records = new Map();
let wins = 0;
let losses = 0;

for (const game of games) {
  const label = `${game.date} ${game.away} at ${game.home}`;
  const away = Number(game.away_score);
  const home = Number(game.home_score);
  assert(game.away_score !== '' && game.home_score !== '', `${label}: missing final score`);
  assert(Number.isSafeInteger(away) && Number.isSafeInteger(home) && away >= 0 && home >= 0, `${label}: invalid final score`);
  assert.notEqual(away, home, `${label}: NBA game cannot end tied`);
  for (const side of ['away', 'home']) {
    const applicable = rules.filter(rule => rule.team === game[side] && game.date >= rule.from && game.date <= rule.to);
    assert.equal(applicable.length, 1, `${label}: expected exactly one ${side} coach, got ${applicable.length}`);
    const coach = applicable[0].coach;
    if (!records.has(coach)) records.set(coach, { wins: 0, losses: 0, games: 0 });
    const record = records.get(coach);
    const won = side === 'away' ? away > home : home > away;
    record.games++;
    if (won) { record.wins++; wins++; } else { record.losses++; losses++; }
  }
}

assert.equal(wins, games.length, 'One coach win is required per attended game');
assert.equal(losses, games.length, 'One coach loss is required per attended game');
for (const [name, record] of records) assert.equal(record.wins + record.losses, record.games, `${name}: incomplete W–L record`);
console.log(`PASS: ${games.length} NBA finals, ${wins} coach wins, ${losses} coach losses, ${records.size} coaches`);
console.log('Mike Dunleavy:', records.get('Mike Dunleavy'));
