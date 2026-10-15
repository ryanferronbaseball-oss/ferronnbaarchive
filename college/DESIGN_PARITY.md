# Courtside Archive — NBA / College Design Parity Contract

**Decision:** the existing NBA archive is the implementation reference for the NCAAB module. Preserve its *actual page markup, shared assets, editorial ivory-and-evergreen CSS, layout, controls, and information architecture* rather than approximating the design with a new framework.

## Source pages, one-to-one

| Existing NBA source | College counterpart | Parity commitment |
| --- | --- | --- |
| `index.html` | `college/index.html` | Identical overview structure, feature cards, attendance summary, and highlighted performances |
| `game.html` | `college/game.html` | Identical game selector, scoreboards, team box scores, player-of-game, highlights, and next/previous navigation |
| `stats.html` | `college/stats.html` | Identical searchable sortable player leaderboard, traditional and advanced tabs, columns, and eligibility rules |
| `player.html` | `college/player.html` | Identical hero, aggregate stats, tab layout, and chronological unified game log; support school filter as an additive control |
| `records.html` | `college/records.html` | Identical single-game records and stat search/sort behavior |
| `milestones.html` | `college/milestones.html` | Identical records, milestones, school/team achievements, legendary-performance navigation |
| `insights.html` | `college/insights.html` | Identical attendance metrics, timeline, venue, team/school and player insights |

The college pages should point to **the same canonical stylesheet** `../assets/site.css` and share behavior/utilities where practical. The NBA visual rules and mobile breakpoints are the acceptance standard. No college-only redesign, different colors, arbitrary omissions of panels, or rearranged navigation. Copy existing page structure first; introduce reusable views only if resulting appearance and interactions remain equivalent.

## Data adapter: preserve the NBA UI contract

The existing pages consume `data/games.csv` and `data/player_boxscores_espn.json`. The college importer currently produces `college/output/matches.csv` and `college/output/player_boxscores_raw.json` in a GitHub Actions artifact. **These are not frontend-ready yet.**

Generate `college/data/games.csv` and `college/data/player_boxscores_espn.json` that preserve the existing UI key names and meanings:

- Game: `id` (stable attendance ID), `date`, `away`, `home`, `arena` (where verified), `away_score`, `home_score`, `boxscore_status`; retain ESPN event ID as a separate field.
- Player game: `player_id` (provider-qualified stable ESPN athlete ID), `player`, `team_id`, `espn_event_id`, `date`, `minutes`, `pts`, `reb`, `ast`, `stl`, `blk`, `fgm`, `fga`, `fg3m`, `fg3a`, `ftm`, `fta`, `to`, and any additional existing NBA-required columns.
- Keep missing/absent fields as null, not zero. Validate athlete counts and each team's sum of recorded points against the official scoreboard before publishing.

Use the NCAA ESPN URL and player headshot path rather than the NBA equivalents. Replace static NBA team-ID/name maps with verified college school IDs and historical school names. Neutral-site games and college venues should be represented accurately without altering the visual hierarchy.

## Unified player profiles across transfers

**One college profile per `espn:<athlete_id>`**. Accumulate every game the user attended regardless of school, sorted chronologically in **one game log**, matching the existing Lamar Odom/Lakers/Clippers NBA behavior. Add **All Schools** (default) / **School A** / **School B** filters without removing the full log. Overall totals use all selected attended appearances; school splits use only that school's appearances. Never join separate athlete IDs solely by matching names.

## Statistical parity

Keep the existing NBA traditional metrics, percentages, minimum-attempt filters, per-36 columns, per-game rates, sorting, milestones, and advanced/derived measures. College-specific supplemental per-40 may be offered **in addition to**, not instead of, the established NBA measures. Where ESPN lacks an input, show `—` and annotate the gap; don't silently replace a column or invent values. Do not expose raw unvalidated totals as official archive records.

## Shipping checklist

1. Normalize and verify the 94 matched game IDs and 1,790 raw player-game lines.
2. Port pages **one-to-one** and supply compatible college data, using the shared NBA visual assets.
3. Audit every page against the live NBA version at desktop and mobile widths: same page groups, sections, controls, colors, typography, responsive patterns, links, and statistics.
4. Validate cross-school profiles (especially Hunter Sallis and the 13 additional identified college transfers).
5. Only then link the college module from the master navigation. The currently published NBA pages are not to be changed or broken during this process.
