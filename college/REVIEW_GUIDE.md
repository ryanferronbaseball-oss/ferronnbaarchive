# Courtside Archive College — visual acceptance checklist

This is the **unpublished development version**. Its pages are separate from the NBA site. The production `main` branch should **not** be merged or navigationally linked until explicit owner approval.

## Preview without publishing

Open [College seven-page browser QA](https://github.com/ryanferronbaseball-oss/ferronnbaarchive/actions/workflows/college-step3-parity.yml), select the newest passing **College Step 3 seven-page parity** run on `college-import-pilot`, and download the **college-step3-seven-page-review** artifact at the bottom of that run. It contains two screenshot/report directories, `step3-browser/` for home/game/records/milestones/insights and `step2-browser/` for the players and profile pages. Review these screenshot previews:

- `college-home-desktop.png` — the full 94-game college attendance homepage.
- `college-home-mobile.png` — the narrow-screen homepage.
- `college-game-details.png` — Utah State at San Diego, attendance #59, with sourced Jenny Craig Pavilion and the full player box score.
- `college-single-game-records.png` — single-game leaderboards.
- `college-milestones.png` — milestones, records and team results.
- `college-attendance-insights.png` and `college-insights-mobile.png` — team/arena/attendance analytics.
- `college-stats-desktop.png` and `college-stats-mobile.png` — player-leaderboard snapshots.
- `townsend-profile-desktop.png` and `sallis-multi-school-gamelog.png` — cross-linked sourced player profiles and Gonzaga/Wake Forest school transfer filtering.

The same workflow validates the 240-official-field fixture, original NBA-style seven-page HTML parity and HTTP Chromium functionality. **A recent passing run is required** before treating these screenshots as QA-approved.

## Interactions to check in a local browser

Because GitHub Actions screenshots are static, to test interactivity locally clone/download the development branch, and from the repository root serve it over HTTP (CSV/JSON requests do not run reliably from `file://`):

```sh
python3 -m http.server 8000
```

Then visit `http://localhost:8000/college/index.html`. Check:

1. **Home:** All 94 game rows; year and matchup search; era-specific arena names.
2. **Game:** `college/game.html?id=59` is Utah State 91 @ San Diego 89 (OT), with Jase Townsend's profile linked; `?id=76` is California vs SDSU in the Pavilion at JSerra, visibly designated **Neutral site**.
3. **Players:** Traditional / Advanced / Per 36 and all category filters; Jase Townsend (14 attended games / 170 points); Hunter Sallis unified across Gonzaga and Wake Forest.
4. **Records:** All six record tiles and searchable source-traced player lines.
5. **Milestones:** Records, teams, performance milestones, and legendary performance tabs all work.
6. **Insights:** Complete team/arena history; 18 distinct physical arenas across 19 historical names, with PNC/Lenovo counted together; six neutral-site games retain listed home-team designations.
7. **Accessibility:** Desktop keyboard focus/Tab navigation, form accessible labels, contrast, and no document-level overflow on 390px mobile width.

## Data and release caveats

**Venue records:** 94 of 94 game locations sourced, with source links stored in `data/verified_venues.csv`.

**Stats:** 1,825 player-game rows retained, 94/94 score/minute totals reconciled. A new university source check validates 240 selected cells and repaired five individual Colorado fields. The *rest* of the historical secondary stat fields have not each been externally verified.

**Identity:** 17 college-player identities remain provisional `official:` records rather than confirmed ESPN player IDs; do not merge these by matching name alone.

**Launch guard:** Do not press **Merge pull request**, publish Pages for this branch, or add navigation to NBA main until owner gives explicit authorization. A draft pull request is solely a review vehicle.
