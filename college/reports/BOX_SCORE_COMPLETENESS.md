# College archive — ESPN box-score completeness audit

Run: [94-game normalized ESPN import (October 15, 2026)](https://github.com/ryanferronbaseball-oss/ferronnbaarchive/actions/runs/38765641462).

**Attendance matching:** 94/94 games. **Score-reconciled player box scores:** 72/94 games. **Partial player box scores:** 22/94 games. **Retrieved individual lines:** 1,790. **Lines in verified-complete games:** 1,389.

A game is marked **complete only if the sum of individual player PTS matches the final team score for both schools**. Partial games remain in the attendance history, but raw player rows from those games are excluded from certified leaderboard totals pending verification/backfill. Excluding a game is not a claim that its player performances are wrong; it is a conservative choice while ESPN's lineup appears incomplete.

## Backfill queue

| Attendance ID | Date | Matchup | Missing from away player's summed PTS | Missing from home player's summed PTS |
|---:|---|---|---:|---:|
| 8 | 2017-12-22 | Life Pacific @ San Diego | 13 | 0 |
| 18 | 2018-11-20 | Colorado @ San Diego | 40 | 0 |
| 29 | 2019-11-20 | San Diego State @ San Diego | 20 | 0 |
| 31 | 2019-11-30 | Eastern Michigan @ UC Irvine | 1 | 0 |
| 36 | 2020-01-11 | Boise State @ San Diego State | 0 | 20 |
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
