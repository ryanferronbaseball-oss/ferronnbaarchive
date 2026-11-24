# Historical college logo audit — checkpoint 2026-11-23

Scope: Multiple Schools directories and eventual matching profile logos. Use first attended appearance, not first roster season. Basketball season starts in autumn; baseball uses calendar year. Verify actual artwork as well as its active dates before deploying. Use primary athletics mark, not alternate unless deliberately designated sport-specific.

## Basketball exact inventory

17 eligible ESPN identities, 35 player-school entries, 28 distinct school-season combinations. Derived from current college/data/player_boxscores_espn.json and team_names.json using the directory's eligibility and earliest-date logic.

| Player | First witnessed school appearances |
|---|---|
| Ryan Woolridge | North Texas (249): 2017-12-16; Gonzaga (2250): 2020-01-09 |
| Tahirou Diabate | Portland (2501): 2019-02-21; San Diego State (21): 2021-11-18 |
| Lazaro Rojas | Fresno State (278): 2019-11-12; UT Arlington (250): 2021-11-20 |
| Pierre Crockrell II | Pacific (279): 2019-12-28; UC Irvine (300): 2022-11-29 |
| Chad Baker-Mazara | San Diego State (21): 2021-11-18; Auburn (2): 2025-02-19 |
| DJ Horne | Arizona State (9): 2021-11-18; North Carolina State (152): 2024-01-30 |
| Hunter Sallis | Gonzaga (2250): 2022-02-03; Wake Forest (154): 2024-01-22 |
| Noah Waterman | BYU (252): 2022-11-11; Louisville (97): 2025-02-12 |
| Darrion Williams | Nevada (2440): 2023-01-10; North Carolina State (152): 2025-12-06 |
| Andrej Stojakovic | Stanford (24): 2023-12-21; California (25): 2025-01-18 |
| Mady Sissoko | Michigan State (127): 2024-03-21; California (25): 2025-01-18 |
| Tre Holloman | Michigan State (127): 2024-03-21; North Carolina State (152): 2025-12-06 |
| Phat Phat Brooks | Michigan (130): 2024-11-10; Central Michigan (2117): 2026-11-14 |
| Juke Harris | Wake Forest (154): 2024-11-10; Tennessee (2633): 2026-11-13 |
| Ven-Allen Lubin | North Carolina (153): 2025-03-13; North Carolina State (152): 2025-12-06 |
| Ty-Laur Johnson | Wake Forest (154): 2025-03-13; San Diego (301): 2025-11-18; Tennessee State (2634): 2026-11-13 |
| Tyler Lundblade | Belmont (2057): 2026-02-03; Tennessee (2633): 2026-11-13 |

### First evidence pass

- Fresno State, Lazaro Rojas, 2019-11-12: use 2016–2020 bulldog rather than post-refresh deeper red. Official announcement 2019-12-11: https://gobulldogs.com/news/2019/12/11/general-fresno-state-athletics-refreshes-its-brand ; historical artwork reference https://www.sportslogos.net/logos/view/68177952006/Fresno-State-Bulldogs-Logo/2016/Primary-Logo . Asset URL and visual verification pending.
- NC State: wolf-head primary beginning 2023, so all witnessed dates in this directory are after adoption. Check ESPN image actually matches. https://gopack.com/sports/2024/7/17/nc-state-athletics-brand-guidelines
- Portland: 2014 onward era includes 2019 appearance. https://www.sportslogos.net/logos/list_by_team/804/Portland-Pilots-Logos/
- North Texas: 2005 onward diving eagle mark was already in use in 2017. https://www.sportslogos.net/logos/view/78267462005/North-Texas-Mean-Green-Logo/2005/Primary-Logo
- UC Irvine: 2014 onward era includes 2022 appearance. https://www.sportslogos.net/logos/list_by_team/880/California-Irvine-Anteaters-Logos/
- Wake Forest: 2019 refresh predates all directory appearances. https://godeacs.com/news/2019/10/1/general-wake-forest-athletics-refreshes-its-brand
- Pacific: 2019 licensing confirms Powercat and athletics wordmarks. https://pacifictigers.com/sports/2019/6/5/information-traditions-logos
- Other school-season artwork remains pending; no blanket current-logo verification claimed.

## Baseball preliminary inventory

172 identity merge records with multiple distinct school strings; 116 distinct source school strings (includes a Northridge spelling variant). Not a verified rendered-player count. The large player_stats.json could not be read through the connector, so player-specific first dates remain pending. The table below reports school attendance windows from games.json, NOT player-specific appearances; use it to prioritize historical research.

