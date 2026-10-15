# College archive — ESPN box-score completeness audit

Latest: [94-game validated ESPN import after four additional official box-score restorations (October 15, 2026)](https://github.com/ryanferronbaseball-oss/ferronnbaarchive/actions/runs/38773910953).

**Attendance matching:** 94/94 games. **Point-score reconciliation:** 91/94. **Strict point-and-minute reconciliation:** 90/94. **Games requiring backfill:** 4 (3 with missing player points, 1 with missing player minutes only). **Original ESPN rows:** 1,790. **Officially supplemented rows:** 30. **Existing ESPN rows corrected from official scores:** 9. **Total combined player lines:** 1,820. **Strictly certified player lines:** 1,742.

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

## Systematic Jase Townsend audit — all 17 attended USD games (2021–23)

The original ESPN game-summary import had **zero** Jase Townsend appearances in these seasons, even though the University of San Diego's official box scores show him playing in **14 of the 17 games attended**. Before this audit we had restored three official lines (attendance #45, #59, #68). All **eleven remaining appearances** are now appended to the sourced supplement file, using the **same stable ID** `official:san-diego:jase-townsend` across seasons. No unverified ESPN athlete ID was manufactured.

| Attendance ID | Date | Opponent | Townsend PTS | Townsend MIN | Official game box score |
|---:|---|---|---:|---:|---|
| 42 | 2021-11-09 | La Verne | 13 | 21 | [USD](https://usdtoreros.com/sports/mens-basketball/stats/2021-22/la-verne/boxscore/12401) |
| 43 | 2021-11-17 | UC Riverside | 8 | 30 | [USD](https://usdtoreros.com/sports/mens-basketball/stats/2021-22/uc-riverside/boxscore/12405) |
| 45 | 2021-11-19 | Cal State Fullerton | 14 | 32 | [USD](https://usdtoreros.com/sports/mens-basketball/stats/2021-22/cal-state-fullerton/boxscore/12406) |
| 47 | 2021-11-28 | Cal State Northridge | 3 | 33 | [USD](https://usdtoreros.com/boxscore.aspx?id=12409&path=mbball) |
| 48 | 2021-12-05 | Cal Poly | 7 | 20 | [USD](https://usdtoreros.com/sports/mens-basketball/stats/2021-22/cal-poly/boxscore/12411) |
| 50 | 2021-12-11 | Cal Lutheran | No appearance | — | [USD](https://usdtoreros.com/sports/mens-basketball/stats/2021-22/cal-lutheran/boxscore/12412) |
| 52 | 2022-01-13 | Portland | No appearance | — | [USD](https://usdtoreros.com/sports/mens-basketball/stats/2021-22/portland/boxscore/12253) |
| 53 | 2022-01-15 | Loyola Marymount | No appearance | — | [USD](https://usdtoreros.com/sports/mens-basketball/stats/2021-22/loyola-marymount/boxscore/12254) |
| 54 | 2022-02-03 | Gonzaga | 13 | 25 | [USD](https://usdtoreros.com/sports/mens-basketball/stats/2021-22/gonzaga/boxscore/12249) |
| 55 | 2022-02-05 | Santa Clara | 7 | 27 | [USD](https://usdtoreros.com/boxscore.aspx?id=12259&path=mbball) |
| 56 | 2022-11-09 | Florida Gulf Coast | 11 | 25 | [USD](https://usdtoreros.com/boxscore.aspx?id=13875&path=mbball) |
| 59 | 2022-11-17 | Utah State | 7 | 30 | [USD](https://usdtoreros.com/sports/mens-basketball/stats/2022-23/utah-state/boxscore/13877) |
| 61 | 2022-11-28 | Longwood | 15 | 36 | [USD](https://usdtoreros.com/sports/mens-basketball/stats/2022-23/longwood/boxscore/13881) |
| 63 | 2022-12-03 | UNLV | 14 | 31 | [USD](https://usdtoreros.com/sports/mens-basketball/stats/2022-23/unlv/boxscore/13883) |
| 66 | 2023-01-05 | Pacific | 12 | 36 | [USD](https://usdtoreros.com/boxscore.aspx?id=13855&path=mbball) |
| 68 | 2023-01-12 | Pepperdine | 25 | 38 | [USD](https://usdtoreros.com/sports/mens-basketball/stats/2022-23/pepperdine/boxscore/13857) |
| 72 | 2023-01-28 | San Francisco | 21 | 33 | [USD](https://usdtoreros.com/sports/mens-basketball/stats/2022-23/san-francisco/boxscore/13861) |

**Three non-appearance confirmations:** The official [Cal Lutheran (December 11)](https://usdtoreros.com/sports/mens-basketball/stats/2021-22/cal-lutheran/boxscore/12412), [Portland (January 13)](https://usdtoreros.com/sports/mens-basketball/stats/2021-22/portland/boxscore/12253), and [Loyola Marymount (January 15)](https://usdtoreros.com/sports/mens-basketball/stats/2021-22/loyola-marymount/boxscore/12254) player tables were checked separately after the attendee supplied all three source links. Townsend does not have an individual appearance in any of them, so no zero-stat or DNP record is fabricated. These were already included in the 17-game audit. A BYU box-score link was mistakenly supplied and explicitly withdrawn by the attendee; that game is **not** added to the attendance archive. The 94-game attendance list and player-stat dataset are unchanged by this confirmation.

**Attended-game totals from these fourteen official player lines: 170 PTS, 417 MIN, 14 GP (12.1 PPG)**. This is not a full USD career total. The source comparison and 17-game HTML audit run are documented at [this GitHub workflow](https://github.com/ryanferronbaseball-oss/ferronnbaarchive/actions/runs/38771801039).

Ten more games passed the strict game-level quality gate after restoring eleven Townsend appearances. **Cal Poly at San Diego on December 5, 2021 (#48) remains partial**, because Cal Poly's player totals are still short **two points and twenty minutes**; Townsend's San Diego statistics are now restored and USD's own team totals reconcile.

## Life Pacific, Hofstra, Santa Clara and Cal Poly restorations — October 15, 2026

Four user-supplied official San Diego box-score documents were compared player by player with the raw ESPN source. All four attended games now pass **both teams' final-score and full player-minute checks**.

| Attendance ID | Date | Matchup | Official player lines missing from ESPN | Existing record corrections | Result |
|---:|---|---|---|---|---|
| 8 | 2017-12-22 | Life Pacific @ San Diego | Jacob Brummett (7 PTS, 25 MIN), Chez Lister (6 PTS, 28 MIN), Adam Saavedra (0 PTS, 16 MIN) | Jonathan Cortez 23→22 MIN; Trey Huckabay 26→27 MIN | Life Pacific 51/200 MIN; San Diego 94/200 MIN |
| 30 | 2019-11-27 | Hofstra @ San Diego | Kevin Schutte (0 PTS, 7 MIN) | No incorrect player stat lines found; ESPN calls Eli Pemberton "Elijah Pemberton" | Hofstra 69/200 MIN; San Diego 79/200 MIN |
| 37 | 2020-01-25 | Santa Clara @ San Diego | Trey Wertz (7 PTS, 25 MIN) | No additional changes | Santa Clara 65/200 MIN; San Diego 52/200 MIN |
| 48 | 2021-12-05 | Cal Poly @ San Diego | Trevon Taylor (2 PTS, 21 MIN) | Tuukka Jaakkola 7→6 MIN | Cal Poly 51/200 MIN; San Diego 52/200 MIN |

Sources: [2017 San Diego vs Life Pacific official PDF](https://usdtoreros.com/documents/2018/5/10/13853__m_baskbl_2017_18_misc_non_event__USDvsLPCbox.pdf), [2019 San Diego vs Hofstra official box](https://usdtoreros.com/sports/mens-basketball/stats/2019-20/hofstra/boxscore/9522), [2020 San Diego vs Santa Clara official box](https://usdtoreros.com/sports/mens-basketball/stats/2019-20/santa-clara/boxscore/9536), [2021 San Diego vs Cal Poly official box](https://usdtoreros.com/sports/mens-basketball/stats/2021-22/cal-poly/boxscore/12411).

The PDF confirms Life Pacific's *Brummett* and *Saavedra* spellings, which differ from some third-party sources. The imported individual records and all player stat categories were checked against the corresponding official player tables. The official corrections are saved in `college/data/official_boxscore_supplements.csv` and `college/data/official_boxscore_overrides.csv` with source URLs. Original ESPN raw values are preserved in the audit archive.

These six added individual lines have **22 points and 129 player-minutes in total**, but also include two zero-point players who would not be detected by scoring reconciliation alone. Where ESPN athlete IDs are not independently confirmed, restored players use qualified official-source identifiers rather than invented ESPN IDs.

Full validation: [GitHub Actions run 38773910953](https://github.com/ryanferronbaseball-oss/ferronnbaarchive/actions/runs/38773910953). **Remaining attendance IDs: 31, 49, 64, 71.**

## Additional scoreless-player investigation

One game still reconciles every point yet fails the NCAA expected player-minute check, suggesting a missing zero-point player appearance:

| Attendance ID | Date | Matchup | Imported team minutes needing investigation |
|---:|---|---|---|
| 64 | 2022-12-10 | Denver @ UCLA | Denver 197 of 200 |

**The scoring backfill queue below contains 3 games.** The additional minute-only case brings the total open QA queue to 4.

## Backfill queue (3 games with missing player points)

| Attendance ID | Date | Matchup | Missing from away player's summed PTS | Missing from home player's summed PTS |
|---:|---|---|---:|---:|
| 31 | 2019-11-30 | Eastern Michigan @ UC Irvine | 1 | 0 |
| 49 | 2021-12-08 | Cal State Fullerton @ San Diego State | 3 | 0 |
| 71 | 2023-01-25 | Utah State @ San Diego State | 15 | 0 |

**Quality gate before integrating college into live navigation:** resolve or explicitly document all partial games; validate player rows and aggregations, preserve the exact NBA design and seven page structures, test college school-transfer player profiles, and verify mobile/desktop navigation. No production merge while audit failures remain unresolved.

The underlying workflow artifact includes full machine-readable reconciliation CSV, the normalized complete-player dataset, and the full raw import for controlled backfill.
