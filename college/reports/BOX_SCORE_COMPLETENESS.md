# College archive — ESPN box-score completeness audit

Latest: [94-game import with sourced corrections and NCAA team-minute validation (October 15, 2026)](https://github.com/ryanferronbaseball-oss/ferronnbaarchive/actions/runs/38767303519).

**Attendance matching:** 94/94 games. **Point-score reconciliation:** 74/94 games after two official school box-score corrections. **Strict score-and-team-minute reconciliation:** 72/94 games. **Games needing backfill:** 22 (20 with missing points, 2 with missing minutes but complete scoring). **Original ESPN lines:** 1,790. **Officially supplemented lines:** 2. **Combined lines:** 1,792. **Lines in strictly verified games:** 1,389.

A game is marked **complete only when both teams' player points match their final scores AND their player-minute totals match NCAA regulation or overtime expectations**. Partial games remain in the attendance history, but raw player rows from those games are excluded from certified leaderboard totals pending verification/backfill. Excluding a game is not a claim that its player performances are wrong; it is a conservative choice while ESPN's lineup appears incomplete.

## Verified repairs from official school records

The original ESPN summaries omitted **Yanni Wetzell (ESPN athlete ID 4077221)** from two games, each causing a 20-point discrepancy. Both complete rows are now sourced from official box scores and recorded in `college/data/official_boxscore_supplements.csv`:

- **Attendance #29:** November 20, 2019 — San Diego State 66, San Diego 49. Wetzell: 27 MIN, 20 PTS, 12 REB, 1 AST. [Official San Diego box score](https://usdtoreros.com/sports/mens-basketball/stats/2019-20/san-diego-state/boxscore/9520).
- **Attendance #36:** January 11, 2020 — San Diego State 83, Boise State 65. Wetzell: 31 MIN, 20 PTS, 5 REB, 4 AST. [Official Boise State box score](https://broncosports.com/sports/mens-basketball/stats/2019/san-diego-state/boxscore/14335).

Corrected imports verify **both teams' point AND minute totals** in these two games. Original ESPN raw data is preserved, supplements have explicit provenance, and duplicate athlete appearances are prohibited.

## Additional scoreless-player investigation

Two games still reconcile every point yet fail the NCAA expected player-minute check, suggesting missing zero-point player appearances:

| Attendance ID | Date | Matchup | Imported team minutes needing investigation |
|---:|---|---|---|
| 30 | 2019-11-27 | Hofstra @ San Diego | Hofstra 193 of 200 |
| 64 | 2022-12-10 | Denver @ UCLA | Denver 197 of 200 |

**The scoring backfill queue below contains 20 games.** These additional 2 minute-only cases bring the total open QA queue to 22.

## Backfill queue (20 games with missing player points)

| Attendance ID | Date | Matchup | Missing from away player's summed PTS | Missing from home player's summed PTS |
|---:|---|---|---:|---:|
| 8 | 2017-12-22 | Life Pacific @ San Diego | 13 | 0 |
| 18 | 2018-11-20 | Colorado @ San Diego | 40 | 0 |
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
