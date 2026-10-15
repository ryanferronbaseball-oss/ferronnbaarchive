# Courtside Archive — College (men's basketball)

**Work-in-progress only.** This branch does not modify the live NBA website. The goal is a college module that can ultimately appear under one master archive with NBA and NCAAB tabs.

## Attendance input
- `data/attendance.csv` contains 94 games from the owner's uploaded list, dated 2013–2026.
- Attendance IDs 1–94 are stable: never renumber, even if an older game is added.
- All 94 attended game IDs are matched to ESPN event IDs and verified for player scoring and minute coverage; individual historical stat fields still require spot review.
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

**Final historical game completeness result (October 15, 2026): all 94 of 94 attended games match ESPN event IDs, have both teams' player points reconciled to official final scores, and have team player-minute totals reconciled to 200 minutes in regulation or expected overtime totals.** Open player-point/minute backfills: **0**. The final normalized data contains **1,790 ESPN raw player appearances plus 35 traceable official-school supplements = 1,825 certified player-game records**, with **9 originally imported player records corrected from official school sources**, **1,034 distinct player identities** and **no duplicate player-game rows**.

A systematic audit of **all 17 San Diego games attended during Jase Townsend's tenure** confirmed **14 actual appearances missed by the ESPN summary feed**. They now share the single qualified identity `official:san-diego:jase-townsend`: **170 points in 14 games witnessed**. Official sources also restore Yanni Wetzell twice, Colorado omissions, missing scoreless players, and all other scoring/minute discrepancies; the last four repaired games were Eastern Michigan @ UC Irvine, Cal State Fullerton @ San Diego State, Denver @ UCLA, and Utah State @ San Diego State. Daniel Akin and Tory San Antonio are correctly unified across two attended games each.

[Successful final 94-game GitHub Actions validation](https://github.com/ryanferronbaseball-oss/ferronnbaarchive/actions/runs/38775099460); see `reports/BOX_SCORE_COMPLETENESS.md` for the annotated audit trail and source links.

**Website implementation status (October 15, 2026): all seven college pages now exist on `college-import-pilot`.** The user's approved Step 2 pages, `stats.html` and `player.html`, passed Chromium tests and retain NBA advanced/traditional/per-36 calculation parity, with verified single player identities across school transfers. Step 3 adds `index.html`, `game.html`, `records.html`, `milestones.html`, and `insights.html`. All seven preserve the actual NBA markup and shared ivory-and-evergreen CSS, adapted for NCAA schools and game IDs. [Step 3 live HTTP browser QA passed](https://github.com/ryanferronbaseball-oss/ferronnbaarchive/actions/runs/38781320333) with **42 passing browser assertions and zero JavaScript errors**. Review screenshots, source parity and known limitations in `reports/STEP3_UI_VALIDATION.md`.

**Next release gate:** The visual review and remaining launch checks are still required. In particular, **all 94 game venue records now have game-specific historical sources and neutral-site classification**, and venue counts are now available, grouped by verified physical arena identity rather than merely current sponsor names. Source/statistic semantics, identity aliases, desktop/mobile accessibility and external link checks should receive final review. Score/minute reconciliation does not independently validate every statistical field, and missing advanced inputs must not be fabricated. Do not deploy the college pages or modify NBA production until the user approves the remaining site checks.

**Design gate:** `DESIGN_PARITY.md` requires direct reuse of the existing NBA archive's seven page structures, visual theme, sortable statistics, and single cumulative player profiles across school transfers. The live NBA archive and its default branch remain unchanged by this college development work.


**Step 4 sourced arena completion:** All 94 historical attended game venues are recorded in `data/verified_venues.csv` with provider event ID, historical arena label, site classification and source URL. This includes **19 era-specific venue labels across 18 physical arenas** (PNC Arena and Lenovo Center are one building) and **six neutral-site events**; other games are genuine home-court games. Automated parity tests have been updated but their latest execution has not yet been confirmed. Remaining gates are historical stat-field spot checks, provisional athlete identity review, accessibility and visual sign-off. The college pages stay unpublished. See `reports/STEP4_RELEASE_READINESS.md`.
