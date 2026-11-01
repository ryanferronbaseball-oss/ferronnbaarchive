// All live sports player profiles use the same versioned color treatment.
import assert from "node:assert/strict";
import { readFileSync, existsSync } from "node:fs";
import { resolve } from "node:path";
import { fileURLToPath } from "node:url";

const root=resolve(fileURLToPath(new URL("..",import.meta.url)));
const paths=["nba","nfl","mlb","soccer","college","cfb","college-baseball"];
const shared="../assets/player-palette.css?v=shared-20261101";
const stylePath=resolve(root,"assets/player-palette.css");
assert(existsSync(stylePath));

for(const sport of paths){
 const html=readFileSync(resolve(root,sport,"player.html"),"utf8");
 assert(html.includes(`href="${shared}"`),`${sport} profile needs the shared palette`);
 assert(html.includes("</head>"),`${sport} HTML head intact`);
}
const css=readFileSync(stylePath,"utf8");
for(const token of ["--ca-player-tag-bg: #e7eee5","--ca-player-tag-border: #bfd0bf","--ca-player-green: #284d3c","--ca-player-tab-bg: #f0f2eb","--ca-player-detail-bg: #f6f8f3"])
 assert(css.includes(token),`Missing palette token: ${token}`);
for(const selector of [".hero .accolade-badge",".award-badges .award-badge",".achievement-row .career-badge","body[data-page=\"player\"] .mlb-profile-badge","body[data-page=\"player\"] .soccer-micro",".career-honors .honor-tab[aria-selected=\"true\"]",".nfl-honor-tabs button[aria-selected=\"true\"]","body[data-page=\"player\"] .mlb-award-tab[aria-selected=\"true\"]"])
 assert(css.includes(selector),`Unstyled sport control: ${selector}`);
assert(css.includes("background: var(--ca-player-green) !important"),"Selected tabs need the shared dark green");
assert(css.includes("background: var(--ca-player-detail-bg) !important"),"Awards detail panels must share the light theme");
console.log(`PASS ${paths.length} sports share player achievement colors, selected tabs, and details styling`);
