# Courtside Archive — Continuity and Decision Record

**Maintainer:** Ryan Ferron  
**Repository:** `ryanferronbaseball-oss/ferronnbaarchive`  
**Last consolidated:** 2026-11-06  
**Purpose:** A durable handoff for future conversations, contributors, and maintenance. This is a decision record, **not** a substitute for live source data or a claim that every historical task was published.

## Start here in a new conversation

1. Read this file, then inspect the relevant sport's current GitHub data and recent commits before editing.
2. Preserve user-confirmed decisions. Distinguish **approved**, **committed**, **published**, and **verified live**; these are not interchangeable.
3. Internal attended-game box scores and player profiles are the canonical experience. External ESPN/NCAA/league sources verify source facts but should not replace working internal links.
4. Never invent statistics, roster participation, player identities, awards, dates, or venues. Mark unavailable data explicitly. An upcoming candidate game is **not attended** until Ryan confirms attendance after it happens.
5. For potentially destructive identity merges, file deletions, or ambiguous image placements, resolve the exact target first. Preserve original material and maintain an audit trail.
6. After changes, validate file integrity, relevant pages, internal links, and deployment; report the commit and any unverified live behavior.

## Project identity and presentation

The archive chronicles games Ryan attended across MLB, NBA, NFL, NCAA men's basketball, college football, college baseball, and soccer. Core ideas include **“Every Game Has a Story,”** game-level box scores, player pages and game logs, Player of the Game, signature performances, relevant career honors, and cross-sport recognition. The site favors a unified **Games** experience and clickable internal player-to-game links.

On 2026-11-13, chronological baseball recaps were launched with MLB first and college baseball after the MLB queue is complete. Recaps render immediately above Player of the Game; player mentions should use internal player-profile links when the player appeared in that game.

Approved design direction: **Courtside Editorial**—ivory `#FAF8F2`, deep evergreen `#284D3C`, subtle borders, rounded cards, legible editorial spacing. Preserve functionality during redesigns; maintain consistent honor/tag colors across sports. The home venue map belongs **below the introduction and above the archives**.

## Adding an attended game: required checklist

1. Confirm actual attendance, date, teams, competition, and correct home/neutral-site designation. Do not add mere calendar candidates.
2. Verify final score, venue, game identity, and official box-score source. Enter every player who **participated**, including a new profile when appropriate; do not create a profile solely because a player was on the roster.
3. Preserve full available team/player statistics and source game logs. Missing values display as `—`, not invented estimates.
4. Fix team identification and abbreviation problems (`undefined` is unacceptable). Round displayed basketball minutes to the nearest **whole minute** while preserving accurate source-derived calculations and totals where appropriate.
5. Link game rows to the correct existing player identity, including transfers, initials, suffixes, and multi-school histories. Do not merge names on similarity alone.
6. Apply already-earned, verified player awards and career-status tags using the intended season/year, including NBA/MLB/NFL debuts and draft status if supported.
7. Add/update player headshots when reputable source photos are available; user-supplied game photography must be matched to the **exact game** and displayed in that game slot.
8. Recognize a new physical venue through its canonical venue profile, aliases, map location, and associated visit; do not accidentally create duplicate venues for renamed buildings.
9. Determine Player of the Game through the relevant sport's established impact methodology and update signature performances if applicable.
10. Validate pages, stats, links, photos, mobile rendering and deployment before reporting completion. Correct errors in one pass where practical.

### Critical photo lessons

Past photo batches suffered incorrect game assignments. Treat a user's explicit `current slot → correct slot` correction as authoritative, and verify **both** removed and destination slots. Distinguish image identification, upload to the repository, mapping to a game, and live-site rendering. Favor user photos over generic stock where supplied, but retain appropriate rights/attribution information when known. Never say "uploaded" solely from image recognition.

The 2026-11-06 GitHub photo work included `college/data/game_photos.json` game 80 (`2024-03-21`, Michigan State 69–Mississippi State 51), and NFL images integrated into `nfl/game.html` for 2007-11-25 SF–ARI, 2008-12-07 STL–ARI, and 2023-12-03 IND–TEN. Inspect current commits for final state.

## Sport-specific rules

### College basketball (NCAAB)

