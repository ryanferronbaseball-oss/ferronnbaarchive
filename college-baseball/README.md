# College Baseball · Courtside Archive

**Status:** 444 attended college baseball games are staged in **draft PR #10**, with eight complete official gamebooks and six additional sourced college tournament scoreboards. Published site unchanged until user approval.

The site lives under \`/college-baseball/\`, with independent college baseball stats and verified inter-level player IDs only. It shares the exact MLB archive design system for Inter fonts, navigation, scoreboards, box-score layout, cards, responsive tables, and bat-order number column.

## Attendance import and source verification — October 2026

The original uploaded Excel workbook \`NCAAB Games.xlsx\` has **444 attendance entries, 2017–2026**, now all represented in \`data/games.json\`. \`data/attendance_master_444.csv\` is an auditable plain-text normalized sheet, preserving original workbook row numbers 2–445. The original spreadsheet is not changed. \`data/attendance_source_444.deflate.b64\` is a losslessly packed record of the normalized attendance data, decoded by \`scripts/build_attendance_master.py\`, which preserves official gamebooks and gives each date/matchup/source-row a stable ID. No unidentified doubleheader or tournament game is merged. Same-date repeated matchups are flagged \`possible_same_day_doubleheader\` and do **not** receive invented doubleheader game numbers.

Current data statuses:

| Status | Games | Meaning |
|---|---:|---|
| \`official_boxscore_verified\` | **8** | All original player batting, pitching, lineup positions and substitutions imported from official sources and reconciled to game totals |
| \`official_scoreboard_verified\` | **6** | Original college gamebook / university or conference source identifies matchup, tournament game, R/H/E, innings and pitching decisions; **individual player lines not yet imported** |
| \`attendance_only\` | **430** | Original attended date / schools retained; no invented scores, player stats or gamebook availability |
| **Total** | **444** | Original personal attendance entries, one distinct row per contest |

The first fully completed batch includes **six 2026 NCAA Auburn Regional games** on May 29–31, including the user-corrected final attendance game #444 **UCF @ Auburn** (regional Game 5, Auburn 9–3), plus the separately documented **Auburn @ Milwaukee** later May 31 (regional Game 6, Auburn 8–1). These gamebooks include 165 player-game lines.

The next source-verified batch covers **eight SEC Tournament games (May 20–23, 2026; original workbook rows 432–439)**. All eight final scores and per-inning lines are checked and staged. Two also have *complete official hitter and pitcher gamebooks*, including 51 additional player-game lines:
- **May 20 LSU @ Auburn:** Auburn 3–1; 27 player-game lines, source-confirmed starting batting order and four substitute entries; winner Jake Marciano, loser Casan Evans, save Jackson Sanders. Official LSU 2026 PDF gamebook cited in game record.
- **May 23 Arkansas @ Auburn:** Arkansas 2–1; 24 player-game lines and nine starters on each side; winner Ethan McElvain, loser Ryan Hetzler. Official Arkansas gamebook linked.
- **Six further May 20–23 SEC tournament games** (Tennessee–Arkansas, Mississippi State–Georgia, Florida–Alabama, Arkansas–Texas, Auburn–Texas A&M, Florida–Georgia) have official scores, inning lines and decisions but **not** individual player stats yet.

Across eight full scorebooks: **216 source-reconciled player-game rows, 117 unique college athlete IDs**. Batting-slot identities stay 1–9 with indented \`↳\` substitutions, and pitcher #1 is the starting pitcher. Incomplete NCAA stats are not filled from a season roster or guessed.

Other confirmed corrections: user's South Alabama @ Old Dominion 2024-03-30 originally appeared as \`Friday, 3/30/34\`; final game #444 originally entered Milwaukee–Auburn but corrected to UCF–Auburn. Both corrections documented in \`data/import_report.json\` and in the source queue.

The source audit and browser checks are in \`scripts/test_college_baseball.py\` and GitHub workflow \`.github/workflows/college-baseball-qa.yml\` (desktop 1280px + mobile 390px, with screenshot artifacts). Current review gate is **draft only**; do not merge into \`main\` until user approval. Import remaining 2026 official player gamebooks newest-to-oldest in batches of 5–10, marking source conflicts or unavailable stats rather than silently guessing.

## What we are building

- **Overview:** witnessed games, teams, seasons, ballparks, and a searchable attendance history.
- **Games & Box Scores:** matchup, ballpark, official scores, inning lines, verified college batting and pitching box scores, game decisions and scoring details when the sources contain them; neutral sites, doubleheaders, NCAA Regionals, Super Regionals, the Men's College World Series and conference tournament games.
- **Players:** deduplicated identities, attended-game aggregates, AVG/OBP/SLG/OPS for batters, ERA/WHIP/strikeouts for pitchers, and separate batting and pitching panels for two-way players.
- **Signature Performances:** single-game top performances and documented historic achievements, never imagined totals.
- **Future To the MLB:** explicitly verified crosslinks of college identity to MLB player identity (and separate drafted-only/MLB-appearance statuses, if verified). MLB, college and MiLB statistics must **never** be summed together.

## Attendance import: one row for each game witnessed

The empty CSV template is at [data/attendance.csv](data/attendance.csv). It contains only a header:

\`attendance_id,date,away,home,ballpark,city,state,neutral_site,game_number,game_type,postseason_round,away_score,home_score,source_url,notes\`

- **Required:** \`date\` in \`YYYY-MM-DD\` (or US \`MM/DD/YYYY\`), the visiting \`away\` team and designated \`home\` team. For a neutral-site event, use the officially designated home and away sides when possible.
- **Everything else optional:** leave fields blank when not known. The importer preserves unknowns as \`null\` (not guesses).
- **Doubleheaders:** if two games share the same calendar date and opponents, set \`game_number\` to \`1\` and \`2\`. A duplicate with missing identifiers is **rejected**, never silently merged.
- **Neutral site:** \`yes\`, \`no\`, or blank for unknown.
- **Game type:** regular season, exhibition, conference tournament, NCAA postseason, etc. Keep the exact \`postseason_round\` if supplied.
- **Scores supplied by user:** copied with provenance \`user_attendance_log\`; the source-check status remains **attendance only** even if the scores are present.
- **Official source:** \`source_url\` may point to a gamebook or box score but a URL in the list alone does **not** mean the statistics have been checked.
- **Attendance ID:** optional stable identifier from your source sheet; generated canonical game IDs use date, team names and doubleheader number.

Google Sheets users can export a CSV (File → Download → Comma-separated values). A pre-existing sheet or other attendance list can also be supplied and normalized into this schema.

### Validate, then import

Run from repository root:

\`\`\`bash
python college-baseball/scripts/import_attendance.py --validate-only
python college-baseball/scripts/import_attendance.py
\`\`\`

The importer writes only \`college-baseball/data/games.json\` and the import report. It does not reach out to NCAA/ESPN or fabricate scores, teams, player statistics or pitch-by-pitch data. No attended games are shipped with the initial foundation.

## Official scorebook verification workflow

After attendance rows are imported, select a small 3–5 game pilot across years and schools:

1. **Identify exact game** by date, away/home, actual venue, designated home side, game number, and postseason classification.
2. **Source hierarchy:** university athletics official scorebook/Sidearm HTML or PDF → NCAA gamebook and verified conference archives → other corroborating sources. ESPN data may assist discovery but should not override official gamebooks, especially for older college baseball.
3. **Reconcile scoreboard:** inning by inning to final score, extra innings, game completion / suspended games and doubleheader number.
4. **Reconcile hitters/pitchers:** all players, lineup changes, two-way roles, runs, hits, errors, AB, R, H, 2B, 3B, HR, RBI, BB, SO, SB, and pitching outs/H/R/ER/BB/K when recorded. Preserve pitching outs as an integer; \`5.1\` IP means 16 outs, not 5.1 decimal innings.
5. **Source status:** per-game \`attendance_only\`, \`source_matched\`, \`partial_boxscore\`, or \`official_boxscore_verified\` only after full reconciliation. Missing historical fields stay null. Do not present a nonofficial box score as verified.
6. **Cross-level identities:** match college athletes by player, school, season and source ID. Only add a college → MLB identity link after verification. \`data/mlb_crosswalk.json\` begins empty.

## MLB visual parity and official college batting order

The new college baseball dashboard intentionally shares the **exact MLB archive base CSS** (Inter typeface, cream/forest palette, 1160px page width, headline sizes, navigation spacing, score cards, table styles, and responsive breakpoints) with college-specific additions only where the gamebook requires them. Game details reuse the three-column MLB scoreboard, inning panels, **Win / Loss / Save** cards, and separate **Batting / Pitching** tabs. Player profiles use the same hero composition and six-stat rows as MLB; leaderboards, game cards, and signature cards follow the same presentation.

Every batter from the six verified Auburn Regional games has a source-verified `batting_slot` (integer **1–9**), `batting_sub_index` (0 for the starter, 1+ for replacements in that **same spot**), `batting_appearance_index`, and `position`. A substitute is rendered with the MLB **↳** notation immediately under the original starter, not a fictitious tenth or eleventh batting position. The pilot source audit confirms **116 batting appearances including eight substitute/replacement entries**, which are kept separate across both games held on May 31. Pitcher `pitching_appearance_index` begins at 0 for the starting pitcher and increases for relief appearances, matching MLB's numbered pitching rows.

For future older-game imports: **do not guess batting order** from a general season roster, a list sorted by name, or batting-stat totals. Transcribe the original lineup table and substitution indentations from the actual university/NCAA scorebook. If the information is unavailable, leave the lineup metadata absent and show an em dash rather than an invented batting spot. College stats remain independent of MLB data.

## Data contracts

\`data/games.json\`: one row per attended contest; \`id\`, dates, teams, scores, site, \`game_number\`, source and verification. \`data/player_stats.json\`: one player-game row with \`game_id\`, \`player_id\`, \`player\`, \`team\`, optional \`batting\` and/or \`pitching\` objects, and an official source reference. Hitter keys use the professional site convention (\`atBats\`, \`runs\`, \`hits\`, \`doubles\`, \`triples\`, \`homeRuns\`, \`rbi\`, \`baseOnBalls\`, \`strikeOuts\`, \`hitByPitch\`, \`sacFlies\`, \`stolenBases\`). Pitcher keys include \`outs\`, \`hits\`, \`runs\`, \`earnedRuns\`, \`baseOnBalls\`, \`strikeOuts\`, \`numberOfPitches\`, \`wins\`, \`losses\`, \`saves\`.

A missing field differs from a recorded **zero**. Derived rates appear only when the required numerator and denominator fields are present, and no college rates are added to professional rates. \`data/scoring_plays.json\` is intentionally empty until source-verified game scoring can be assembled; \`data/mlb_crosswalk.json\` is an empty verified cross-level ID mapping.

This foundation does not assert an attendance total, a postseason game, or a college player has already been observed. All examples in QA run only from disposable **synthetic** test fixtures.
