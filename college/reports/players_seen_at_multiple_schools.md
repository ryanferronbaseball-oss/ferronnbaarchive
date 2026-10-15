# Courtside College — Players seen at multiple schools

Based on the [successful October 15, 2026 94-game ESPN import](https://github.com/ryanferronbaseball-oss/ferronnbaarchive/actions/runs/38763553107), representing **94 matched games and 1,790 raw player-game records**.

**Result: 14 distinct ESPN player IDs are present under at least two different college teams.** Cross-school identification is based on the *same ESPN athlete ID*, not a name-only comparison. These are preliminary raw-data observations; statistical leaderboards require normalized and validated box scores.

| Player | ESPN athlete ID | School appearances in attended games | Attended games |
| --- | --- | --- | ---: |
| Chad Baker-Mazara | 4700877 | San Diego State; Auburn | 5 |
| Pierre Crockrell II | 4432962 | Pacific; UC Irvine | 5 |
| Hunter Sallis | 4433281 | Gonzaga; Wake Forest | 4 |
| Tahirou Diabate | 4280209 | Portland; San Diego State | 4 |
| Andrej Stojakovic | 5175007 | Stanford; California | 2 |
| DJ Horne | 4431993 | Arizona State; NC State | 2 |
| Darrion Williams | 4937074 | Nevada; NC State | 2 |
| Lazaro Rojas | 4066681 | Fresno State; UT Arlington | 2 |
| Mady Sissoko | 4433154 | Michigan State; California | 2 |
| Noah Waterman | 4593355 | BYU; Louisville | 2 |
| Ryan Woolridge | 3906547 | North Texas; Gonzaga | 2 |
| Tre Holloman | 5105816 | Michigan State; NC State | 2 |
| Ty-Laur Johnson | 4845369 | Wake Forest; San Diego | 2 |
| Ven-Allen Lubin | 4684799 | North Carolina; NC State | 2 |

## Hunter Sallis audit example

ESPN athlete ID: `4433281` on every college box-score line.

| Date | Attendance ID | School | Raw PTS |
| --- | ---: | --- | ---: |
| 2022-02-03 | 54 | Gonzaga | 2 |
| 2024-01-22 | 78 | Wake Forest | 18 |
| 2024-11-10 | 82 | Wake Forest | 18 |
| 2025-03-13 | 91 | Wake Forest | 25 |

Raw total: **4 games, 63 points**. Source: `player_boxscores_raw.json` in the linked workflow artifact.

## Profile design rule

- One college athlete profile per stable `espn:<athlete_id>`.
- Maintain a team-at-time-of-game relationship for every appearance. Transfers never split a player's career totals.
- Provide **All Schools** cumulative totals and distinct **Per School** splits; game log sorted chronologically.
- Never merge athletes with distinct IDs only because their names match.
- Treat DNPs, raw strings, missing stats, and conflicting provider IDs conservatively until validation.
