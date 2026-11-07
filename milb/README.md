# MiLB Archive

Standalone eighth sport. Only add verified attended games and official player stat lines.

- games.json rows: id, date, source_game_id, home_team, away_team, home_score, away_score, level, venue.
- player_stats.json rows: game_id, player_id, name, team, batting and/or pitching objects with h, hr, rbi, ip, so.
- player_links.json rows: milb_id, mlb_id, college_id. Only confirmed identity links.

No fabricated attendance or scores. The archive begins with zero records until the user's actual MiLB games are identified.

## Navigation and alumni workflow
Five top-level MiLB pages: Overview, Games, Players, Records, To the MLB (`mlb-alumni.html`). No Hall of Fame or Statcast MiLB pages.

`player_links.json` is a manual, confirmed identity registry, **not** a speculative prospect list. Add `milb_id`, `mlb_id`, and optional `college_id` only after checking that the player has actually appeared in an MLB regular-season/postseason game and that all linked player IDs refer to the same individual. Keep non-debuted prospects off To the MLB. Preserve MiLB and MLB statistics separately. Do not bulk-create player links from names alone.
