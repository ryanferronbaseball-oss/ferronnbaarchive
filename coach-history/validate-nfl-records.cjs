/* Run with: node coach-history/validate-nfl-records.cjs */
const fs = require('node:fs');
const path = require('node:path');
const assert = require('node:assert/strict');
const root = path.resolve(__dirname, '..');
const games = JSON.parse(fs.readFileSync(path.join(root, 'nfl/data/games.json'), 'utf8'));
const rules = require('./data/verified-assignments.json').rules.filter(rule => rule.sport === 'NFL');
const records = new Map();
let wins = 0;
let losses = 0;
let ties = 0;
for (const game of games) {
 const label = `${game.date} ${game.away} at ${game.home}`;
 assert(Number.isSafeInteger(game.away_score) && Number.isSafeInteger(game.home_score), `${label}: missing or invalid final score`);
 assert(game.away_score >= 0 && game.home_score >= 0, `${label}: negative final score`);
 for (const side of ['away', 'home']) {
  const matches = rules.filter(r => r.team === game[side] && game.date >= r.from && game.date <= r.to);
  assert.equal(matches.length, 1, `${label}: expected one ${side} head coach, got ${matches.length}`);
  const name = matches[0].coach;
  if (!records.has(name)) records.set(name, {wins: 0, losses: 0, ties: 0, games: 0});
  const rec = records.get(name);
  const own = game[side + '_score'], other = game[side === 'home' ? 'away_score' : 'home_score'];
  rec.games++;
  if (own > other) {rec.wins++;wins++;} else if (own < other) {rec.losses++;losses++;} else {rec.ties++;ties++;}
 }
}
assert.equal(wins, games.length - ties / 2);
assert.equal(losses, games.length - ties / 2);
for(const [name,rec] of records)assert.equal(rec.games,rec.wins+rec.losses+rec.ties,`${name}: incomplete decisions`);
console.log(`PASS: ${games.length} NFL games, ${records.size} coaches, ${wins} wins, ${losses} losses, ${ties} tie appearances`);
console.log(Object.fromEntries(records));
