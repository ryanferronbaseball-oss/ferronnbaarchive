# Courtside Archive

A personal sports-attendance archive with a master home and distinct NBA and college basketball experiences.

## Sports gateway — development preview

- **Master site:** `index.html` (canonical `/`) — a unified welcome page with separate NBA and college cards, counts drawn from each league's current `games.csv`, and room for a future MLB archive.
- **NBA archive:** dedicated `nba/index.html` route (`/nba/`), plus all six NBA detail and analytics pages inside `nba/`. The original root game/player/stats/records/milestones/insights URLs now redirect to corresponding NBA paths, preserving query/hash deep links.
- **College archive:** `college/index.html` and the matching seven college pages. College's 94 games and 1,825 player-game rows remain separate from the NBA statistics.
- **Return links:** Both sports have an `All archives` link on every page leading back to `/`.
- **Current NBA game list:** 31 historical attended NBA games, primarily 2006–2018. Player-box-score import is still an incomplete pilot; don't treat NBA cumulative player leaderboards as complete.
- **Current college game list:** 94 games, six known neutral sites, 18 physical arenas across 19 historical venue names.

**Why not combine the databases?** The two leagues use different player, team and source ID systems. One branded master site can navigate to both without treating NCAA performances as NBA box scores. MLB can later become another independent section.

### Preview QA

- [Verified successful integrated GitHub Actions run](https://github.com/ryanferronbaseball-oss/ferronnbaarchive/actions/runs/38789326684): 57 college page checks + 22 college player/profile checks + 34 master/route/mobile checks = **113 passing browser assertions**, in addition to source-field and HTML parity checks.
- [Master homepage, NBA and college mobile/desktop screenshot bundle](https://github.com/ryanferronbaseball-oss/ferronnbaarchive/actions/runs/38789326684/artifacts/11998289959).
- [College visual review guide](college/REVIEW_GUIDE.md).

**Deployment strategy:** The migration is staged on `college-import-pilot` for pre-merge QA. Upon the explicitly requested launch it can be merged into `main` without changing the hosting provider. The old `sports.html` preview redirects to the master root, and existing NBA game/player URLs redirect to `/nba/` while retaining query parameters.

### Approved canonical paths

- Site home: `/` (`index.html`).
- NBA home: `/nba/` (`nba/index.html`); details `/nba/game.html?id=...`, `/nba/player.html?id=...`.
- College home: `/college/` (`college/index.html`); details `/college/game.html?id=...`, `/college/player.html?id=...`.
- Old NBA root links, including `game.html?id=...`, remain compatible via redirects.
- New sports can be added as dedicated folders later.

## Hosting

The repository is structured for static GitHub Pages hosting. An owner-approved release can deploy via the repository's Pages settings. The combined-site preview does not require a paid hosting service.

## Data quality

The original NBA raw attendance records, import queue and historical reconciliation remain in `data/`; that portion is an incomplete pilot.

The college `college/data/` tables have full verified game scoring/minute totals, source-cited venue history and a separate official stat-field spot-check regression. Its provisional cross-source player identities are deliberately not conflated with NBA players or invented ESPN IDs.

**Status: The owner approved publishing one master site with dedicated NBA and college routes. QA must be successful before promoting this branch to production.**
