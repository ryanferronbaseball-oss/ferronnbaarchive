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

## Chromium end-to-end browser QA — passed (real HTTP)

The [Step 2 Chromium GitHub Actions run](https://github.com/ryanferronbaseball-oss/ferronnbaarchive/actions/runs/38778999442) installed a real Chromium browser and served the **actual checked-in HTML, shared canonical CSS/JS and college data files over local HTTP**, rather than replacing the site's fetch requests. The committed test is [`college/scripts/test_step2_browser.py`](../scripts/test_step2_browser.py). **21 full browser assertions passed, with zero unhandled JavaScript runtime errors**, including:

1. The college leaderboard returns HTTP 200, loads exactly 94 verified games, 1,825 appearances and 1,034 players, and populates all 1,034 player rows.
2. The page's computed background is `rgb(250, 248, 242)`, the editorial NBA archive's canonical ivory background.
3. The **Traditional**, **Advanced** and **Per 36** view controls switch correctly and preserve the original NBA calculations.
4. Searching for Jase Townsend isolates his verified row (14 attended games, 170 points). **Clicking the row actually navigates over HTTP to `college/player.html?id=official%3Asan-diego%3Ajase-townsend`**, displaying his single canonical profile.
5. Townsend has fourteen chronological box-score rows, NCAA ESPN provider links, and no irrelevant school filter.
6. Hunter Sallis loads into a single profile across **Gonzaga** and **Wake Forest**. His all-school log shows four games, Gonzaga one, Wake Forest three; all dropdown interactions work in the browser.
7. A narrow **390px mobile browser** also loads the complete 1,034-player leaderboard.
8. The browser reported **no page-level JS exceptions**.

The GitHub browser-test artifact `college-step2-chromium-check` contains the actual rendered desktop leaderboard, Jase profile, Sallis transfer-history log, mobile screenshot and machine-readable report. This is the recommended **visual review evidence**. The prior separate in-sandbox Chromium test (19 passing assertions using an in-memory local data shim) also passed; the new GitHub Action is stronger because it checks real HTTP fetches and in-site navigation.

**This does not make the pages live/public or verify the unfinished five college pages.** The actual college stats/profile pages are development-branch files awaiting the human design-parity checkpoint.

## Remaining work and user review

- **Please review the Step 2 visual screenshots** against the NBA statistics and player pages, especially the leaderboard density, profile hero, tab treatment and transfer filter.
- Five additional pages (`college/index.html`, `college/game.html`, `college/records.html`, `college/milestones.html`, `college/insights.html`) are **not yet built**. Navigation links for those pages will work after Step 3; do not expose Step 2 as a complete stand-alone site before then.
- Every game currently lacks a verified arena name. Do not invent arena locations or pretend this empty field is complete when the Attendance Insights page is ported.
- Provisional official-source IDs are retained until independently verified ESPN IDs are available. Do not merge same-named athletes without ID evidence.
- Publication and main branch changes remain blocked pending seven-page parity, full link testing, final arena QA and user approval.
