import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { Script } from 'node:vm';

const file = p => readFileSync(new URL(`../${p}`, import.meta.url), 'utf8');
const data = JSON.parse(file('data/nba_olympic_representation.json'));
const logs = JSON.parse(file('data/player_boxscores_espn.json'));
const knownIds = new Set(logs.map(row => String(row.player_id).replace(/^espn:/, '')));
const entries = Object.entries(data.players);

assert.equal(entries.length, 61, 'Olympic player roster should remain stable until reviewed');
assert.ok(entries.every(([id]) => knownIds.has(id)), 'Every Olympian must be in the NBA archive');
const validYears = new Set([1996, 2000, 2004, 2008, 2012, 2016, 2020, 2024]);
for (const [id, record] of entries) {
 assert.ok(data.countries[record.team], `Unknown represented team for ${id}`);
 assert.ok(record.years.length > 0, `No Olympic Games listed for ${id}`);
 assert.deepEqual(record.years, [...new Set(record.years)].sort((a, b) => a - b), id);
 assert.ok(record.years.every(year => validYears.has(year)), id);
 assert.ok(!record.discipline || record.discipline === '3x3', id);
}

const examples = {
 '1966': ['USA', [2004, 2008, 2012, 2024]], // LeBron James
 '110': ['USA', [2008, 2012]], // Kobe Bryant
 '996': ['ESP', [2004, 2008, 2012, 2016, 2020]], // Pau Gasol
 '1982': ['GER', [2008]], // Chris Kaman
 '3439': ['ESP', [2012]], // Serge Ibaka
 '272': ['ARG', [2004, 2008, 2012, 2016]], // Manu Ginobili
 '3112335': ['SRB', [2016, 2024]], // Nikola Jokic
 '3037789': ['SRB', [2016, 2024]], // Bogdan Bogdanovic
 '1016': ['SCG', [2004]], // Vladimir Radmanovic
 '1713': ['BRA', [2012, 2016]], // Nene
 '6434': ['USA', [2024]], // Jimmer Fredette (3x3)
};
for (const [id, [team, years]] of Object.entries(examples)) {
 assert.equal(data.players[id]?.team, team, id);
 assert.deepEqual(data.players[id].years, years, id);
}
assert.equal(data.players['6434'].discipline, '3x3');
for (const id of ['3989', '3456', '3423', '2528210', '3232']) {
 assert.ok(!(id in data.players), `Non-Olympian ${id} must not show a tag`);
}

const page = file('nba/player.html');
assert.ok(page.includes('id="olympicBadge"'));
assert.ok(page.includes('class="accolade-badge olympic-badge"'));
assert.ok(page.includes('nba_olympic_representation.json?v=olympics-20261101'));
assert.ok(page.includes('badge.classList.add("visible")'));
assert.ok(!page.includes('Olympic medal'), 'No medal totals should be shown');
const inlineJs = page.match(/<script>([\s\S]*?)<\/script>/)?.[1];
assert.ok(inlineJs, 'NBA profile inline JavaScript missing');
new Script(inlineJs, { filename: 'nba/player.html inline JavaScript' });

console.log(`NBA Olympic tags validated: ${entries.length} profiles, ${Object.keys(examples).length} exact examples.`);
