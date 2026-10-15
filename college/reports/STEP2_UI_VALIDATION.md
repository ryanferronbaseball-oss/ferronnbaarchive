# College Courtside Archive — Step 2 Player Stats + Profile QA

**Stage:** implemented and validated on `college-import-pilot`, **not published to the live NBA site or main branch**. User visual review is the next checkpoint before the remaining five pages.

## Implemented files

- [college/stats.html](../stats.html) — direct port of NBA `stats.html`, reusing existing `../assets/site.css` and `../assets/site.js`; traditional, advanced and per-36 leaderboard tabs, player search, category sorting, minimum-game filtering, search results, embedded player breakdown and links to the canonical player profile.
- [college/player.html](../player.html) — direct port of NBA `player.html`; original hero, aggregate traditional stats, advanced cards, game log, milestone panels and player portrait fallback. Adds a school selector **only for multi-school players**, defaulting to an all-school chronological log.
- [college/data/games.csv](../data/games.csv), [college/data/player_boxscores_espn.json](../data/player_boxscores_espn.json), [college/data/team_names.json](../data/team_names.json), and [college/data/validation.json](../data/validation.json) — generated, versioned data from the 94-game reconciliation workflow.

## Automated GitHub QA

[Full 94-game data build + source parity + JavaScript syntax verification passed](https://github.com/ryanferronbaseball-oss/ferronnbaarchive/actions/runs/38777739359).

The `college/scripts/test_step2_pages.py` checker verifies that the NBA and college pages retain the **same section hierarchy, number of statistical tables and original navbar links**, and that *all* NBA controls remain addressable by their DOM IDs. It also verifies the same canonical CSS and navigation JavaScript, the same NBA implementation of `aggregate()`, `advancedRecord()`, and `advDefinitions`, and validates all extracted page scripts through `node --check`. No NBA team maps, NBA-specific boxscore URLs or NBA headshot paths are allowed in college pages.

The generated data contract reports **94/94 games; 1,825 player appearances; 1,034 player IDs; 75 NCAA school IDs; 14 multi-school players**, zero duplicate player-game rows and fully reconciled team scoring and minutes. NCAA ESPN boxscore links use the correct league path. Sources and provenance from official university corrections are preserved.

[Review-bundle build and static verification](https://github.com/ryanferronbaseball-oss/ferronnbaarchive/actions/runs/38777976542) contains the isolated HTML, current NBA templates for side-by-side review, canonical CSS/JS and published college data.

## Browser DOM and visual checks

The two checked-in HTML pages and canonical CSS/JS were rendered in Chromium with the real, checked-in college JSON data supplied through a local fetch shim. (Navigation was restricted in the testing sandbox, so the local test validated **rendering and controls**, not public URL hosting.) **19 browser assertions passed with zero JavaScript runtime errors:**

1. Traditional leaderboard loaded 94 box scores / 1,825 appearances / 1,034 unique players; 1,034 player rows populated.
2. Original **Advanced** and **Per 36** statistical tab panels opened properly.
3. Searching for Jase Townsend returned one row with **14 GP / 170 PTS** under his canonical official identity.
4. Jase's player page showed 14 attended games, the original layout, and 14 chronological game-log rows. A single-school profile correctly hides the transfer selector.
5. NCAA ESPN box-score links were generated correctly from real event IDs.
6. Hunter Sallis showed **4 attended games / 63 points** across **Gonzaga and Wake Forest**, without separate player identities. The all-school log showed four rows; the Gonzaga school filter showed one, and the Wake Forest filter showed three.
7. Mobile-width player leaderboard loaded all 1,034 athletes.
8. There were **no unhandled JavaScript page errors**. Browser inspection confirmed the same shared ivory background `rgb(250, 248, 242)` as the NBA editorial theme.

Screenshots of desktop stats, Jase profile, Hunter multi-school log, and 390-pixel mobile view were captured during browser testing; these are review artifacts in the ChatGPT conversation rather than committed binary images to the Git repository.

## Remaining work and user review

- **Please review the Step 2 visual screenshots** against the NBA statistics and player pages, especially the leaderboard density, profile hero, tab treatment and transfer filter.
- Five additional pages (`college/index.html`, `college/game.html`, `college/records.html`, `college/milestones.html`, `college/insights.html`) are **not yet built**. Navigation links for those pages will work after Step 3; do not expose Step 2 as a complete stand-alone site before then.
- Every game currently lacks a verified arena name. Do not invent arena locations or pretend this empty field is complete when the Attendance Insights page is ported.
- Provisional official-source IDs are retained until independently verified ESPN IDs are available. Do not merge same-named athletes without ID evidence.
- Publication and main branch changes remain blocked pending seven-page parity, full link testing, final arena QA and user approval.
