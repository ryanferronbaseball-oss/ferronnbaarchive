# College Baseball — Month-by-Month Review Gates

## October 17, 2026 — Entire 2024 season authorized

**User explicitly approved moving to 2024** after the 2025 backfill reached 69/74 verified gamebooks. The new authorized boundary is **2024–2026 only**. Continue source-backed 2025 fixes as needed; beginning 2024 does **not** silently mean the remaining 2025 source exceptions are complete.

The original attendance workbook records **71 games in 2024**: **June 6, May 16, April 7, March 25, February 17**. All listed matchups are four-year colleges (including NCAA Division II Point Loma Nazarene, Angelo State, Indianapolis and Tampa), so they are eligible under the current rules, subject to game-specific validation. **JUCO/NJCAA remains excluded** and retained attendance-only. Preserve the exact 444 original workbook rows and IDs; source-verify 2024 games from June backward, individually verifying university boxscore identity, official venue/neutral-site, correct home-away official R/H/E and innings, source starter positions 1–9 with substitutes, all individual batting/pitching records and W/L/S.

Special checks: 2024 March 23 Vanderbilt–South Carolina has **two same-date matches**, reconcile Game 1 versus Game 2 against official evidence and never silently assume workbook ordering. March 30 South Alabama–Old Dominion workbook year was corrected to 2024 on earlier explicit user instruction, with conflicting weekday metadata: validate official actual date. Preserve the NCAA DII contests regardless of difficulty locating source gamebooks; do not count them complete without verified source. 2023 and earlier are **not approved**; no merge or publication is approved.

## 2025 monthly review gate — CURRENT (October 17, 2026)

User approval for full **2025** backfill is active. **23 of 74** official full player gamebooks verified and imported; May **23/29**, June **0/2**, April **0/10**, March **0/19**, February **0/14**. **51 2025 games remain**. The 26 linked official source entries include three held back: two one-page LSU regional PDFs requiring standalone, source-audited player transcription and Dallas Baptist–Little Rock requiring an accessible complete university scorebook. **48 further attendance games need official source discovery**; those are not equivalent to source failure and must not be silently counted completed.

References: `data/2025_monthly_progress_audit.json` (per-game pending queue and summary), `data/2025_source_import_audit.json` (source-check exceptions), `data/2025_official_source_queue.json` (official links). 2026 remains **68/68 complete**, no change in the 444 original attendance entries, and **no 2024-or-earlier imports or publication** are approved.

## October 17, 2026 — 2025 season approved

**New authorization:** After completion of all 68 eligible 2026 gamebooks, user explicitly approved processing the **entire 2025 college baseball attendance slate**, newest to oldest. 2025 attendance contains **74 original games**: June 2, May 29, April 10, March 19, February 14. All currently listed schools appear to be four-year programs; any subsequently verified NJCAA/junior-college game must be retained as attendance-only and excluded. Apply the same individual official source, inning/R-H-E, original nine-slot batting order, player statistics, pitching W/L/S, and monthly integrity audit standards as 2026.

**Do not** continue into 2024 or earlier or merge/publish the draft without further explicit user approval. The 2026 audit remains complete and untouched. Previous statements below that 2025 has not been approved are historical, superseded by this authorization.

## October 17, 2026 — Junior-college exclusion (latest scope decision)

**User decision:** Ignore **all junior-college / NJCAA games** for box-score/statistical backfill in this archive, including older seasons. Retain the original 444-row personal attendance source and its stable IDs for provenance; mark known JUCO entries `boxscore_backfill_excluded: true` with reason `junior_college`. They are not missing/blocked games and must not count toward monthly backfill completion denominators or missing-source queues. Do not research, infer stats for, or import JUCO gamebooks. NCAA and other eligible four-year college matchups continue normally; never mistake NCAA DIII **Wabash College** for NJCAA **Wabash Valley College**.

