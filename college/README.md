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

The normalization step (`scripts/normalize_espn.py`) validates ESPN team IDs, deduplicates game appearances, decodes shooting and traditional-stat fields, and requires **both official final scores and expected NCAA team-minute totals**. Sourced supplemental lines are in `data/official_boxscore_supplements.csv`; corrections to original ESPN rows are in `data/official_boxscore_overrides.csv` with audit trails.

**Current quality result (October 15, 2026): 94/94 matched games; 91 games pass point-score reconciliation; 90 games pass both scoring and team-minute verification; 4 games still need review** (3 with missing points, 1 with incomplete minutes). There are 1,790 original ESPN player rows, 30 sourced supplements and 9 officially corrected existing lines; 1,742 player lines belong to strictly verified games.

A systematic review of **all 17 USD games attended during Jase Townsend's 2021–23 tenure** showed **14 actual appearances omitted from ESPN's imported records**. All 14 are now available under the single stable `official:san-diego:jase-townsend` identity: **170 points across 14 attended games**. Three of those 14 had been restored earlier; the latest 17-game audit restored 11 more. The other three attended games have no Townsend appearance in the official box scores. Detailed sources and the four-game remaining queue: `reports/BOX_SCORE_COMPLETENESS.md`.

Official university sources have also restored missing Life Pacific, Hofstra, Santa Clara and Cal Poly players, including two zero-point appearances and three minute corrections. Those four additional games are now certified; the remaining IDs are **31, 49, 64, 71**.

**Publication gate:** Do not treat games with incomplete official player-point or minute totals as certified leaderboards until the three remaining scoring discrepancies and one minute-only discrepancy are repaired, or explicitly excluded and clearly labeled. A successful CI run certifies that validation ran, not that all data has been recovered.

**Design gate:** `DESIGN_PARITY.md` requires direct reuse of the existing NBA archive's seven page structures, visual theme, sortable statistics, and single cumulative player profiles across school transfers. The live NBA archive and its default branch remain unchanged by this college development work.
