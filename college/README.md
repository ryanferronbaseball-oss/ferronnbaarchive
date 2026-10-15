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
python college/scripts/import_espn.py --limit 94 --fetch-boxscores
python college/scripts/normalize_espn.py --expected-games 94
```
The script queries ESPN's men's college basketball date-specific scoreboard and game summary, matching exact dates and both normalized school identities. It rejects ambiguous/no-match cases, and saves:
- `output/matches.csv`: one line per attended game with match/source status;
- `output/player_boxscores_raw.json`: original ESPN player stat arrays and field labels;
- `output/summary.json`: counts and limitations.

A GitHub Actions workflow imports and validates the full 94-game attendance collection on pushes to the college development branch. Results are uploaded as **build artifacts**, not published to the website. Missing ESPN data will be backfilled from verified official school box scores later.

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

The normalization step (`scripts/normalize_espn.py`) validates ESPN team IDs, deduplicates player-game records, decodes shooting and traditional stat fields, and requires **both official final scores and expected NCAA team-minute totals** to reconcile. Officially sourced supplement rows are in `data/official_boxscore_supplements.csv`; corrections to existing ESPN rows are in `data/official_boxscore_overrides.csv`, with the original values preserved for audit. The latest run finds **75 games with both teams' scoring reconciled, 73 games also passing the minute audit, and 21 remaining for investigation** (19 scoring gaps plus two minute-only cases). The combined data now contains **1,790 original ESPN rows, 8 sourced supplements, and 2 officially corrected existing player lines**. Refer to `reports/BOX_SCORE_COMPLETENESS.md` for the current queue and supporting official sources.

**Publication gate:** Do not expose aggregate player record rankings from all 94 games until the remaining 19 scoring gaps and 2 minute-only gaps are repaired or appropriately excluded and clearly labeled. A successful GitHub Actions job means parsing and QA succeeded, *not* that all player statistics are verified complete.

**Design gate:** `DESIGN_PARITY.md` requires direct reuse of the existing NBA archive's seven page structures, visual theme, sortable statistics, and single cumulative player profiles across school transfers. The live NBA archive and its default branch remain unchanged by this college development work.
