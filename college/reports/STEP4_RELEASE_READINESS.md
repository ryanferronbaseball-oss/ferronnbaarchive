# Step 4: Release readiness and source-audited arenas

**October 15, 2026 · Development branch `college-import-pilot` · Not published**

## Sourced venue pilot

- **94 attended games**, 1,825 certified player appearances, 1,034 distinct athlete identities retained.
- **20 per-game venues verified** across **15 distinct recorded arena names**, leaving **74 games with unverified venues**. Nothing inferred from a listed host school.
- **5 neutral-site games distinguished from designated home/away status**: attendance #60 (The Pavilion at JSerra, SoCal Challenge), #80 (Spectrum Center, 2024 NCAA tournament), #82 (First Horizon Coliseum, Michigan–Wake Forest), #90 and #91 (Spectrum Center, 2025 ACC tournament).
- Name reflects its game-date form where sourced: e.g., PNC Arena in January 2024, Lenovo Center in 2025. A later canonical physical-building alias system requires separate verification.
- Every entry in `data/verified_venues.csv` carries date-specific research provenance URL, attendance ID and source event ID. `scripts/build_site_data.py` reapplies records on future imports, rejects duplicates and mismatched IDs, and keeps unknown arenas blank.
- College game detail and attendance insights explicitly label/exclude incomplete arena information. Home-team wins are identified as **listed** home-team wins, since neutral-site games have designated home teams.

## Automated regression additions

- Seven-page static parity, exact 94/1,825/75 data contract and expected 20 verified game venues, 15 venue names, five neutral games.
- HTTP-based Chromium checks for First Horizon Coliseum neutral-site detail and a sourced Spectrum Center venue leaderboard, including visible exclusion of the 74 unknown locations.
- Workflow path triggers extended to venue data and adapter. Existing NBA main branch and production URL remain unchanged.

## Launch blocks that still need resolution

1. **Venue research:** individually corroborate the 74 remaining games against official dated event records; do not extrapolate home-school location.
2. **Accessibility review:** manual keyboard navigation, focus state, explicit labels, screen-reader live updates, table headers, small-screen overflow and contrast across all seven pages. Current automated browser checks are not a WCAG certification.
3. **Field-by-field sources:** scoring and team minutes reconcile for 94/94, but that alone does not independently certify each assists/turnovers/rebounds field.
4. **Athlete aliases:** 17 provisional `official:` IDs should be audited against stable provider IDs, never merged by name alone.
5. **End-to-end sign-off:** user to compare actual desktop/mobile college previews to NBA, and authorize a merge, navigation change, or GitHub Pages release explicitly. No publication is authorized by this venue pilot.

This is a partial Step 4 implementation, **not final launch approval**.
