# Courtside Archive College — Implementation Plan

Baseline: [94/94 game point-and-minute validation](https://github.com/ryanferronbaseball-oss/ferronnbaarchive/actions/runs/38775099460) (October 15, 2026). 1,825 player-game rows, 1,034 distinct identifiers, 35 official supplements. **NBA production stays untouched**; all implementation work remains on `college-import-pilot`.

## Step-by-step checkpoint status (October 15, 2026)

**Step 1 — Data conversion and relational validation: COMPLETE.** The version-controlled `college/scripts/build_site_data.py` adapter runs in GitHub Actions after the 94-game normalizer and produces a separately downloadable `college-site-ready-data` artifact with `games.csv`, `player_boxscores_espn.json`, `team_names.json`, and `validation.json`. [Successful Step 1 workflow](https://github.com/ryanferronbaseball-oss/ferronnbaarchive/actions/runs/38776739381).

Verified output: **94 games**, **1,825 player appearances**, **1,034 unique player IDs**, **75 college school IDs**, **14 multi-school ESPN athlete identities**, no duplicate attendance/player combinations, exact source event/date/school joins, all point and minute totals reconciled. Regression fixtures: **Jase Townsend 14 attended games / 170 points**, **Daniel Akin 2 / 36**, **Tory San Antonio 2 / 10**, and **Hunter Sallis 4 / 63** with Gonzaga + Wake Forest still connected to one player. All statistics and official-source provenance are retained. The separate site data is generated as a CI artifact, **not yet checked into the served website path or published**.

**Known non-blocking data gap:** all 94 arena fields in the current sourced college game export are blank. **Do not guess venues, fabricate arena counts, or treat unverified arenas as a single physical arena.** Venue lookup must be a distinct fact-check before launching arena insights. The Step 1 result proves the data schema and joins, not page layout fidelity or exhaustive field-by-field historical verification.

**Step 2 — Player statistics and profile UI port: IMPLEMENTED; AUTOMATED AND CHROMIUM UI CHECKS PASSED; USER VISUAL REVIEW NEXT.** The direct NBA template ports live at `college/stats.html` and `college/player.html` on the dev branch, using the same canonical shared CSS and navigation JavaScript. Both pages load the committed college fixture, preserve statistical formulas and all leaderboard views, use NCAA team maps / ESPN URLs, and show one cross-school profile with an optional school-filtered game log. Traditional, Advanced and Per-36 views; 94 games / 1,825 appearances / 1,034 players; Jase Townsend (14G, 170 PTS); and Hunter Sallis (4G, Gonzaga + Wake Forest 1/3 split) have been checked in Chromium. See [Step 2 detailed review and evidence](reports/STEP2_UI_VALIDATION.md) and the [passing GitHub Actions check](https://github.com/ryanferronbaseball-oss/ferronnbaarchive/actions/runs/38777739359). No live production change.

**Steps 3–4 — Other five pages, then full site review/release: NOT STARTED.** Stay on development branch; leave NBA production untouched.

## Phase 1 — College data adapter and test fixture

The current NBA site's seven HTML pages consume `./data/games.csv` and `./data/player_boxscores_espn.json`, rendered with `./assets/site.css` and `./assets/site.js`. They should be ported to `college/*.html` with `../assets/` shared references and `./data/` college references. Keep existing markup, component classes, breakpoints, controls and visual hierarchy.

The NBA `data/games.csv` columns are `id,date,away,home,arena,nba_game_id,away_score,home_score,boxscore_status`. The college normalizer emits `id,date,away,home,arena,espn_event_id,away_score,home_score,away_team_id,home_team_id,boxscore_status`. NBA player rows contain `game_id`, `espn_event_id`, `date`, `player_id`, `player`, `team_id`, `minutes`, `pts`, `reb`, `ast`, `fgm`, `fga`, `fg3m`, `fg3a`, `ftm`, `fta`, `oreb`, `dreb`, `stl`, `blk`, `tov`, `source`; college normalized rows currently add `game_id` as **attendance ID**, plus school/opponent and source metadata. **Game identification/linking must be adapted explicitly** rather than assuming NBA's game ID rules.

1. Ship `college/data/games.csv` and `college/data/player_boxscores_espn.json` generated deterministically from the reconciled 94-game workflow; avoid manual one-off edits to published JSON.
2. Keep historical attendance dates, away/home labels, ESPN event IDs, and official source/provenance fields intact.
3. Ensure every `player.game_id` refers to exactly one college game and links to `college/game.html?id=...`. The match must use attendance ID, with event ID only for ESPN outbound links.
4. Resolve player ID aliasing **without ever merging players by name alone**. Jase Townsend's 14 USD appearances, Daniel Akin's 2, Tory San Antonio's 2 and all 14 NCAA multi-school players must remain unified.
5. Prefer NCAA team maps populated from verified provider school ID and actual historical school name. NBA team names, NBA logos, headshot links and ESPN NBA boxscore links must not appear on college pages.
6. Preserve missing values as missing; avoid fabricated advanced metrics or silent zeros. Test shot makes/attempts, inferred points, aggregate rates, per-36 and per-game views.

## Phase 2 — Pixel/layout parity and functional validation

Port the same seven HTML templates, unchanged in main visual structure:

- `college/index.html` ← `index.html` (homepage)
- `college/game.html` ← `game.html` (game detail)
- `college/stats.html` ← `stats.html` (traditional / advanced / per-36 tabs)
- `college/player.html` ← `player.html` (single cross-school player identity and chronological log)
- `college/records.html` ← `records.html`
- `college/milestones.html` ← `milestones.html`
- `college/insights.html` ← `insights.html`

Start functional review with the stats and player pages: source-proof Jase Townsend, Yanni Wetzell, Hunter Sallis, Daniel Akin, Tory San Antonio, and cross-school Chad Baker-Mazara. Show one chronological all-schools game log by default with optional school filter. Test all tab selections, sorting, filters, game-to-player links, player-to-game links, static-host relative paths, null values, and small-screen overflow. Then compare the remaining five pages and shared desktop/mobile CSS to NBA production. Preserve current NBA `main` branch and existing live URLs.

## Exit criteria before launch

- 94/94 games, 1,825 unique player-game rows; both scoring and team minutes reconciled.
- Generated site output is deterministic and directly traceable to official and ESPN sources.
- Seven college pages present with the same design tokens, layout, page sections, and working navigation.
- Same leaderboard categories, statistical calculation definitions, and missing-input treatment as NBA.
- Transfer players have one canonical profile with correct school splits; no cross-school double-counting.
- No NBA-specific URLs, headlines, logos, or team ID maps leaking into college displays.
- Human spot-check at both desktop and mobile widths; follow-up fixes on development branch.
- Only publish / connect to navigation after reviewed; do not merge unreviewed scaffolding to `main`.

## User review

No additional official box scores are currently required for the 94-game batch. The next useful user action is to **compare a working college preview** to the existing NBA pages and flag differences; later confirm any ambiguous arenas/neutral sites before launch.