- Game, player and career pages support NBA-alumnus recognition; keep College-to-NBA coverage up to date with a visible last-updated date. Specific audit requests included **Vlad Goldin**, **Jaylen Clark**, and **Dylan Cardwell** (not “Caldwell”).
- Basketball advanced stats use overview plus Scoring/Efficiency, Playmaking, Rebounding/Defense, and Overall Impact groupings; aggregate makes/attempts, compute per-36 from total minutes, show missing values as `—`, and require fouls before standard Game Score.
- Records & Milestones include individual performances, player-frequency rankings, and player/team/game records.
- Verified conference honors should be attached to the correct player and school/season; guard against similarly named athletes and transfer confusion.

### College baseball

- Scope: attended college baseball games, notably 2017–2026 (major imports 2024–2026); **exclude JUCO** from this portion unless Ryan changes scope.
- Hitter aggregate fields: `G, PA, AB, R, H, 2B, 3B, HR, RBI, BB, K, BA, OBP, SLG, OPS, BB%, K%`. Pitcher fields: `G, GS, IP, BF, H, ER, BB, K, ERA, WHIP, BB%, K%`. Player game log preview shows the most recent **three** games.
- Approved identity merges include Tate Soderstrom (Arizona/UC San Diego), Ethan Lizama (WKU/South Carolina), and Kyle Hvidsten (WKU/Liberty). Preserve explicit **DO NOT MERGE** decisions (e.g., Christian Rodriguez Cal State Fullerton/Florida; Sam Beck San Francisco/BYU). Full decision records exist under `college-baseball/data/identity_audit*`, `player_identity_crosswalk.json`, `player_identity_merges.json`, and `player_identity_reconciliation_audit.json`.
- Names, extra-base hits, dual-team player attachment, and venue corrections were important historical cleanup areas. Notable fixtures: 2021-02-20 SDSU, 2018 USD/Cincinnati, 2018-03-13 SDSU–USD, 2023-05-12 Saint Mary's, 2025-03-19 Virginia, 2025-03-22 WKU–Milwaukee, LSU 2025-05-31 and 2025-06-01. Recheck actual current data rather than assuming every correction is published.
- For MLB draft tags when a player was drafted twice, use the **later** draft selection. Do not build a separate "drafted only" section until requested.
- National individual awards scope (2014–2026): Golden Spikes, Dick Howser, Buster Posey catcher, two-way, Brooks Wallace shortstop, and national Defensive Player; **not** relief-pitcher awards. Record only Ryan-confirmed YES matches on existing profiles. NO/UNSURE remain untagged. Dominic Keegan was corrected to YES.
- Baseball America postseason All-American screening excludes **high-school players**. Kevin McGonigle was NO/excluded. Preserve YES/NO/UNSURE decisions rather than inferring attendance. All-CWS teams, MOP and national champions should also be recognized for confirmed attendees.
- Conference individual award research and All-Conference team selection are distinct. All-Conference scope: seasons **2015–2026**, official **First, Second and Third Teams when published**, **no Honorable Mentions**. Initial priority was SEC, ACC, Big Ten, Big 12, WCC, then remaining conferences. Verify transfers and school-season attribution; preserve gaps and uncertain attendance separately.
- `college-baseball/data/all_conference_*`, `conference_attendance_match_audit_2026-11-04.json`, `mountain_west_attendance_yes_recovery_2026_11_05.json`, and `all_conference_attendance_completion_2026_11_05.json` are starting points for recent progress. Earlier conversational counts can be stale; recompute from these files.
- Tomas Valincius was specifically flagged for a missing All-SEC tag; verify current status. Some player searches may require aliases such as **Hank/Henry** or **EJ/… Jr.**

### NFL, NBA, MLB and college football

- NFL: complete scoring chronology, offense/defense/special teams boxes, Player of the Game, full-PPR milestones and career honors (All-Pro, MVP, Pro Bowl, NFL 100, championships, retired numbers, franchise honors). At mid-article, distinguish eventual NFL participants from players **drafted without an NFL regular-season game**.
- MLB: box scores, MLB debut/status, draft tags, Statcast leaders, Gold Gloves, other honors and World Series titles. Verify season/year of awards before attaching them.
- NBA: NBA Top 75, retired jerseys, championships and other career recognition, linked from attended college and NBA histories.
- College football: an article section between score and box highlights attendees who later reached the NFL; link internally. Preserve draft-only distinctions.

## Venue map and venue naming

Ryan approved preferred venue names for **129 physical venues** and generally approved address/coordinate and profile framework. One physical venue should have one profile, with historic names as aliases and first-visit date. Approved examples: Crypto.com Arena, Cameron Indoor Stadium, Dean E. Smith Center, Angel Stadium, Oracle Park, Wrigley Field, Original Nissan Stadium, GEODIS Park, Mercedes-Benz Stadium, and Fowler Park and Cunningham Field. Exact canonical spellings must be taken from `venues/data/venues.json` and approved-name records, not this sample list.

