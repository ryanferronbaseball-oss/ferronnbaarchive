# College Baseball · Courtside Archive

**Current verified status (October 17, 2026):** Unpublished draft PR #10 contains **434/437 eligible attended college baseball games with fully imported, original-source-verified player box scores** and **13,088 player-game rows**. All **444 original attendance IDs** remain intact. Seven JUCO attendance games are excluded from player-stat backfill. **Three 2018 games remain**, listed below. Nothing has merged into production or been deployed.

The site lives under `/college-baseball/`, with independent college baseball stats and verified inter-level player IDs only. It shares the MLB archive design system: Inter fonts, navigation, scoreboards, box-score layout, player cards, responsive tables, and numbered batting-order slots.

## October 17, 2026 — authoritative post-verification import status

The original university batting, pitching, scorer decisions, inning totals, and nine-slot starting lineups are source-validated by `scripts/import_historical_verified_queue.py`. The latest [2018 incomplete-game audit](data/2018_historical_stat_import_audit.json), [2022 complete-game audit](data/2022_historical_stat_import_audit.json), [2023 complete-game audit](data/2023_historical_stat_import_audit.json), and `data/import_report.json` determine actual completion—not the older source discovery notes below.

| Season | Fully verified player gamebooks | Eligible attended games |
|---|---:|---:|
| 2017 | 1 | 1 |
| 2018 | 27 | 30 |
| 2019 | 41 | 41 |
| 2020 | 11 | 11 |
| 2021 | 32 | 32 |
| 2022 | 62 | 62 |
| 2023 | 47 | 47 |
| 2024 | 71 | 71 |
| 2025 | 74 | 74 |
| 2026 | 68 | 68 |
| **Total** | **434** | **437** |

All four previously held 2022–2023 attendance date conflicts were **explicitly confirmed by the user October 17, 2026** and imported. Actual site dates now match their original university gamebooks; each record also keeps `original_worksheet_date`, `date_correction_user_confirmed`, original source worksheet row and immutable game ID. The 2022 Gonzaga–San Diego and San Diego–Portland two-game doubleheaders were imported separately, matching both start times and scores. The official 2023 seven-inning Nebraska–San Diego 16–16 tie retains no win, loss or save.

**October 18 update: both February 18 Cincinnati–San Diego games are fully imported.** The original university-hosted archived scorebooks were recovered from Cincinnati's Google Cloud archive (not USD's inaccessible PDF landing pages). Game 1 imported **33 player rows**, Game 2 **27**; all nine starting batting slots, 10- and 9-inning scores, scorer's winning/losing/saving pitchers, and source player totals verified. The archived PDFs print February 17 but both universities' actual game schedules identify Sunday, February 18. The source header-date discrepancy is explicitly preserved in the strict import audits rather than silently corrected.

**The only three remaining unimported games, all from 2018:**

1. March 13, San Diego State at San Diego (SDSU 9–3): original user-supplied university PDF and transcribed source in `data/official_pdf_transcriptions/2018_03_13_sdsu_san_diego.txt`; strict player-stat import pending.
2. April 14, Saint Mary's at San Diego (Saint Mary's 6–5): original user-supplied university PDF and transcribed source in `data/official_pdf_transcriptions/2018_04_14_saint_marys_san_diego.txt`; strict player-stat import pending.
3. May 9, Arizona State at San Diego (ASU 12–7): official batting/pitching and user-reconciled hitter K evidence in `data/2018_05_09_asu_san_diego_screenshot_evidence.json`; full inning line and exact substitution slots still require verification.

Do not mark a source-matched game as imported until all individual player rows, inning R/H/E, pitcher decisions and nine batting slots pass the same stringent checks. No JUCO backfill. **No publication, production merge, or live-site deployment was authorized.**

The sections below are a **preserved historical discovery timeline**. Their earlier claims such as “0 imports,” “41 pending,” or incomplete year totals were snapshots written *before* the source-verified imports and are no longer current.

## 2017–2018 backfill — all gamebooks identified and full player tables evidenced (October 17, 2026)

**2017:** 1/1 original attendance game April 20 BYU at San Diego has an official full gamebook source; player stats not yet imported.

