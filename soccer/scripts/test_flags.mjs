// Dependency-free rendering smoke test for the soccer nationality tags.
import assert from "node:assert/strict";
import fs from "node:fs";
import path from "node:path";
import vm from "node:vm";
import { fileURLToPath } from "node:url";

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "../..");
const matches = JSON.parse(fs.readFileSync(path.join(root, "soccer/data/matches.json"), "utf8"));
const countries = JSON.parse(fs.readFileSync(path.join(root, "soccer/data/nationalities.json"), "utf8"));
const archiveSource = fs.readFileSync(path.join(root, "soccer/assets/archive.js"), "utf8");
const pagesSource = fs.readFileSync(path.join(root, "soccer/assets/pages.js"), "utf8");

const names = new Set();
for (const m of matches) {
  for (const field of ["home_starters", "away_starters", "home_subs_used", "away_subs_used"])
    for (const name of m[field] || []) names.add(name);
  for (const e of m.events || [])
    for (const field of ["player", "out", "assist", "secondary_assist"])
      if (e[field]) names.add(e[field]);
}
const assigned = Object.values(countries).flat();
assert.equal(names.size, 83);
assert.equal(assigned.length, names.size);
assert.deepEqual(new Set(assigned), names);

async function render(page, search = "") {
  const elements = new Map(), handlers = [];
  const element = id => {
    if (!elements.has(id)) elements.set(id, {
      innerHTML: "", value: ({ category: "appearances", matchFilter: "all", recordStat: "goals", milestoneStat: "goals:1", milestoneMode: "games", goalKind: "all" })[id] || "",
      addEventListener() {}, querySelector() { return null; }, querySelectorAll() { return []; },
    });
    return elements.get(id);
  };
  const ctx = {
    console, Intl, URLSearchParams,
    location: { search, hash: "" },
    window: { history: { replaceState() {} } },
    document: {
      title: "", body: { dataset: { page } }, getElementById: element,
      addEventListener(type, fn) { if (type === "DOMContentLoaded") handlers.push(fn); },
      querySelector() { return {}; },
    },
    async fetch(url) {
      if (url.includes("matches.json")) return { ok: true, json: async () => matches };
      if (url.includes("nationalities.json")) return { ok: true, json: async () => countries };
      throw new Error("Unexpected request " + url);
    },
  };
  vm.runInNewContext(archiveSource, ctx);
  const archive = ctx.window.SoccerArchive;
  const data = await archive.load();
  assert.equal(data.players.length, names.size);
  for (const player of data.players) {
    assert(player.nationality, `No country for ${player.name}`);
    assert.match(archive.playerLink(player), /class="soccer-flag"/);
  }
  assert.match(archive.nationalityFlag("Ahmed Qasem"), /aria-label="Iraq"/);
  assert.match(archive.nationalityFlag("Samuel Gidi"), /aria-label="Slovakia"/);
  assert.match(archive.nationalityFlag("Sam Surridge"), /aria-label="England"/);
  vm.runInNewContext(pagesSource, ctx);
  await handlers[0]();
  const rendered = [...elements.values()].map(e => e.innerHTML).join("\n");
  assert.match(rendered, /class="soccer-flag"/, `${page} has no visible flag tags`);
  return { elements, rendered };
}

for (const page of ["home", "games", "stats", "player", "records", "goals"]) {
  const result = await render(page, page === "player" ? "?id=ahmed-qasem" : "");
  if (page === "games") assert.equal((result.elements.get("app").innerHTML.match(/<li><a href="\.\/player\.html\?id=/g) || []).length, 32);
  if (page === "player") assert.match(result.elements.get("app").innerHTML, /Ahmed Qasem<span class="soccer-flag" role="img" aria-label="Iraq"/);
  console.log(`PASS ${page} renders nationality flags`);
}
console.log("PASS all 83 player nationalities covered");
