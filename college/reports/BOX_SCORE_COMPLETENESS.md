# College archive — ESPN box-score completeness audit

Latest: [94-game import with official Utah State, Pepperdine and Cal State Fullerton repairs (October 15, 2026)](https://github.com/ryanferronbaseball-oss/ferronnbaarchive/actions/runs/38770568094).

**Attendance matching:** 94/94 games. **Point-score reconciliation:** 78/94. **Strict point-and-minute reconciliation:** 76/94. **Games requiring backfill:** 18 (16 missing points, 2 incomplete minutes with scoring complete). **Original ESPN rows:** 1,790. **Officially supplemented rows:** 13 (2 Wetzell, 6 Colorado, 5 across the three new repairs). **Corrected pre-existing ESPN rows:** 6. **Strictly certified rows:** 1,463.

A game is marked **complete only when both teams' player points match their final scores AND their player-minute totals match NCAA regulation or overtime expectations**. Partial games remain in the attendance history, but raw player rows from those games are excluded from certified leaderboard totals pending verification/backfill. Excluding a game is not a claim that its player performances are wrong; it is a conservative choice while ESPN's lineup appears incomplete.

## Verified repairs from official school records

The original ESPN summaries omitted **Yanni Wetzell (ESPN athlete ID 4077221)** from two games, each causing a 20-point discrepancy. Both complete rows are now sourced from official box scores and recorded in `college/data/official_boxscore_supplements.csv`:

- **Attendance #29:** November 20, 2019 — San Diego State 66, San Diego 49. Wetzell: 27 MIN, 20 PTS, 12 REB, 1 AST. [Official San Diego box score](https://usdtoreros.com/sports/mens-basketball/stats/2019-20/san-diego-state/boxscore/9520).
- **Attendance #36:** January 11, 2020 — San Diego State 83, Boise State 65. Wetzell: 31 MIN, 20 PTS, 5 REB, 4 AST. [Official Boise State box score](https://broncosports.com/sports/mens-basketball/stats/2019/san-diego-state/boxscore/14335).

Corrected imports verify **both teams' point AND minute totals** in these two games. Original ESPN raw data is preserved, supplements have explicit provenance, and duplicate athlete appearances are prohibited.

## Colorado @ San Diego: restored 6 players and corrected 2 existing records

**Attendance #18 (November 20, 2018)** previously had 40 unaccounted Colorado points. The [San Diego official box score](https://usdtoreros.com/sports/mens-basketball/stats/2018-19/colorado/boxscore/8128), independently confirmed by [Colorado's own box-score reproduction](https://cubuffs.com/documents/download/2019/11/15/cunotes_san_diego.pdf), establishes six Colorado players absent from ESPN's returned box score: Evan Battey (18), McKinley Wright IV (14), Tyler Bey (6), Daylen Kountz (2), D'Shawn Schwartz (0), and Eli Parquet (0). We added all six from the official stats including zero-point players, not merely the 40 missing points.

We also reconciled Shane Gatling's official turnover count (1, ESPN had 0) and Namon Wright's minutes (18, ESPN had 14). Official corrections are in `college/data/official_boxscore_overrides.csv`, preserving original ESPN values in `official_override_audit.json` (workflow artifact). Cross-checking aggregate steals and blocks confirmed the original ESPN steal/block values for the three pre-existing Colorado player rows; no unnecessary changes remain.

**Verified result:** Colorado 64 points in **200 player-minutes**, San Diego 70 points in **200 player-minutes**; 11 Colorado and 9 San Diego individual stat lines. The NCAA game now passes both validation checks.

**Identity status:** Daylen Kountz's restored appearance uses his verified ESPN athlete ID `espn:4397060`. The other five restored appearances have distinct, provider-qualified official-source IDs (not falsely invented ESPN IDs), pending future corroboration against official player identity records.

## Utah State, Pepperdine, and Cal State Fullerton repairs (October 15, 2026)

Three official university box scores resolved three additional attended games, with each team matching both its official score and expected individual player minutes:

| Attendance ID | Date | Matchup | Missing official player lines restored | Additional official corrections | Post-repair verification |
|---:|---|---|---|---|---|

Primary sources: [Cal State Fullerton official box score](https://fullertontitans.com/sports/mens-basketball/stats/2021-22/san-diego/boxscore/2198), [San Diego official Utah State box score](https://usdtoreros.com/sports/mens-basketball/stats/2022-23/utah-state/boxscore/13877), and [San Diego official Pepperdine box score](https://usdtoreros.com/sports/mens-basketball/stats/2022-23/pepperdine/boxscore/13857).

**Identity handling:** The three restored Jase Townsend performances share a single stable `official:san-diego:jase-townsend` ID. Daniel Akin and Tory San Antonio also use distinct source-qualified provisional IDs. These are deliberately **not labeled ESPN IDs**; map them to independently verified ESPN IDs later if available. Existing ESPN lines retain their original ESPN identity. In `official_boxscore_overrides.csv`, player-level ESPN mistakes are corrected without altering the original raw import; `official_override_audit.json` records before and after for every override.

The [completed full archive QA run](https://github.com/ryanferronbaseball-oss/ferronnbaarchive/actions/runs/38770568094) confirms all three games as `complete`, including overtime team-minute reconciliation in Utah State–San Diego.

## Additional scoreless-player investigation

Two games still reconcile every point yet fail the NCAA expected player-minute check, suggesting missing zero-point player appearances:

| Attendance ID | Date | Matchup | Imported team minutes needing investigation |
|---:|---|---|---|
| 30 | 2019-11-27 | Hofstra @ San Diego | Hofstra 193 of 200 |
| 64 | 2022-12-10 | Denver @ UCLA | Denver 197 of 200 |

**The scoring backfill queue below contains 16 games.** These additional 2 minute-only cases bring the total open QA queue to 18.

## Backfill queue (16 games with missing player points)

| Attendance ID | Date | Matchup | Missing from away player's summed PTS | Missing from home player's summed PTS |
|---:|---|---|---:|---:|
| 8 | 2017-12-22 | Life Pacific @ San Diego | 13 | 0 |
| 31 | 2019-11-30 | Eastern Michigan @ UC Irvine | 1 | 0 |
| 37 | 2020-01-25 | Santa Clara @ San Diego | 7 | 0 |
| 42 | 2021-11-09 | La Verne @ San Diego | 0 | 13 |
| 43 | 2021-11-17 | UC Riverside @ San Diego | 0 | 8 |
| 45 | 2021-11-19 | Cal State Fullerton @ San Diego | 7 | 14 |
| 47 | 2021-11-28 | Cal State Northridge @ San Diego | 0 | 3 |
| 48 | 2021-12-05 | Cal Poly @ San Diego | 2 | 7 |
| 49 | 2021-12-08 | Cal State Fullerton @ San Diego State | 3 | 0 |
| 54 | 2022-02-03 | Gonzaga @ San Diego | 0 | 13 |
| 55 | 2022-02-05 | Santa Clara @ San Diego | 0 | 7 |
| 56 | 2022-11-09 | Florida Gulf Coast @ San Diego | 0 | 11 |
| 59 | 2022-11-17 | Utah State @ San Diego | 21 | 7 |
| 61 | 2022-11-28 | Longwood @ San Diego | 0 | 15 |
| 63 | 2022-12-03 | UNLV @ San Diego | 0 | 14 |
| 66 | 2023-01-05 | Pacific @ San Diego | 0 | 12 |
| 68 | 2023-01-12 | Pepperdine @ San Diego | 2 | 25 |
| 71 | 2023-01-25 | Utah State @ San Diego State | 15 | 0 |
| 72 | 2023-01-28 | San Francisco @ San Diego | 0 | 21 |

**Quality gate before integrating college into live navigation:** resolve or explicitly document all partial games; validate player rows and aggregations, preserve the exact NBA design and seven page structures, test college school-transfer player profiles, and verify mobile/desktop navigation. No production merge while audit failures remain unresolved.

The underlying workflow artifact includes full machine-readable reconciliation CSV, the normalized complete-player dataset, and the full raw import for controlled backfill.
