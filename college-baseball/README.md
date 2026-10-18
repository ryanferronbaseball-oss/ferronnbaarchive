# College Baseball · Courtside Archive

**Status (October 17, 2026):** Unpublished draft PR #10 retains 444 original attendance records. **2021: 27/32 university full player gamebook links, 5 audit exceptions and 0/32 imports**; **2022: 62/62 source gamebooks linked, 0/62 imports**; **2023: 47/47 sources linked, 0/47 imports**. **2024 71/71, 2025 74/74, 2026 68/68** verified college gamebooks = **213 official 2024–26 full boxscores and 6,316 player-game records** (JUCO excluded). No merge or production deployment.

The site lives under \`/college-baseball/\`, with independent college baseball stats and verified inter-level player IDs only. It shares the exact MLB archive design system for Inter fonts, navigation, scoreboards, box-score layout, cards, responsive tables, and bat-order number column.

## 2021 backfill — PARTIAL FULL GAMEBOOK DISCOVERY (authorized October 17, 2026)

**32 original 2021 attendance entries (Feb 6, Mar 14, Apr 7, May 5): 27 university-hosted full individual-player gamebook links established; 0/32 2021 player-level boxscores imported.** Remaining five source match issues: April 24 CSUB at UC San Diego was actually **two games** (12:03 PM CSUB 3–UCSD 2; 3:32 PM CSUB 1–UCSD 7) but user worksheet has one attendance row, so neither can be assigned yet; April 2 USD at Fullerton 1–3 official result/recap found, but a complete player-level gamebook link remains pending; May 6–8 BYU at USD university boxscore pages identified, but player-line data is not accessible in retrieved pages, so the standard complete-gamebook parser must not treat them as verified player sources.

The **March 13 UC Riverside at San Diego doubleheader is separated**: first game 1:00 PM USD 7–0 (USD source 12057), second 4:10 PM USD 9–0 (USD source 12117). The March 30 Vanguard (four-year NAIA) game is eligible, as it is not JUCO. Current official USD detailed historical gamebooks resolve March 5/7 location in favor of original attendance list; a conflicting WCC season index must not overwrite source gamebook identity.

- [2021 official source queue](data/2021_official_source_queue.json): preserves the original 32 attendance IDs, 27 direct player-level gamebooks, candidate boxscores for April 24 and official game/recap-only sources for the remaining four.
- [2021 monthly progress audit](data/2021_monthly_progress_audit.json): monthly checkpoints, source verification limits and identity hold.
- **Scope:** User authorized 2021 discovery on October 17, 2026. Still no 2021 full player-stat imports, no 2020 and earlier authorization, no publication or merge. All 444 attendance records and existing 2024–26 verified player-stat records remain unchanged; all JUCO backfill is excluded.

## 2022 backfill — OFFICIAL SOURCES LOCATED (authorized October 17, 2026)

**62/62 original 2022 attendance games now have linked university original complete gamebook URLs, but 0/62 player-gamebooks are imported into the archive as verified.** February 7/7, March 16/16, April 16/16, May 17/17, June 6/6 source links. Exactly **61** date-matched original sources; **April 21 Grand Canyon–Stanford** original workbook row 152 conflicts with both 2022 university schedules, which list that game on **April 22** at Tony Gwynn Stadium; GCU faced San Diego State on April 21. Keep the original attendance metadata unchanged and require identity clarification before that game's stat import.

Two WCC series doubleheaders require explicit source-specific **Game 1 / Game 2** mapping: April 9 San Diego at Portland (1 PM USD 8–6 Portland; 4:30 PM USD 4–5 Portland in 10) and May 21 Gonzaga at San Diego (1 PM Gonzaga 4–USD 7; 4:45 PM Gonzaga 1–USD 0). USD official source IDs **12487 / 12486** run in reverse for the latter. All six June 3–5 Corvallis Regional gamebooks are sourced, with June 3 NMSU–Oregon State played in 10 innings. Preserve WCC Stockton neutral-site game identities.

- [2022 original university gamebook source queue](data/2022_official_source_queue.json): all 62 direct source links tied to original stable attendance IDs, with the one conflicted date separately marked.
- [2022 monthly progress and exception audit](data/2022_monthly_progress_audit.json): source-match coverage, doubleheader ordering, venue and clearance gates; **zero 2022 player-level box scores imported yet**.
- **Scope:** user authorized 2022 source backfill on October 17, 2026. Earlier years and publication/merge still not approved. Existing 2023 official-source research and 213 fully verified 2024–26 gamebooks remain preserved unchanged. All JUCO backfill excluded.

## 2023 backfill — SOURCES LOCATED, STAT IMPORT PENDING (authorized October 17, 2026)

**47/47 original attendance games now have linked original university full gamebooks, but 0/47 have completed player-level imports.** May: **10/10** source links, April: **18/18**, March: **10/10**, February **9/9**. Exactly **44** original attendance date entries match the official gamebook date; **three February tournament dates** (UNLV–UC Irvine and UNLV–San Diego originally entered February 25, UC Irvine–San Diego originally entered February 26) need reconciliation to official **February 26/27** dates. On February 20, Nebraska–San Diego finished **16–16 in 7 innings**: the importer must handle a tie without manufacturing a winner or nine innings. The spelling *Cal State Northrdige* in the February 21 original row maps to official CSUN.

- [2023 complete official source queue](data/2023_official_source_queue.json) — one official gamebook link per game, original stable attendance IDs, and flagged discrepancies.
- [2023 month-by-month checkpoint](data/2023_monthly_progress_audit.json) — source discovery complete; player-stat import not yet complete.
- Work may proceed newest-to-oldest through all of 2023 without new monthly approval. **Neither 2022-and-earlier backfill nor publishing/merging has been approved.** Do not alter the existing 213 officially verified 2024–26 gamebooks or their 6,316 player-game rows. All 444 attendance IDs remain intact, and JUCO games remain excluded from statistical backfill.

## 2024 backfill — COMPLETE (authorized October 17, 2026)

**71/71 four-year NCAA/DII gamebooks fully verified, 0 remaining.** Monthly completion: **June 6/6, May 16/16, April 7/7, March 25/25, February 17/17.** All completed gamebooks were imported from original university, ACC, or NCAA source records with reconciliation of batting/pitching totals, lineup spots 1–9, substitutions, innings and pitching decisions. Four-year NCAA Division II games remain included; NJCAA/JUCO games are excluded.

- [2024 monthly completion audit](data/2024_monthly_progress_audit.json): 71/71 and exact monthly totals.
- [2024 full source import audit](data/2024_source_import_audit.json): PASS with no remaining source exceptions.
- [2024 final source discovery and identity audit](data/2024_remaining_verification_and_source_match_audit.json): cleared backlog and original date reconciliation.
- The final source formats included original 2024 Virginia/Clemson StatCrew HTML, Vanderbilt/Auburn/Georgia Tech official PDFs, and the ACC March 8 Notre Dame at Virginia Tech full gamebook.

**User-confirmed identity and date corrections:** Siena–UNC Asheville March 2 **Game 1 only**; Vanderbilt–South Carolina March 23 **both games** (the sheet's two attendance rows are mapped chronologically as Game 1/2; their original entry order was not separately confirmed); Florida State–Virginia on **May 24**, not May 23. University records confirm Southern Miss–Georgia State **April 14**, not the original April 15. Duke–Indiana **February 16** remains authoritative despite the archived boxscore metadata showing February 15. All original 444 worksheet attendance IDs were preserved, including legacy IDs where a user-approved date changed.

**Historical release note (superseded for 2023 on October 17, 2026):** The 2024 import is complete, 2025 is complete, and the current approval extends to 2023 only. No 2022-or-earlier backfill or publication is authorized.

## 2025 backfill — COMPLETE (authorized October 17, 2026)

**74/74 original 2025 attendance games have full official-source, player-level gamebooks verified, 0 remaining.** The [2025 source import audit](data/2025_source_import_audit.json) is **PASS**, with no pending gamebooks or source exceptions. The five final completed gamebooks are:

- February 19: North Alabama 2 at Auburn 6 — original North Alabama Sidearm gamebook.
- April 13: Stanford 11 at Clemson 6 — original ACC conference gamebook, summary and composite player tables matched by identity.
- May 22: Texas A&M 3 vs Auburn 2 — original Auburn one-page PDF gamebook with pitching decisions and lineups.
- May 23: Texas A&M 3 vs LSU 4 — LSU archival StatCrew original HTML gamebook.
- June 1: Dallas Baptist 6 vs Little Rock 8 — official Conference USA gamebook, bypassing original university certificate error.

**Verified totals:** 2024 71/71, 2025 74/74, 2026 68/68 eligible four-year gamebooks, with **213 official full gamebooks and 6,316 player-game records**. Original 444 attendance entries retained. All JUCO games excluded from stat backfill; 2023 sourcing and import now approved; 2022-and-earlier and release/merge/publication remain unauthorized.

## 2026 NCAA season — final PASS (October 17, 2026)

**2026 statistical backfill is complete: 68/68 eligible NCAA/four-year gamebooks, 1,990 verified player-game records and 1,061 distinct college player IDs.** The 7 junior-college games remain as original attendance-only rows, excluded from statistics. All 444 original attendance games remain in the unpublished draft.

| Month | Eligible four-year games | Verified player gamebooks | JUCO excluded |
|---|---:|---:|---:|
| January | 0 | 0 | 2 |
| February | 8 | 8 | 3 |
| March | 19 | 19 | 2 |
| April | 14 | 14 | 0 |
| May | 27 | 27 | 0 |
| **2026 total** | **68** | **68** | **7** |

The three documented doubleheaders—Nicholls–Tennessee (February 14), Ohio–Austin Peay (March 10), and ETSU–Belmont (April 11)—each retain their two separately verified attendance/game records with explicit Game 1 and Game 2 labels. The February and March attendance-row alignment remains flagged for final confirmation rather than silently inferred.

The final scorer-decision audit also matches the win, loss and save credits against 16 original February/March university box scores (including surname-first university naming), with each credited pitcher reconciled to the correct player-game record. See `data/2026_feb_march_pitching_decisions_audit.json` (**PASS**).

The audited source of truth is `data/2026_full_slate_monthly_integrity_audit.json` (status **PASS**, zero remaining errors) plus `data/import_report.json`. March 1 Notre Dame–Tennessee Tech is separately reconciled to its official Notre Dame one-page PDF; March 10 Ohio–Austin Peay and February 14 Nicholls–Tennessee doubleheaders retain their individual game identities. The remaining source-research queues document historical discovery, not unfinished 2026 tasks. Older progress figures below are preserved as pilot history only.

**Release boundaries:** No 2025 or earlier player-game backfill and no merge, publication or production deployment without separate user approval.

## Junior-college game exclusion — October 17, 2026

Exclude all NJCAA/junior-college games from box-score lookup, player statistics, 2026 work queues, and monthly progress denominators. Retain their original attendance rows only for audit/provenance and identify them with `boxscore_backfill_excluded: true` and `boxscore_backfill_exclusion_reason: "junior_college"`. Exactly seven 2026 games are excluded (two January, three February, two March). This leaves **68 eligible NCAA/four-year games** for 2026: 27 May, 14 April, 19 March, 8 February and none in January. Other seasons must follow the same rule when work is authorized. Approval currently extends through all 2026, not 2025 or publication. Older numerical snapshots below document prior stages, not current counts.

## Attendance import and source verification — October 2026

The original uploaded Excel workbook \`NCAAB Games.xlsx\` has **444 attendance entries, 2017–2026**, now all represented in \`data/games.json\`. \`data/attendance_master_444.csv\` is an auditable plain-text normalized sheet, preserving original workbook row numbers 2–445. The original spreadsheet is not changed. \`data/attendance_source_444.deflate.b64\` is a losslessly packed record of the normalized attendance data, decoded by \`scripts/build_attendance_master.py\`, which preserves official gamebooks and gives each date/matchup/source-row a stable ID. No unidentified doubleheader or tournament game is merged. Same-date repeated matchups are flagged \`possible_same_day_doubleheader\` and do **not** receive invented doubleheader game numbers.

Current data statuses:

| Status | Games | Meaning |
|---|---:|---|
| \`official_boxscore_verified\` | **9** | All original player batting, pitching, lineup positions and substitutions imported from official sources and reconciled to game totals |
| \`official_scoreboard_verified\` | **5** | Original college gamebook / university or conference source identifies matchup, tournament game, R/H/E, innings and pitching decisions; **individual player lines not yet imported** |
| \`attendance_only\` | **430** | Original attended date / schools retained; no invented scores, player stats or gamebook availability |
| **Total** | **444** | Original personal attendance entries, one distinct row per contest |

The first fully completed batch includes **six 2026 NCAA Auburn Regional games** on May 29–31, including the user-corrected final attendance game #444 **UCF @ Auburn** (regional Game 5, Auburn 9–3), plus the separately documented **Auburn @ Milwaukee** later May 31 (regional Game 6, Auburn 8–1). These gamebooks include 165 player-game lines.

The next source-verified batch covers **eight SEC Tournament games (May 20–23, 2026; original workbook rows 432–439)**. All eight final scores and per-inning lines are checked and staged. Three also have *complete official hitter and pitcher gamebooks*, including 81 additional player-game lines:
- **May 20 LSU @ Auburn:** Auburn 3–1; 27 player-game lines, source-confirmed starting batting order and four substitute entries; winner Jake Marciano, loser Casan Evans, save Jackson Sanders. Official LSU 2026 PDF gamebook cited in game record.
- **May 23 Arkansas @ Auburn:** Arkansas 2–1; 24 player-game lines and nine starters on each side; winner Ethan McElvain, loser Ryan Hetzler. Official Arkansas gamebook linked.
- **May 23 Florida @ Georgia:** Georgia 8–7; 30 player-game lines, nine starting batting spots per team, two DH substitutions confirmed by the official Florida gamebook; winning pitcher Justin Byrd, losing pitcher Joshua Whritenour.
- **Five further May 20–23 SEC tournament games** (Tennessee–Arkansas, Mississippi State–Georgia, Florida–Alabama, Arkansas–Texas, Auburn–Texas A&M) have official scores, inning lines and decisions but **not** individual player stats yet.

Across nine full scorebooks: **246 source-reconciled player-game rows, 147 unique college athlete IDs**. Batting-slot identities stay 1–9 with indented \`↳\` substitutions, and pitcher #1 is the starting pitcher. Incomplete NCAA stats are not filled from a season roster or guessed.

Other confirmed corrections: user's South Alabama @ Old Dominion 2024-03-30 originally appeared as \`Friday, 3/30/34\`; final game #444 originally entered Milwaukee–Auburn but corrected to UCF–Auburn. Both corrections documented in \`data/import_report.json\` and in the source queue.

The source audit and browser checks are in \`scripts/test_college_baseball.py\` and GitHub workflow \`.github/workflows/college-baseball-qa.yml\` (desktop 1280px + mobile 390px, with screenshot artifacts). Current review gate is **draft only**; do not merge into \`main\` until user approval. Import remaining 2026 official player gamebooks newest-to-oldest in batches of 5–10, marking source conflicts or unavailable stats rather than silently guessing.

## What we are building

- **Overview:** witnessed games, teams, seasons, ballparks, and a searchable attendance history.
- **Games & Box Scores:** matchup, ballpark, official scores, inning lines, verified college batting and pitching box scores, game decisions and scoring details when the sources contain them; neutral sites, doubleheaders, NCAA Regionals, Super Regionals, the Men's College World Series and conference tournament games.
- **Players:** deduplicated identities, attended-game aggregates, AVG/OBP/SLG/OPS for batters, ERA/WHIP/strikeouts for pitchers, and separate batting and pitching panels for two-way players.
- **Signature Performances:** single-game top performances and documented historic achievements, never imagined totals.
- **Future To the MLB:** explicitly verified crosslinks of college identity to MLB player identity (and separate drafted-only/MLB-appearance statuses, if verified). MLB, college and MiLB statistics must **never** be summed together.

## Attendance import: one row for each game witnessed

The empty CSV template is at [data/attendance.csv](data/attendance.csv). It contains only a header:

\`attendance_id,date,away,home,ballpark,city,state,neutral_site,game_number,game_type,postseason_round,away_score,home_score,source_url,notes\`

- **Required:** \`date\` in \`YYYY-MM-DD\` (or US \`MM/DD/YYYY\`), the visiting \`away\` team and designated \`home\` team. For a neutral-site event, use the officially designated home and away sides when possible.
- **Everything else optional:** leave fields blank when not known. The importer preserves unknowns as \`null\` (not guesses).
- **Doubleheaders:** if two games share the same calendar date and opponents, set \`game_number\` to \`1\` and \`2\`. A duplicate with missing identifiers is **rejected**, never silently merged.
- **Neutral site:** \`yes\`, \`no\`, or blank for unknown.
- **Game type:** regular season, exhibition, conference tournament, NCAA postseason, etc. Keep the exact \`postseason_round\` if supplied.
- **Scores supplied by user:** copied with provenance \`user_attendance_log\`; the source-check status remains **attendance only** even if the scores are present.
- **Official source:** \`source_url\` may point to a gamebook or box score but a URL in the list alone does **not** mean the statistics have been checked.
- **Attendance ID:** optional stable identifier from your source sheet; generated canonical game IDs use date, team names and doubleheader number.

Google Sheets users can export a CSV (File → Download → Comma-separated values). A pre-existing sheet or other attendance list can also be supplied and normalized into this schema.

### Validate, then import

Run from repository root:

\`\`\`bash
python college-baseball/scripts/import_attendance.py --validate-only
python college-baseball/scripts/import_attendance.py
\`\`\`

The importer writes only \`college-baseball/data/games.json\` and the import report. It does not reach out to NCAA/ESPN or fabricate scores, teams, player statistics or pitch-by-pitch data. No attended games are shipped with the initial foundation.

## Official scorebook verification workflow

After attendance rows are imported, select a small 3–5 game pilot across years and schools:

1. **Identify exact game** by date, away/home, actual venue, designated home side, game number, and postseason classification.
2. **Source hierarchy:** university athletics official scorebook/Sidearm HTML or PDF → NCAA gamebook and verified conference archives → other corroborating sources. ESPN data may assist discovery but should not override official gamebooks, especially for older college baseball.
3. **Reconcile scoreboard:** inning by inning to final score, extra innings, game completion / suspended games and doubleheader number.
4. **Reconcile hitters/pitchers:** all players, lineup changes, two-way roles, runs, hits, errors, AB, R, H, 2B, 3B, HR, RBI, BB, SO, SB, and pitching outs/H/R/ER/BB/K when recorded. Preserve pitching outs as an integer; \`5.1\` IP means 16 outs, not 5.1 decimal innings.
5. **Source status:** per-game \`attendance_only\`, \`source_matched\`, \`partial_boxscore\`, or \`official_boxscore_verified\` only after full reconciliation. Missing historical fields stay null. Do not present a nonofficial box score as verified.
6. **Cross-level identities:** match college athletes by player, school, season and source ID. Only add a college → MLB identity link after verification. \`data/mlb_crosswalk.json\` begins empty.

## MLB visual parity and official college batting order

The new college baseball dashboard intentionally shares the **exact MLB archive base CSS** (Inter typeface, cream/forest palette, 1160px page width, headline sizes, navigation spacing, score cards, table styles, and responsive breakpoints) with college-specific additions only where the gamebook requires them. Game details reuse the three-column MLB scoreboard, inning panels, **Win / Loss / Save** cards, and separate **Batting / Pitching** tabs. Player profiles use the same hero composition and six-stat rows as MLB; leaderboards, game cards, and signature cards follow the same presentation.

Every batter from the six verified Auburn Regional games has a source-verified `batting_slot` (integer **1–9**), `batting_sub_index` (0 for the starter, 1+ for replacements in that **same spot**), `batting_appearance_index`, and `position`. A substitute is rendered with the MLB **↳** notation immediately under the original starter, not a fictitious tenth or eleventh batting position. The pilot source audit confirms **116 batting appearances including eight substitute/replacement entries**, which are kept separate across both games held on May 31. Pitcher `pitching_appearance_index` begins at 0 for the starting pitcher and increases for relief appearances, matching MLB's numbered pitching rows.

For future older-game imports: **do not guess batting order** from a general season roster, a list sorted by name, or batting-stat totals. Transcribe the original lineup table and substitution indentations from the actual university/NCAA scorebook. If the information is unavailable, leave the lineup metadata absent and show an em dash rather than an invented batting spot. College stats remain independent of MLB data.

## Data contracts

\`data/games.json\`: one row per attended contest; \`id\`, dates, teams, scores, site, \`game_number\`, source and verification. \`data/player_stats.json\`: one player-game row with \`game_id\`, \`player_id\`, \`player\`, \`team\`, optional \`batting\` and/or \`pitching\` objects, and an official source reference. Hitter keys use the professional site convention (\`atBats\`, \`runs\`, \`hits\`, \`doubles\`, \`triples\`, \`homeRuns\`, \`rbi\`, \`baseOnBalls\`, \`strikeOuts\`, \`hitByPitch\`, \`sacFlies\`, \`stolenBases\`). Pitcher keys include \`outs\`, \`hits\`, \`runs\`, \`earnedRuns\`, \`baseOnBalls\`, \`strikeOuts\`, \`numberOfPitches\`, \`wins\`, \`losses\`, \`saves\`.

A missing field differs from a recorded **zero**. Derived rates appear only when the required numerator and denominator fields are present, and no college rates are added to professional rates. \`data/scoring_plays.json\` is intentionally empty until source-verified game scoring can be assembled; \`data/mlb_crosswalk.json\` is an empty verified cross-level ID mapping.

This foundation does not assert an attendance total, a postseason game, or a college player has already been observed. All examples in QA run only from disposable **synthetic** test fixtures.