- Grand Canyon: all matching school games in 2018–2022 precede the 2023-06-30 retirement of arched GCU. https://gculopes.com/news/2023/6/30/general-new-university-branding-launches
- Loyola Marymount: 2018–2023 school window crosses spring 2019 rebrand. https://brand.lmu.edu/identitystandards/logos/athleticsmark/
- UC Riverside: 2018–2021 crosses 2020-07-01 athletic rebrand. https://gohighlanders.com/news/2020/7/1/general-uc-riverside-athletics-completes-new-visual-identity-rebrand
- Fresno State: school window crosses 2019/2020 refresh.
- Gardner Webb: matching school games 2024–2025 follow 2022-04-28 refresh. https://gwusports.com/news/2022/4/28/baseball-gardner-webb-athletics-launches-new-athletics-branding-thursday
- Missing directory mapping: Cal State Northrdige (typo), Lenoir-Rhyne, Point Loma Nazarene, Tampa. The general colleges/logo_overrides.json contains alternate mappings for the three non-D1 schools; verify historically appropriate assets.
- No renderer or identity edits in this checkpoint.

| School string | ESPN ID in baseball mapping | Earliest school game | Latest school game | Matching games |
|---|---|---|---|---:|
| Alabama | 333 | 2025-05-20 | 2026-05-21 | 4 |
| Arizona | 12 | 2018-02-25 | 2020-02-22 | 3 |
| Arkansas | 8 | 2018-02-23 | 2026-05-23 | 7 |
| Auburn | 2 | 2024-02-23 | 2026-05-31 | 12 |
| BYU | 252 | 2017-04-20 | 2024-03-07 | 11 |
| Baylor | 239 | 2024-04-26 | 2026-04-10 | 3 |
| Binghamton | 2066 | 2024-03-08 | 2024-03-08 | 1 |
| Cal Baptist | 2856 | 2019-05-14 | 2022-05-10 | 4 |
| Cal Poly | 13 | 2018-02-23 | 2018-02-24 | 2 |
| Cal State Bakersfield | 2934 | 2021-04-24 | 2021-04-24 | 1 |
| Cal State Northrdige | missing | 2023-02-21 | 2023-02-21 | 1 |
| Cal State Northridge | 2463 | 2023-03-28 | 2023-05-07 | 3 |
| California | 25 | 2018-02-16 | 2024-05-05 | 4 |
| Campbell | 2097 | 2024-03-09 | 2025-04-06 | 4 |
| Cincinnati | 2132 | 2018-02-17 | 2026-04-10 | 4 |
| Clemson | 228 | 2024-02-20 | 2026-04-24 | 6 |
| Coastal Carolina | 324 | 2024-02-16 | 2025-02-17 | 5 |
| Cornell | 172 | 2025-03-07 | 2025-03-07 | 1 |
| Davidson | 2166 | 2025-05-10 | 2025-05-10 | 1 |
| Duke | 150 | 2024-02-16 | 2025-03-12 | 6 |
| East Carolina | 151 | 2024-03-01 | 2025-04-27 | 4 |
| Eastern Michigan | 2199 | 2026-02-18 | 2026-02-18 | 1 |
| Florida | 57 | 2024-06-08 | 2026-05-23 | 6 |
| Florida State | 52 | 2024-03-02 | 2024-05-24 | 4 |
| Fresno State | 278 | 2019-02-22 | 2022-02-26 | 2 |
| Gardner Webb | 2241 | 2024-03-28 | 2025-03-04 | 2 |
| Georgia | 61 | 2025-02-14 | 2026-05-23 | 8 |
| Georgia Southern | 290 | 2025-05-06 | 2025-05-06 | 1 |
| Georgia State | 2247 | 2024-04-14 | 2024-04-14 | 1 |
| Georgia Tech | 59 | 2024-03-17 | 2025-05-06 | 5 |
| Gonzaga | 2250 | 2018-05-04 | 2023-05-24 | 14 |
| Grand Canyon | 2253 | 2018-02-24 | 2022-04-22 | 6 |
| Hawaii | 62 | 2019-04-24 | 2023-02-24 | 3 |
| High Point | 2272 | 2025-03-08 | 2025-03-08 | 1 |
| Illinois | 356 | 2024-03-02 | 2024-03-02 | 2 |
| Indiana | 84 | 2018-03-02 | 2024-02-18 | 7 |
| Iowa | 2294 | 2020-02-22 | 2025-05-17 | 7 |
| James Madison | 256 | 2024-05-31 | 2024-06-02 | 3 |
| Kansas State | 2306 | 2019-02-22 | 2025-02-17 | 3 |
| Kennesaw State | 338 | 2025-02-18 | 2026-04-25 | 3 |
| Kentucky | 96 | 2025-05-20 | 2026-05-19 | 10 |
| LSU | 99 | 2025-05-23 | 2026-05-20 | 7 |
| Lenoir-Rhyne | missing | 2025-02-04 | 2025-02-04 | 1 |
| Liberty | 2335 | 2024-03-29 | 2026-04-03 | 4 |
| Louisville | 97 | 2024-03-21 | 2026-05-14 | 15 |
| Loyola Marymount | 2351 | 2018-04-06 | 2023-04-30 | 11 |
| Maryland | 120 | 2025-04-25 | 2025-04-25 | 1 |
| Mercer | 2382 | 2024-03-22 | 2026-05-15 | 2 |
| Miami | 2390 | 2024-05-21 | 2025-03-14 | 3 |
| Michigan State | 127 | 2024-03-02 | 2026-02-15 | 4 |
| Middle Tennessee State | 2393 | 2025-02-28 | 2026-03-29 | 5 |
| Milwaukee | 270 | 2026-05-29 | 2026-05-31 | 3 |
| Minnesota | 135 | 2025-04-19 | 2025-04-19 | 1 |
| Mississippi State | 344 | 2025-05-21 | 2026-05-21 | 3 |
| Missouri | 142 | 2025-05-20 | 2026-05-20 | 7 |
| NC State | 152 | 2024-02-28 | 2026-05-30 | 13 |
| Nebraska | 158 | 2020-02-21 | 2025-04-25 | 6 |
| North Carolina | 153 | 2024-02-27 | 2025-05-08 | 6 |
| Northeastern | 111 | 2025-03-16 | 2025-04-06 | 2 |
| Notre Dame | 87 | 2024-03-08 | 2026-03-15 | 5 |
| Oklahoma | 201 | 2019-02-22 | 2026-05-19 | 7 |
| Old Dominion | 295 | 2024-03-30 | 2025-03-02 | 4 |
| Ole Miss | 145 | 2025-05-21 | 2026-05-19 | 5 |
| Oregon | 2483 | 2022-02-18 | 2025-05-17 | 10 |
| Oregon State | 204 | 2022-06-03 | 2023-03-07 | 4 |
| Pacific | 279 | 2019-05-10 | 2023-03-19 | 12 |
| Pepperdine | 2492 | 2019-03-15 | 2023-04-02 | 12 |
| Pittsburgh | 221 | 2024-05-22 | 2025-05-10 | 3 |
| Point Loma Nazarene | missing | 2024-06-03 | 2024-06-03 | 1 |
| Portland | 2501 | 2019-04-18 | 2023-04-16 | 12 |
| Presbyterian | 2506 | 2024-02-20 | 2024-03-28 | 2 |
| Princeton | 163 | 2025-03-14 | 2025-03-14 | 1 |
| Purdue | 2509 | 2024-03-01 | 2024-03-01 | 1 |
| Richmond | 257 | 2025-03-19 | 2025-05-09 | 2 |
| Rutgers | 164 | 2024-03-12 | 2025-04-19 | 3 |
| Saint Mary's | 2608 | 2018-04-14 | 2023-05-24 | 8 |
| San Diego | 301 | 2017-04-20 | 2025-05-03 | 203 |
| San Diego State | 21 | 2018-03-13 | 2023-04-18 | 11 |
| San Francisco | 2539 | 2019-03-22 | 2025-05-03 | 15 |
| Santa Clara | 2541 | 2018-03-16 | 2024-05-04 | 12 |
| Seattle | 2547 | 2020-02-22 | 2020-02-23 | 2 |
| South Alabama | 6 | 2024-03-30 | 2024-03-30 | 1 |
| South Carolina | 2579 | 2024-02-21 | 2026-05-19 | 12 |
| Southeastern Louisiana | 2545 | 2024-03-01 | 2024-03-01 | 1 |
| Southern California | 30 | 2021-03-23 | 2024-05-05 | 2 |
| Southern Mississippi | 2572 | 2024-04-14 | 2025-05-11 | 2 |
| St. Bonaventure | 179 | 2025-02-28 | 2025-03-02 | 3 |
| St. John's | 2599 | 2019-03-01 | 2019-03-04 | 3 |
| St. Louis | 139 | 2024-04-28 | 2024-04-28 | 1 |
| Stanford | 24 | 2022-04-22 | 2026-04-12 | 4 |
| Stony Brook | 2619 | 2025-04-18 | 2025-04-18 | 1 |
| Tampa | missing | 2024-06-02 | 2024-06-02 | 1 |
| Tennessee | 2633 | 2025-03-28 | 2026-05-20 | 17 |
| Texas | 251 | 2025-05-22 | 2026-05-22 | 2 |
| Texas A&M | 245 | 2025-05-21 | 2026-05-22 | 4 |
| The Citadel | 2643 | 2026-03-06 | 2026-03-08 | 3 |
| Troy | 2653 | 2025-02-23 | 2025-02-23 | 1 |
| Tulane | 2655 | 2025-04-26 | 2025-04-27 | 2 |
| UC Riverside | 27 | 2018-05-08 | 2021-03-14 | 6 |
| UC San Diego | 28 | 2021-03-04 | 2023-05-07 | 11 |
| UCF | 2116 | 2026-05-29 | 2026-05-31 | 3 |
| UNC Asheville | 2427 | 2024-03-02 | 2024-03-02 | 1 |
| UNC Greensboro | 2430 | 2024-03-22 | 2024-03-22 | 1 |
| UNC Wilmington | 350 | 2024-04-02 | 2026-03-27 | 6 |
| Utah | 254 | 2019-02-23 | 2019-02-24 | 2 |
| VCU | 2670 | 2024-02-27 | 2025-05-09 | 3 |
| Vanderbilt | 238 | 2022-06-03 | 2026-05-20 | 19 |
| Virginia | 258 | 2024-02-23 | 2026-05-14 | 9 |
| Virginia Tech | 259 | 2024-03-08 | 2025-03-15 | 5 |
| Wake Forest | 154 | 2024-03-21 | 2025-05-10 | 4 |
| West Virginia | 277 | 2024-03-07 | 2024-04-27 | 3 |
| Western Kentucky | 98 | 2025-03-22 | 2026-04-25 | 3 |
| Wichita State | 2724 | 2024-02-23 | 2024-02-25 | 3 |
| William and Mary | 2729 | 2024-03-26 | 2026-03-27 | 2 |
| Winthrop | 2737 | 2024-03-03 | 2024-03-03 | 1 |
| Xavier | 2752 | 2026-04-10 | 2026-04-10 | 1 |

