# Independently verified college player-stat spot checks — October 15, 2026

**Status: 240 of 240 selected fields match dated university box scores.**
This is a focused verification sample, not a claim that every one of the 1,825 historical player-game lines has been independently audited field by field.

| Attendance | Source game | Players checked | Fields per player | Result |
|---|---|---:|---:|---|
| #18 (Nov 20, 2018) | [Colorado 64 at San Diego 70](https://usdtoreros.com/sports/mens-basketball/stats/2018-19/colorado/boxscore/8128) | 11 Colorado athletes | 16 | 176/176 match after corrections |
| #29 (Nov 20, 2019) | [San Diego State 66 at San Diego 49](https://usdtoreros.com/sports/mens-basketball/stats/2019-20/san-diego-state/boxscore/9520) | Yanni Wetzell | 16 | 16/16 |
| #59 (Nov 17, 2022) | [Utah State 91 at San Diego 89 (OT)](https://usdtoreros.com/sports/mens-basketball/stats/2022-23/utah-state/boxscore/13877) | Jase Townsend, Daniel Akin, Eric Williams Jr. | 16 | 48/48 |

**Compared fields:** MIN; FGM, FGA; 3PM, 3PA; FTM, FTA; OREB, DREB, REB; PF; AST; individual TO; BLK; STL; PTS.

## Historical Colorado correction found through field-level comparison

Earlier all-game scoring and minute reconciliations passed, yet multiple Colorado *individual* lines at San Diego on November 20, 2018 diverged from the published official table. The following values were corrected in the source-controlled official override/supplement files AND in the served college player fixture:

| Player | Stat | Old archive | Official correction |
|---|---|---:|---:|
| D'Shawn Schwartz | Minutes | 23 | 25 |
| Evan Battey | Minutes | 28 | 30 |
| McKinley Wright IV | Individual turnovers | 4 | 5 |
| Namon Wright | Minutes | 18 | 14 |
| Shane Gatling | Individual turnovers | 1 | 0 |

**Why team-level QA missed them:** the 4 redistributed minutes offset each other, and the two individual turnover errors offset each other. Team minutes still equal 200 and points remain 64. The official Colorado box-score turnover total is 14, of which **11 belong to players and three are team turnovers**. Team turnovers must not be assigned arbitrarily to individual players.

The updated regression at `college/scripts/test_official_spotchecks.py` pins these 15 official player rows and 240 stat values. CI invokes it before browser page parity checks; the newly updated CI run still requires confirmation.

## Remaining quality policy

- Preserve the original raw ESPN imports and the dated school sources for every override. `college/data/official_boxscore_overrides.csv` captures existing ESPN-row corrections; `college/data/official_boxscore_supplements.csv` captures originally omitted player lines.
- Prioritize further varied-era field-by-field samples. Passing points and total minutes does not certify every assist, rebound, block, personal foul or shooting rate in the rest of the dataset.
- Continue the 17 provisional athlete identity crosswalk investigation only with corroborated provider records; no name-based consolidation.
