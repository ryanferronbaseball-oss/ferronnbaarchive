# College archive — Provisional official-source athlete identity audit

**October 15, 2026 · Development-branch audit, not a provider-ID migration.**

The sourced 94-game dataset has 1,825 unique player-game rows and 1,034 qualified player IDs. **17 athlete identities are currently qualified `official:` IDs**, restoring individuals missing from ESPN game JSON. Their appearance records and box-score sources are present and scored, but **a reliable cross-provider athlete ID has not yet been established for these 17**. Name-only matching is prohibited.

## Verified current database integrity

- 94/94 games passed a fresh score-versus-individual-scoring audit, with player points also reproduced from made field goals, made three-pointers and free throws.
- 94/94 team pairs have the expected NCAA player-minute sum, including overtime where relevant.
- All 1,825 player-game rows have unique `(attendance_id, player_id)` keys; ESPN event IDs and dates link correctly.
- Each of the 17 `official:` athlete IDs has a consistent name and one or more game-specific official box-score source URLs.
- A normalized-name scan of every existing athlete returned **zero same-name collisions** between these 17 official IDs and any different ESPN player ID **within this attendance dataset only**. This is not confirmation that ESPN has no corresponding athlete elsewhere.

| Official-source identity | School | Attended GP | PTS witnessed | Evidence |
|---|---|---:|---:|---|
| `official:life-pacific:adam-saavedra` (Adam Saavedra) | Life Pacific | 1 | 0 | [1 official box score](https://usdtoreros.com/documents/2018/5/10/13853__m_baskbl_2017_18_misc_non_event__USDvsLPCbox.pdf) |
| `official:life-pacific:chez-lister` (Chez Lister) | Life Pacific | 1 | 6 | [1 official box score](https://usdtoreros.com/documents/2018/5/10/13853__m_baskbl_2017_18_misc_non_event__USDvsLPCbox.pdf) |
| `official:colorado-2018-19:dshawn-schwartz` (D'Shawn Schwartz) | Colorado | 1 | 0 | [1 official box score](https://usdtoreros.com/sports/mens-basketball/stats/2018-19/colorado/boxscore/8128) |
| `official:utah-state:daniel-akin` (Daniel Akin) | Utah State | 2 | 36 | [2 official box scores](https://usdtoreros.com/sports/mens-basketball/stats/2022-23/utah-state/boxscore/13877) |
| `official:colorado-2018-19:eli-parquet` (Eli Parquet) | Colorado | 1 | 0 | [1 official box score](https://usdtoreros.com/sports/mens-basketball/stats/2018-19/colorado/boxscore/8128) |
| `official:colorado-2018-19:evan-battey` (Evan Battey) | Colorado | 1 | 18 | [1 official box score](https://usdtoreros.com/sports/mens-basketball/stats/2018-19/colorado/boxscore/8128) |
| `official:life-pacific:jacob-brummett` (Jacob Brummett) | Life Pacific | 1 | 7 | [1 official box score](https://usdtoreros.com/documents/2018/5/10/13853__m_baskbl_2017_18_misc_non_event__USDvsLPCbox.pdf) |
| `official:eastern-michigan:jalen-king` (Jalen King) | Eastern Michigan | 1 | 1 | [1 official box score](https://ucirvinesports.com/sports/mens-basketball/stats/2019/eastern-mich-/boxscore/6331) |
| `official:denver:james-sanders-iv` (James Sanders IV) | Denver | 1 | 0 | [1 official box score](https://denverpioneers.com/sports/mens-basketball/stats/2022-23/ucla/boxscore/12495) |
| `official:san-diego:jase-townsend` (Jase Townsend) | San Diego | 14 | 170 | [14 official box scores](https://usdtoreros.com/sports/mens-basketball/stats/2021-22/la-verne/boxscore/12401) |
| `official:denver:javonni-bickham` (JaVonni Bickham) | Denver | 1 | 0 | [1 official box score](https://denverpioneers.com/sports/mens-basketball/stats/2022-23/ucla/boxscore/12495) |
| `official:hofstra:kevin-schutte` (Kevin Schutte) | Hofstra | 1 | 0 | [1 official box score](https://usdtoreros.com/sports/mens-basketball/stats/2019-20/hofstra/boxscore/9522) |
| `official:colorado-2018-19:mckinley-wright-iv` (McKinley Wright IV) | Colorado | 1 | 14 | [1 official box score](https://usdtoreros.com/sports/mens-basketball/stats/2018-19/colorado/boxscore/8128) |
| `official:cal-state-fullerton:tory-san-antonio` (Tory San Antonio) | Cal State Fullerton | 2 | 10 | [2 official box scores](https://fullertontitans.com/sports/mens-basketball/stats/2021-22/san-diego/boxscore/2198) |
| `official:cal-poly:trevon-taylor` (Trevon Taylor) | Cal Poly | 1 | 2 | [1 official box score](https://usdtoreros.com/sports/mens-basketball/stats/2021-22/cal-poly/boxscore/12411) |
| `official:santa-clara:trey-wertz` (Trey Wertz) | Santa Clara | 1 | 7 | [1 official box score](https://usdtoreros.com/sports/mens-basketball/stats/2019-20/santa-clara/boxscore/9536) |
| `official:colorado-2018-19:tyler-bey` (Tyler Bey) | Colorado | 1 | 6 | [1 official box score](https://usdtoreros.com/sports/mens-basketball/stats/2018-19/colorado/boxscore/8128) |

## Identity safety policy

1. **Never unify on player name alone.** Match a proposed ESPN athlete ID to an independent college team roster/athlete profile plus official box-score event. Double-check year, school and jersey identity where available.
2. Preserve the existing `official:` keys, attendance ID references, game totals and source URLs until a corroborated provider crosswalk is ready.
3. On confirmed ID conversion, remap every historical appearance for the particular identity in one atomic data-rebuild update and rerun no-duplicate, appearance, transfer, and sum checks.
4. Protect regression fixtures: Jase Townsend 14 attended games / 170 points; Daniel Akin two / 36; Tory San Antonio two / 10; Hunter Sallis four / 63 (two schools).
5. No unresolved identity constitutes a license to discard its officially sourced performance. Display qualified official IDs internally, public-facing names and the correct stats.

**Status:** Provisional identities documented and scanned for current-archive collisions; **independent external provider crosswalk remains an open launch-review task**.
