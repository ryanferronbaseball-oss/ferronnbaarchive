# MiLB Archive

Standalone eighth sport. Only add verified attended games and official player stat lines.

- games.json rows: id, date, source_game_id, home_team, away_team, home_score, away_score, level, venue.
- player_stats.json rows: game_id, player_id, name, team, batting and/or pitching objects with h, hr, rbi, ip, so.
- player_links.json rows: milb_id, mlb_id, college_id. Only confirmed identity links.

No fabricated attendance or scores. The archive begins with zero records until the user's actual MiLB games are identified.
