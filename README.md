# Courtside Archive

Personal NBA attendance archive for 30 regular-season games attended between 2006 and 2018.

## Current status

- 30 attendance entries catalogued
- 30 matchups matched to historical records (research tracker status; identification still subject to audit)
- 27 final scores recorded
- 18 NBA game IDs recorded
- Complete player box score imported for **1 game only**; leaderboards are partial

## Website

The initial standalone dashboard is in `index.html`. It is designed for GitHub Pages. The leaderboard is a pilot, **not** a complete representation of all attended games.

## Data

- `data/attendance.json` — source attendance list, with original spellings preserved
- `data/import_queue.csv` — historical matching and verification tracker
- `data/pilot_games.json` — pilot game match records
- `data/pilot_player_boxscores.json` — player-level pilot statistics

## Publishing

GitHub repository Settings → Pages → Build and deployment → Deploy from a branch → `main` / `(root)` → Save.

## Next

Complete historical game ID checks, import player box scores, validate totals, and rebuild complete leaderboards.
