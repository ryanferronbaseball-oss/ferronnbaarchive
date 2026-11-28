# College sports expansion — initial inventory and parity contract

Confirmed by archive owner: 5 women's basketball games, 7 men's soccer matches, 4 women's indoor volleyball matches. See each new sport's data/attendance_seed.json. This is a staging inventory, not a complete player-stat import. Official dates override recalled dates; original dates retained for traceability. Scores are points, goals, or sets as indicated. Source URLs may be schedules or recaps; retrieve the full game-specific box score before marking import complete. Carolina University result uses the official Lipscomb recap; cross-check the official PDF before importing player rows.

## Women's basketball (college-women)
Mirror college/index.html, game.html, stats.html, player.html, records.html and insights.html visually and functionally. Reuse shared palette and portrait-fit CSS. Preserve men's archive unchanged; use independent data and IDs, female ESPN headshot paths, WNBA rather than NBA career tags, four-quarter scoring (plus OT). Use existing Hollinger game-score methodology and the college threshold; compute advanced stats only when inputs exist. Recaps above player of game. Do not copy men's records or player tags.

## Men's college soccer (college-soccer)
Mirror soccer/ page shells, archive.css, and scorecard, timeline, lineup, goals, records, profile and Player of the Match presentation. Separate data from professional soccer; adapt to college match reports, including two credited assists where officially documented, historical golden-goal overtime and player minutes when available. Verify player appearances and events before computing records. Do not fabricate possession, xG, substitutions, or missing stats. Use university logos.

## Women's volleyball (college-volleyball)
Match archive navigation, burgundy/ice-blue palette, game cards, portraits, team logos and recap placement. Proposed statistical display pending owner refinement:
- Match scoreboard: sets won and point-by-point set totals; mark winner of each set. Team comparison: kills, errors, attempts, hitting percentage, assists, aces, service errors, digs, blocks.
- Box score: SP, K, E, TA, HIT%, AST, SA, SE, DIG, BS, BA, PTS; preserve reception errors, block errors and ball handling errors when reported. Points = K + SA + BS + BA/2. Hitting percentage = (K-E)/TA, undefined if TA=0.
- Profiles and leaderboards: matches, sets, totals, kills/set, assists/set, digs/set, blocks/set (BS+BA per player), aces/set, points/set, cumulative hitting percentage calculated from summed counts. Keep official team block totals separate from individual block totals.
- Position-aware leaderboards and match honors: hitters (kills and efficiency), setters (assists), liberos (digs and receiving when available), middle blockers (blocks and hitting efficiency). No universal Player of the Match formula adopted yet.
- Recaps above Player of the Match; no missing data rendered as zero.

## Integration acceptance criteria
Import and reconcile all 16 official box scores, with traceable sources and no invented player rows. Validate scores and identities, game/profile links, mobile and desktop rendering, and navigation parity. Then add all three sports to global navigation, homepage totals, venue map, chronological milestones, calendar, yearbook, college pages, player search and photo intake. Count each event once; preserve existing sports. Keep these staging files out of public aggregate counts until integration is complete. No new public pages or global changes in this initial inventory commit.
