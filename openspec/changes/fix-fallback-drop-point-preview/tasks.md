## 1. Import

- [x] 1.1 Add `haversineDistance` and `bearingBetweenPoints` to the `logic.mjs` import in `app.js`

## 2. Fix approach heading

- [x] 2.1 In `renderAttackRun()`, replace hardcoded `landing.heading_deg` with dynamic heading: compute distance from drop point to `derivedApproach`, use `bearingBetweenPoints(dropPoint, approach)` when distance > 30m, else use `(landing.heading_deg + 180) % 360`
- [x] 2.2 Verify approach and exit lines render correctly for a drop point far from approach point
- [x] 2.3 Verify approach and exit lines render correctly for a drop point near (within 30m of) the approach point

## 3. Add exit distance capping

- [x] 3.1 In `renderAttackRun()`, after computing approach heading, compute `min_handoff = max(30, min(approach_distance_m, runway_length_m))` and `max_safe_exit = max(0, distance_to_approach - min_handoff)`, then use `min(exit_distance_m, max_safe_exit)` for the exit point
- [x] 3.2 Verify exit line is shortened when it would extend past the landing approach point
