## 1. Algorithm Alignment (logic.mjs)

- [x] 1.1 Add midpoint polygon inclusion check to `generateBoustrophedonScan`: after computing `leftX`/`rightX` from intersections, check `(leftX + rightX) / 2` is inside `scanPolygon` via `pointInPolygonXY`, skip segment if not
- [x] 1.2 Add endpoint inset to `generateBoustrophedonScan`: compute `insetM = Math.min(5.0, Math.max((exitX - entryX) / 10.0, 1.0))`, adjust entry/exit, handle `entryX > exitX` fallback
- [x] 1.3 Fix climbout distance in `deriveTakeoffPreview`: change climbout `destinationPoint` distance from `fieldProfile.landing.runway_length_m` to `fieldProfile.landing.runway_length_m * 0.5`

## 2. Takeoff Path Visualization (app.js)

- [x] 2.1 Add `takeoffPathLine` to `mapState.overlays`
- [x] 2.2 Implement `renderTakeoffPath` function: read `derivedTakeoff` from validation, draw amber polyline from `(start_lat, start_lon)` to `(climbout_lat, climbout_lon)`
- [x] 2.3 Call `renderTakeoffPath` from `renderOverlays`

## 3. Inter-Segment Connection Lines (app.js)

- [x] 3.1 Add `missionChainLine` to `mapState.overlays`
- [x] 3.2 Implement `renderMissionChain` function: draw gray dashed polyline connecting climbout → scan[0] → scan[last] → approach (degrade gracefully when phases missing)
- [x] 3.3 Call `renderMissionChain` from `renderOverlays`

## 4. Attack Run Preview Label (app.js)

- [x] 4.1 Update `renderAttackRun` drop point marker label from `"降级投弹点"` to `"降级投弹点 (预览)"`

## 5. Cleanup

- [x] 5.1 Ensure `takeoffPathLine` and `missionChainLine` are cleaned up in `destroyMap` overlay reset loop
- [x] 5.2 Verify all new overlays are removed when `renderX` detects missing data (e.g., scan preview empty → remove mission chain)