**2018:** **30/30** original game identities matched and official university gamebook links located. Full individual player batting/pitching tables are supported for **30/30 attended games**: 29 via previously verified university full HTML/PDF sources, and **May 9 Arizona State 12 at USD 7** via the user-supplied browser-rendered [ASU interactive box score](https://thesundevils.com/boxscore/466) batting and pitching screenshots. The official [USD “USD vs ASU Box (PDF)” ID 14288](https://usdtoreros.com/documents/2018/6/27/14288__m_basebl_2017_18_misc_non_event__USDvsASUboxMay9.pdf) is also located, though the PDF bytes are not separately parsed.

**ASU web batting table strikeout anomaly resolved:** the on-screen SO column erroneously assigned pitcher total strikeouts in pitching-as-batter lines while listing every real hitter as zero. The user inspected original play-by-play and supplied every nonzero hitter SO, including the last missing **Todd Jackson 1**. Individual totals now reconcile: **ASU hitters 7 Ks** vs San Diego pitching 7; **USD hitters 11 Ks** vs ASU pitching 11. Verified batting and pitching player lines, detailed play-by-play SO mapping, and unknown/not-imported field flags are in [2018 May 9 screenshot evidence JSON](data/2018_05_09_asu_san_diego_screenshot_evidence.json). Any still-unverified inning-by-inning score, W/L/S metadata, and substitute lineup slots must be verified at player-stat import; never fabricate.

March 13 SDSU–USD and April 14 Saint Mary's–USD source PDFs were supplied by the user and content-verified. Cincinnati on Feb 18 and Indiana on Mar 3 were separate true doubleheaders, two original IDs per date preserved.

- [2017 original university source queue](data/2017_official_source_queue.json) · [2017 audit](data/2017_monthly_progress_audit.json)
- [2018 original university source queue](data/2018_official_source_queue.json) · [2018 audit](data/2018_monthly_progress_audit.json)
- **No 2017 or 2018 player gamebook imports yet (0/31).** All 444 original attendance game records and 2024–26 213 verified gamebooks/6,316 player-game records preserved. JUCO excluded. No merge or deployment.

## 2019–2020 backfill — ALL 52 OFFICIAL GAMEBOOK SOURCES LINKED (authorized October 17, 2026)

**2019:** 41/41 original attended four-year NCAA baseball games source-matched to official university-hosted full individual-player gamebooks: Feb 11, Mar 13, Apr 9, May 8. All dates matched. February 16 Wagner–USD official doubleheader is specifically assigned Game 1 **Wagner 9, USD 15** at 1:03 PM (USD source 8231) and Game 2 **Wagner 1, USD 3** at 5:09 PM (USD source 8232); cumulative stats list these out of chronological order, so use actual first pitch. 2019 Tony Gwynn Legacy off-USD matchups are fully sourced from UC Irvine, K-State, Utah, and Oklahoma university archives.

**2020:** 11/11 original attendance entries have university-hosted full individual-player gamebook links: February 9, March 2. **All 11 game identities now confirmed.** Ten worksheet dates matched the official source and one original worksheet date required a correction: source row 84 (att0083) recorded California Baptist at USD on **March 10**, but the university's full gamebook ID 9683 places USD's 2–0 win on **March 11**. The **user explicitly confirmed on October 17, 2026 that they attended the March 11 game**. The original workbook date (March 10), attendance ID, and source row are preserved for provenance, while the verified source-matched official date is March 11. This game is cleared for eventual player-stat import; no 2020 player rows are imported yet. All February 21–23 Tony Gwynn Legacy games, including four-school off-USD games, are matched to full player gamebooks. February 29 Monmouth–USD went 10 innings.

- [2019 official gamebook queue](data/2019_official_source_queue.json) and [2019 monthly audit](data/2019_monthly_progress_audit.json)
- [2020 official gamebook queue](data/2020_official_source_queue.json) and [2020 monthly audit](data/2020_monthly_progress_audit.json)
- **Important:** **0/41 2019 and 0/11 2020 individual player-gamebooks imported.** Sourcing is distinct from full game/stat import. Original 444 attendance records and the existing 213 fully verified 2024–26 gamebooks/6,316 player rows are unchanged. Exclude JUCO; **2018 and earlier, merging or publication not approved**.

## 2021 backfill — 32/32 OFFICIAL GAMEBOOK SOURCES MATCHED (authorized October 17, 2026)

**All 32 original 2021 attendance entries (Feb 6, Mar 14, Apr 7, May 5) now have unique official university-hosted full individual-player gamebook source matches; 0/32 gamebooks have yet been imported as player-game statistical rows.** The user explicitly confirmed **April 24, 2021 CSU Bakersfield at UC San Diego GAME 1 (12:03 PM), CSUB 3–UCSD 2**, which is [official UCSD gamebook ID 8289](https://ucsdtritons.com/sports/baseball/stats/2021/csu-bakersfield/boxscore/8289). The same-day 3:32 PM Game 2 (official source ID 8292) was not included in the original attended games and is **not** to be imported as an attended game. All original attendance IDs and worksheet rows remain preserved.

Other sources: April 2 USD at Fullerton 1–3, USD gamebook ID 12125; May 6–8 BYU at USD IDs 12085–12087 (May 6 ten innings); March 13 UC Riverside at San Diego doubleheader Game 1 USD 7–0, 1 PM (ID 12057) and Game 2 USD 9–0, 4:10 PM (ID 12117). March 30 Vanguard University (NAIA/four-year) is eligible, as only JUCO games are excluded.

- [2021 official source queue](data/2021_official_source_queue.json): all 32 exact player-gamebook links tied to preserved original attendance IDs; April 24 Game 2 retained separately as expressly **not attended**.
- [2021 monthly progress audit](data/2021_monthly_progress_audit.json): official source and explicit user-confirmation record; zero 2021 player-stat imports.
- **Scope:** user authorized 2021 backfill; player-level imports remain pending, no 2020 and earlier authorization, no merge/publication. The 444 original attendance records and 213 2024–26 fully verified gamebooks and 6,316 player-game rows are untouched. All JUCO backfill excluded.

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