## Next pass

Read full player_stats.json in a repository checkout, reproduce directory merge logic including attendance corrections, derive exact first dates, check primary mark history and image availability for each represented school-season, then add a shared verified college logo registry to both directories and profiles. Keep statistics and identity grouping unchanged. Do not treat source logo history as verification of the actual CDN artwork.

## Conservative first implementation

Four selected marks have visually inspected transparent previews: Fresno State 2016–pre-refresh 2019; GCU arched mark 2015–June 2023; UC Riverside 2012–June 2020; LMU 2008–2018 (conservatively no ambiguous 2019 dates). All other school marks remain unchanged. The shared resolver uses the player's first witnessed date and keeps the existing ESPN image as a fallback. Source previews were visually inspected; original downloads were unavailable in the editing environment, so the registry references source-hosted artwork rather than claiming locally vendored assets. No stats, identity, or layout changes. Full baseball row inventory remains pending.

## Second pass — SportsLogos.Net primary-logo timelines

- Added CSUN 2014–2023 primary matador/cape mark for verified 2014–2023 era; conservative cutoff June 1, 2023 to avoid the unverified transition date. All four archived Northridge school games are in February–May 2023. Source: https://www.sportslogos.net/logos/view/62897842014/Cal-State-Northridge-Matadors-Logo/2014/Primary-Logo . Fixed the misspelled school string's **logo mapping only**, not identity grouping or attendance data.
- Added Vanderbilt 2022–2025 gradient V, unveiled March 22, 2022; conservative cutoff January 1, 2025 pending exact transition date. Archived 2022 and 2024 games are eligible; no 2025 dates overridden. Source: https://www.sportslogos.net/logos/view/89595842022/Vanderbilt-Commodores-Logo/2022/Primary-Logo . Old Star V not added because all archived Vanderbilt baseball dates are after March 2022.
- Replaced GCU historical asset URL with the directly opened SportsLogos.Net primary mark, verified 2015–2023. Source: https://www.sportslogos.net/logos/view/505089242015/Grand-Canyon-Antelopes-Logo/2015/Primary-Logo . Fresno State existing asset verified against the primary-logo page.
- No new change for San Diego State (primary since 2013), San Diego (since 2016), Pacific (since 1998), Louisville (since 2013), UC San Diego (since 2018; represented baseball games 2021–23), Virginia (since 2020; represented games 2024–26), Pittsburgh (since 2019; represented games 2024–25), Campbell (represented games 2024–25, after 2023 rebrand). Long Beach State and Fullerton absent from cross-school merge inventory. LMU and UCR SportsLogos.Net image previews show white backgrounds; do not substitute those particular files for the first-pass URLs without alpha verification.
- Direct source images for CSUN, Vanderbilt and GCU were opened and visually inspected; direct binary download/alpha-channel inspection and deployed browser verification unavailable. Existing ESPN fallback preserved. No new layout, statistics or identity changes.
