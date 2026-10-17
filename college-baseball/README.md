# College Baseball · Courtside Archive

**Status:** source-verified initial pilot on an isolated draft branch. Six game scoreboards are source-matched, three include full player tables; production remains unchanged until reviewed and approved.

The site lives at \`/college-baseball/\` to avoid collision with the established college-basketball \`/college/\` site, professional \`/mlb/\` site, or future MiLB coverage. All college statistics are their own level-specific measurements.

## Pilot import update — October 2026

The uploaded college baseball workbook has **444 attendance rows**, dated 2017–2026 after correcting South Alabama at Old Dominion on March 30, 2024 per user confirmation. The first pilot stages **six verified game scores and inning lines** from the 2026 NCAA Auburn Regional, with **three complete official hitter/pitcher box scores (81 player-game rows; 62 distinct athlete identities)**. The other three games await player-stat transcription. All regional game sources are original official university one-page gamebooks, linked in `data/games.json`.

The published site is **unchanged**; the pilot exists on PR #10 only. Other 438 attendance entries remain in the uploaded master sheet and normalized import-review queue, **not** asserted to have official scores or player stats.

Original workbook rows **440–445** are the staged games. The user clarified that **attendance game #444 (spreadsheet row 445)** was **UCF @ Auburn**, rather than the originally entered Milwaukee @ Auburn. Official Regional **Game 5** on May 31 ended Auburn 9–3 UCF. The other May 31 attendance entry (**game #443, spreadsheet row 444**) is **Auburn @ Milwaukee**, official Regional **Game 6**, which Auburn won 8–1. Its existing source-verified player box score is retained under the original game ID. Both entries remain distinct; the university scorebooks and user correction are recorded in `data/import_report.json`.

The date originally recorded as `Friday, 3/30/34` is confirmed by the user to mean **2024-03-30**, South Alabama @ Old Dominion. This is preserved in `data/import_report.json`, not silently altered in the original upload.

The university PDF headers, batter/runner scores, inning line totals, pitcher outs, team hits, and strikeouts were cross-checked. Distinct regional **game numbers** are not the same field as doubleheader **game_number**. Future 2026 → 2025 → older imports should proceed in reviewed chunks, retaining a source-match/uncertainty queue.

**Do not re-run the simple `import_attendance.py` command in write mode on the current pilot data directory:** it intentionally produces attendance-only records and will overwrite individually verified game metadata. Use `--validate-only` while pilot source-backed box scores are being accumulated.

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

## Data contracts

\`data/games.json\`: one row per attended contest; \`id\`, dates, teams, scores, site, \`game_number\`, source and verification. \`data/player_stats.json\`: one player-game row with \`game_id\`, \`player_id\`, \`player\`, \`team\`, optional \`batting\` and/or \`pitching\` objects, and an official source reference. Hitter keys use the professional site convention (\`atBats\`, \`runs\`, \`hits\`, \`doubles\`, \`triples\`, \`homeRuns\`, \`rbi\`, \`baseOnBalls\`, \`strikeOuts\`, \`hitByPitch\`, \`sacFlies\`, \`stolenBases\`). Pitcher keys include \`outs\`, \`hits\`, \`runs\`, \`earnedRuns\`, \`baseOnBalls\`, \`strikeOuts\`, \`numberOfPitches\`, \`wins\`, \`losses\`, \`saves\`.

A missing field differs from a recorded **zero**. Derived rates appear only when the required numerator and denominator fields are present, and no college rates are added to professional rates. \`data/scoring_plays.json\` is intentionally empty until source-verified game scoring can be assembled; \`data/mlb_crosswalk.json\` is an empty verified cross-level ID mapping.

This foundation does not assert an attendance total, a postseason game, or a college player has already been observed. All examples in QA run only from disposable **synthetic** test fixtures.