Seven 2026 exclusions: January 23 Walters State–USC Salkehatchie (2); February 12–13 Walters State–Pellissippi State (3); March 20 Wabash Valley–Walters State (2). Thus 2026 eligible games are **68 of 75**: January **0 of 2**, February **8 of 11**, March **19 of 21**, April **14 of 14**, May **27 of 27**. May/April are complete; March finished at 19/19 and February at 8/8; January requires no JUCO sourcing. The 2026 slate is complete and verified. Previous JUCO discovery notes are superseded by this decision. Approval for all of 2026 remains intact; 2025 and publication/merge remain unapproved.


## 2026 NCAA all-month gate — PASSED (October 17, 2026)

Every approved 2026 NCAA/four-year game now has an officially reconciled player scorebook: **May 27/27, April 14/14, March 19/19, February 8/8, January 0/0**. The **7 junior-college exclusions** remain attendance-only and do not count as missing. **68/68 eligible complete; 1,990 player-game stat lines; 444 original attendance records preserved.** This supersedes all interim monthly snapshots below. Full validation: [2026 season audit](data/2026_full_slate_monthly_integrity_audit.json); [official Notre Dame PDF audit](data/2026_mar01_notredame_tenntech_pdf_audit.json). **Do not work on 2025 or publish/merge this branch without fresh authorization.**

## Approval policy (updated October 17, 2026)

- **Approved:** May, April, March, February, and January **2026**. Continue newest-to-oldest after each month's source and integrity checks; do not wait for an additional approval.
- **Not approved:** 2025 or earlier imports, or publication/merging the draft into `main`.
- Preserve all 444 original attendance entries, source-match each individual game (including same-day doubleheaders), verify official batting/pitching lines, lineup slots, replacements and team totals. Missing/unreliable records remain attendance-only or score-only without fabricated player statistics.
- Each month should receive an auditable checkpoint; unresolved historical sources can be listed in a clearly separated review queue rather than silently treated as complete.

## October 17, 2026 — Expanded full-season approval

**User explicitly approved continuing throughout ALL of 2026** in chronological reverse order, including the remainder of March, all of February, and the two January attendance entries. Month-by-month completion and source audits remain required, but **no separate user authorization is needed to cross 2026 month boundaries**. Work on the 2025 season and publication/merging into main are **not approved**. Preserve source-missing or ambiguous games as incomplete and flag them for review instead of inventing stats.

## May 2026 audit checkpoint

27 attended games, all identified in the attendance master. As checked on October 17, 2026, 22 completed official gamebooks were present at the beginning of this conversation, including all eight May 20–23 SEC tournament games and six Auburn Regional games. Additional May sources have since been located; count progress dynamically from `data/games.json` because the draft may change while work is ongoing.

Previously outstanding May gamebook sources (all five official sources located):
1. May 16 Arkansas at Kentucky: https://arkansasrazorbacks.com/stats/baseball/2026/ark55.htm — Arkansas 16, Kentucky 12
2. May 10 Little Rock at UT Martin: https://utmsports.com/sports/baseball/stats/2026/little-rock/boxscore/13609 — Little Rock 16, UT Martin 14
3. May 5 Louisville at Vanderbilt: https://gocards.com/sports/baseball/stats/2026/vanderbilt/boxscore/26027 — Louisville 6, Vanderbilt 12
4. May 3 Tennessee at Kentucky: https://utsports.com/sports/baseball/stats/2026/kentucky/boxscore/29752 — Tennessee 10, Kentucky 9
5. May 1 Tennessee at Kentucky: https://utsports.com/sports/baseball/stats/2026/kentucky/boxscore/29750 — Tennessee 2, Kentucky 9

**May gate:** The 27/27 May gamebooks and May data-integrity audit passed; April is underway. **April gate:** March may begin automatically after all 14 April player gamebooks and month-level QA pass, as explicitly approved by the user on October 17, 2026. February and 2025 still require separate approvals.\n\n**Source located is not full statistical verification.** Do not promote any game to `official_boxscore_verified` until individual batter/pitcher lines, replacements, order and source team totals have been reconciled. After May is complete, stop at the approval checkpoint and request April permission.