Photo preference: **interior with game action or spectators**, not an empty facility, when possible. Ryan may later supply his own replacements. Verify licensing, attribution and exact venue identity. Not all venue facts/pins were fully verified; preserve explicit uncertainty. Useful files: `venues/data/venues.json` and `venues/data/photos.json`.

College-baseball venue rules: avoid generic automatic host attribution when games were neutral or moved. Explicit conventions mentioned by Ryan include Tennessee at Lindsey Nelson, Louisville at Jim Patterson, Kentucky at Kentucky Proud Park, Vanderbilt at Hawkins Field (excluding tournament context). USD's default Fowler Park varies by individual road/neutral dates.

## Pregame previews and attendance calendar

- Notion **“Courtside Archive — Potential Games”** is the candidate-game source of truth. A daily **10:00 a.m. America/Chicago** check-in asks for attendance confirmation and generates a preview when appropriate; the day after the game, ask if attendance occurred and then process the box score/tags. A deleted calendar entry should no longer cause reminders.
- Every preview is a **phone-friendly PDF**. Give five or six relevant players per team when warranted, current context, transfers, key stats, honors **already earned**, storylines, and especially surprising players Ryan has previously seen. Include exact prior game date, school and appearance where validated. Current-roster presence does **not** prove current-game participation; eventual archives only tag actual participants.
- Ryan prefers useful depth and unusual connections over exhaustive boilerplate. He can seek a preview to judge a prospective game's value without committing to attend; such a preview should not add the game.
- As of the November 2026 planning discussion, candidates included SIUE at Lipscomb (Nov 7), Tennessee State at Tennessee (Nov 13), Central Michigan at Northern Kentucky (Nov 14), a Kentucky home game (Nov 16), Texas at Louisville (Dec 1), Bridgestone Arena doubleheader (Dec 6), and Santa Clara–Boise State (Dec 21). These are **historical planning snapshots**, not a current schedule or proof of attendance. Recheck Notion and official schedules before acting.

## Audit and publication discipline

| State | Meaning |
| --- | --- |
| Proposed | Suggested change; no approval yet |
| Approved | Ryan confirmed decision, but implementation may remain pending |
| Recorded | Decision saved in a review file; live tags need not have changed |
| Committed | GitHub commit exists on target branch |
| Published | Deployment step succeeded |
| Verified live | Site rendering and expected behavior checked after deployment |

**Do not collapse these states.** In particular, a YES in an attendance review file does not automatically mean a player has a visible live award tag. Inspect the latest commit and deployed page when reporting completion. Preserve NO and UNSURE review outcomes, and do not convert them into tags.

## Pointers to canonical repository data

| Topic | Likely source of truth |
| --- | --- |
| NCAA basketball games | `college/data/games.csv`, `attendance.csv`, `game_photos.json`, `career_awards.json` |
| NFL games | `nfl/data/games.json`, `nfl/game.html` |
| Baseball games/identities | `college-baseball/data/games.json`, `attendance_master_444.csv`, `player_identity_crosswalk.json` |
| Baseball national/conference tags | `college-baseball/data/national_award_profile_tags.json`, `baseball_america_all_american_tags.json`, `all_conference_profile_tags.json`, `conference_award_profile_tags.json` |
| Baseball review/audit state | `college-baseball/data/all_conference_*`, `identity_audit*`, `conference_attendance_match_audit_2026-11-04.json` |
| Venues and venue photos | `venues/data/venues.json`, `venues/data/photos.json` |

These paths describe the layout at consolidation time. Check actual repository structure before making changes.

## Preservation and safe cleanup

The GitHub repository preserves code/data and version history; **ChatGPT saved memory, chat history, and Library files are separate systems**. This document captures major project rules and known decisions, but cannot reproduce every past transcript, ambiguous image identification, or unpublished review result. Do not delete valuable source conversations or files based solely on this summary. Before any cleanup, compare source files against GitHub and keep recoverable backups of originals and important user photographs.

### Maintenance convention

After a meaningful new rule, approval batch, correction or workflow change: update this document **and** the canonical data/audit file as applicable. Record the date, exact file/commit, and whether the outcome was approved, committed or verified live. Keep the main guide readable; detailed per-player screening decisions belong in structured audit files.
