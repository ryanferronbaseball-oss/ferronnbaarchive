# College Baseball — Month-by-Month Review Gates

## Approval policy (confirmed October 17, 2026)

- **Approved active month:** May 2026. Continue source verification and imports for all May attended games without requiring per-game approval.
- **Next month:** April 2026 — **user-approved October 17, 2026, conditional on May finishing QA.** Finish May's full official player gamebooks, run data and desktop/mobile quality checks, and then begin April without asking again. Present a May completion summary when ready.
- **March 2026:** user-approved October 17, 2026, conditional on April's player gamebooks and QA reaching the April completion checkpoint. No need to ask again for March.\n- After completing March, request separate explicit approval before beginning **February 2026**, and then **2025** (work backward through 2025).
- For every month: preserve all original attendance rows; match official scores/innings, hitting/pitching player lines, lineup slots and replacements; verify player IDs; record sources; distinguish complete gamebooks from score-only records; flag ambiguities. Never fabricate missing statistics.
- Month progression and **publication** are separate approvals. Do not merge the college baseball draft to main merely because an import month is approved.

## May 2026 audit checkpoint

27 attended games, all identified in the attendance master. As checked on October 17, 2026, 22 completed official gamebooks were present at the beginning of this conversation, including all eight May 20–23 SEC tournament games and six Auburn Regional games. Additional May sources have since been located; count progress dynamically from `data/games.json` because the draft may change while work is ongoing.

Previously outstanding May gamebook sources (all five official sources located):
1. May 16 Arkansas at Kentucky: https://arkansasrazorbacks.com/stats/baseball/2026/ark55.htm — Arkansas 16, Kentucky 12
2. May 10 Little Rock at UT Martin: https://utmsports.com/sports/baseball/stats/2026/little-rock/boxscore/13609 — Little Rock 16, UT Martin 14
3. May 5 Louisville at Vanderbilt: https://gocards.com/sports/baseball/stats/2026/vanderbilt/boxscore/26027 — Louisville 6, Vanderbilt 12
4. May 3 Tennessee at Kentucky: https://utsports.com/sports/baseball/stats/2026/kentucky/boxscore/29752 — Tennessee 10, Kentucky 9
5. May 1 Tennessee at Kentucky: https://utsports.com/sports/baseball/stats/2026/kentucky/boxscore/29750 — Tennessee 2, Kentucky 9

**May gate:** The 27/27 May gamebooks and May data-integrity audit passed; April is underway. **April gate:** March may begin automatically after all 14 April player gamebooks and month-level QA pass, as explicitly approved by the user on October 17, 2026. February and 2025 still require separate approvals.\n\n**Source located is not full statistical verification.** Do not promote any game to `official_boxscore_verified` until individual batter/pitcher lines, replacements, order and source team totals have been reconciled. After May is complete, stop at the approval checkpoint and request April permission.
