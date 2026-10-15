# College Step 4 — sourced venue completion and release readiness

**Updated October 15, 2026.** Branch: `college-import-pilot`; no merges to NBA `main`, production navigation or live site.

## Verified venue completion

- **94 of 94** attended game locations have a dated source record in `college/data/verified_venues.csv`; zero missing venue fields.
- **19 historical arena labels**, representing **18 physical basketball venues**. Raleigh's same arena was named PNC Arena in the January 2024 game and Lenovo Center in the 2025 games. The historical name is preserved in game detail while venue insights group the building under its newer name.
- **Six verified neutral-site games:** attendance IDs **60, 76, 80, 82, 90 and 91**. The California at San Diego State 2023 SoCal Showcase (#76) was played at the Pavilion at JSerra in San Juan Capistrano, not Viejas Arena. Listed home/away teams are unchanged from the source.
- Historical school and conference sources include university box scores (San Diego, UC Irvine, UC San Diego), UCLA and SDSU published schedules, West Coast Conference dated results and the ACC tournament venue declaration.
- `verified_venues.csv` records attendance ID, ESPN event ID, date-specific arena label, neutral/home designation, public source URL and citation description for **every game**.
- The deterministic site data adapter reapplies venue facts after regenerating ESPN data, checks provider event IDs and unique attendance IDs, and rejects unsourced venue insertions.

## Dataset preserved

- 94 matched games, 1,825 certified player appearances, 1,034 player identities, 75 distinct school IDs, and 14 players with appearances at multiple schools.
- Every game's final score and team player-minute totals were previously reconciled. This does **not** establish independent field-by-field accuracy for all advanced metrics.

## Regression changes committed

- A new independent 240-field official university box-score fixture guards against subtle errors masked by valid game totals. See `scripts/test_official_spotchecks.py`.

- Structural seven-page checks now assert **94 venue joins**, **19 era-specific names**, **18 physical arena identities**, **six neutral games**, and source URLs aligned with each unique attendance ID and ESPN event ID.
- Browser checks target historic Viejas/Jenny Craig locations, two different SoCal neutral-site games, aggregate venue leaderboards, 18 physical venue KPI, and mobile home/insights views.
- Browser test report status now depends on completing **all assertions**, not merely absence of JavaScript errors.
- Search/filter accessible names were previously added on five college pages; full assistive-technology and keyboard testing is still required.

**Final integrated QA PASS (October 15, 2026):** [GitHub Actions run](https://github.com/ryanferronbaseball-oss/ferronnbaarchive/actions/runs/38788094542) executed all newly updated checks successfully, including **57 seven-page desktop/mobile assertions**, **22 player statistics/profile browser assertions**, the **240-cell official source regression** and structural parity checks, with zero unhandled JavaScript page errors. Mobile home, stats and insights did not overflow the device width. We also verified keyboard navigation between homepage search and date filtering. [Download the seven-page screenshot and browser-report preview](https://github.com/ryanferronbaseball-oss/ferronnbaarchive/actions/runs/38788094542/artifacts/11998103847).

## Outstanding launch blockers

1. **Complete:** Fresh combined browser and structural CI passed; see the linked Oct 15 Action run and screenshot artifact.
2. Review 17 qualified provisional official-source player IDs against independent athlete identity evidence; never merge by name only.
3. **Continue** independent source audits beyond the 240 fields now checked in 15 player rows from three games. The spot checks found and repaired five Colorado individual-stat errors while preserving team scoring/minutes, so broader field-level review is still worthwhile. See `reports/OFFICIAL_STAT_SPOTCHECKS.md`.
4. Desktop/mobile browser layouts, named controls and a keyboard path passed automated smoke checks. **Still requires human visual acceptance, full keyboard/assistive-technology navigation and WCAG contrast audit.**
5. Explicit **user acceptance** before merging, publishing, or adding college navigation to the NBA production archive.

**Venue research: COMPLETE. Integrated browser CI: PASS. Production launch: NOT APPROVED / NOT YET PUBLISHED.**
