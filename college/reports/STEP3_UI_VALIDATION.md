# Courtside Archive College — Step 3: Five Remaining Pages QA

**Status (October 15, 2026): IMPLEMENTED AND CHROMIUM VERIFIED — USER VISUAL REVIEW NEXT.**
All work is on GitHub branch `college-import-pilot`. **No change to the NBA website's `main` branch or production URL.**

## Pages built from the actual NBA templates

Each page is a direct port of the existing NBA HTML, preserving the original header, footer, number of sections, navigation, controls and canonical stylesheet `../assets/site.css` and navigation JavaScript `../assets/site.js`. League-specific records, team IDs, labels and ESPN URLs are adapted to NCAA.

| NBA source | New college page | Key adaptation and verification |
| --- | --- | --- |
| `index.html` | [`college/index.html`](../index.html) | Replaces NBA 31-game hardcoded attendance list with the validated 94-game CSV; dynamic team/year charts, signature player records, year/search/sort controls, exact game-detail linking |
| `game.html` | [`college/game.html`](../game.html) | Direct attendance-ID + event-ID match to both university team records, all player statistics, source link, impact selection, previous/next, player profile links; unverified venue properly labeled; avoids falsely calling first five listed players verified starters |
| `records.html` | [`college/records.html`](../records.html) | Six original record cards, searchable single-game leaderboards, official supplement athletes, correct NCAA opponent name and ESPN college source links |
| `milestones.html` | [`college/milestones.html`](../milestones.html) | Record progression, statistical milestones, team/game records and legendary performances; all 94 game results tied directly to attendance and ESPN event IDs |
| `insights.html` | [`college/insights.html`](../insights.html) | Correct NCAA seasons, 75 college team records, school-filtered timeline, close-game/170+ scoring filters, player histories. Intentionally **does not invent arena names** or incorrectly aggregate missing venues as one location |

The approved Step 2 pages — [Player Statistics](../stats.html) and [Player Profile](../player.html) — remain intact, preserving transfer-school player profiles, source-backed Jase Townsend rows, and original advanced and per-36 calculations. All seven pages use the same canonical NBA theme.

## Automated verification

- **Structural and syntax parity:** [`test_step3_pages.py`](../scripts/test_step3_pages.py) checks seven HTML pages against their NBA source, including same navigation, original section/table counts, all NBA controls preserved, one extra intentional school filter on player profiles, complete internal destinations, absence of NBA-only legacy copy, shared CSS and JavaScript, JavaScript syntax via `node --check`, NCAA source event links, and all 94/1,825/75 data contract counts.
- **Real Chromium with HTTP (not an in-memory fetch shim):** [`test_step3_browser.py`](../scripts/test_step3_browser.py) tests home, game, records, milestone, and insight pages in a served site using the actual checked-in college CSV/JSON and original shared CSS/JS. **42 browser assertions passed; zero unhandled JavaScript page errors.**
- [**Passing GitHub Actions seven-page workflow**](https://github.com/ryanferronbaseball-oss/ferronnbaarchive/actions/runs/38781320333). The workflow artifact `college-step3-seven-page-review` includes its machine-readable 42-check test report and 7 original full/viewport PNG screenshots.

Key end-to-end assertions:

1. Homepage shows **94 attended games, 75 school teams, 94/94 imported box scores**, three signature performances, and working year and matchup filters.
2. Utah State @ San Diego (#59) displays **91–89**, correct NCAA opponent names and full player lines; selecting Jase Townsend actually navigates to his **14-game single profile**.
3. Six single-game record cards load. Searching `Jase Townsend` finds a restored athlete.
4. Milestones show **all 94 game results**. Record, Milestone, Team and Legendary panels load; filters and links work.
5. Insights show 8 metrics, all **75 teams**, correct season/calendar timeline toggle, sort and game-experience filters, and player links.
6. Both homepage and insights work at a **390px mobile width**.
7. No fabricated arena names or false arena counts: all 94 current `arena` fields are blank, the insights arena table explicitly says the venue rankings are pending verification, and the game detail page labels the location as unverified.
8. No runtime JavaScript exceptions during browser interaction and page navigation.

## Known launch requirements / user checkpoint

- **Visual review:** Compare the seven NCAA pages to their live NBA templates using the screenshot artifact. In particular check the home hero, game scoreboard, record tables, milestone cards, insights charts, and responsive layout. The original NBA page layout is maintained; the user has already approved the first two pages.
- **Arena completion remains separate from player/boxscore validation.** Venue research for the 94 NCAA games has not been performed. Do not use guessed team home arenas, infer venues from the host school, or include unverified stadium counts.
- **Potential next phase:** Review source/stat field semantics and advanced-stat availability, remaining provisional official athlete IDs (without merging by name), investigate/confirm school neutral-site arenas, full seven-page external and internal navigation tests and accessibility/desktop/mobile checks.
- **Publication:** This is a development-branch implementation. Do not merge, expose in production navigation or present these pages as live GitHub Pages until user acceptance and remaining quality gates are met.

