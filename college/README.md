# Courtside Archive — College (men's basketball)

**Work-in-progress only.** This branch does not modify the live NBA website. The goal is a college module that can ultimately appear under one master archive with NBA and NCAAB tabs.

## Attendance input
- `data/attendance.csv` contains 94 games from the owner's uploaded list, dated 2013–2026.
- Attendance IDs 1–94 are stable: never renumber, even if an older game is added.
- ESPN game IDs are **not yet verified** for all these games.
- Original 16-column intake workbook is maintained separately; this minimal CSV contains only IDs, date and team names.

## First ESPN pilot
Run locally:
```bash
python college/scripts/import_espn.py --ids 1,2,12,80,90,94 --fetch-boxscores
```
The script queries ESPN's men's college basketball date-specific scoreboard and game summary, matching exact dates and both normalized school identities. It rejects ambiguous/no-match cases, and saves:
- `output/matches.csv`: one line per attended game with match/source status;
- `output/player_boxscores_raw.json`: original ESPN player stat arrays and field labels;
- `output/summary.json`: counts and limitations.

A GitHub Actions workflow executes the same six-game pilot on pushes to this branch. Results are uploaded as **build artifacts**, not published to the website. Missing ESPN data will be backfilled from verified official school box scores later.

### Validation before publishing
1. Review every game match, neutral-site designation and score against official sources.
2. Normalize ESPN stat arrays to fixed MIN/PTS/REB/AST/STL/BLK/FG-FGA/3PM-3PA/FT-FTA columns by the **field names**, not assumed positions.
3. Treat missing as null, never zero. Player IDs must use stable provider-qualified IDs.
4. Validate each team's summed scoring versus its final score; handle DNP records and own-team points carefully.
5. Do not display partial or unverified player lines on leaderboards.

### Caveats
ESPN's scoreboard/history endpoints are undocumented and can change or omit small-school or postseason events. Do not infer that an unmatched result means the attended game never happened. Scoreboard dates may be timestamped in UTC, so game matching uses the requested local-date scoreboard response rather than UTC event.date. Teams with ambiguous names may require human aliases.

No API keys needed for the ESPN site endpoint. Do not store future provider keys in GitHub files.

## Full-archive matching and scoring audit (2026-10-15)

The 94-game ESPN discovery importer now matches **94 of 94** attended games. The confirmed Cal State Northridge–Tennessee State date is **November 21, 2022**, ESPN event ID **401486700**.

The separate normalization step (\`scripts/normalize_espn.py\`) validates team IDs, deduplicates player-game records, decodes shooting and traditional stat fields, checks every player's PTS against shooting totals, and verifies **both the final scores and NCAA regulation/overtime player-minute totals**. User-verified official supplemental rows are sourced in \`data/official_boxscore_supplements.csv\` and never overwrite ESPN raw data. The first audit identified 22 score discrepancies. Subsequent official-school backfills restored two missing Yanni Wetzell player lines; the updated audit now finds **74 games with both teams' scoring reconciled, 72 games with both scoring and all expected NCAA team minutes reconciled, and 22 still requiring review** (20 with missing points, 2 with missing scoreless-player minutes). The combined data now contains **1,790 original ESPN lines plus 2 verified official supplements, 1,389 strictly certified lines, 1,016 distinct ESPN athlete IDs, and 14 athletes seen representing multiple colleges**. Refer to \`reports/BOX_SCORE_COMPLETENESS.md\` for the 22-game reconciliation/backfill queue.

**Publication gate:** Do not expose aggregate player record rankings from all 94 games until the remaining 20 scoring gaps and 2 minute-only gaps are repaired or appropriately excluded and clearly labeled. A successful GitHub Actions job means parsing and QA succeeded, *not* that all player statistics are verified complete.

**Design gate:** \`DESIGN_PARITY.md\` requires direct reuse of the existing NBA archive's seven page structures, visual theme, sortable statistics, and single cumulative player profiles across school transfers. The live NBA archive and its default branch remain unchanged by this college development work.
