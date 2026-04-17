## Context

The current field editor in `src/field_editor/` is a plain-JS AMap-based planning tool that already derives landing approach geometry, scan previews, import/export conversion, and map overlays in real time. However, the current UX still breaks core operator workflows: the page height can be driven by the long left-side form instead of keeping the map fitted to the viewport, the boundary drawing interaction is still tied to a sticky `MouseTool.polygon()` flow, the import path assumes WGS84 even when existing field files are marked `GCJ-02`, and the UI only surfaces a narrow subset of the mission geometry that the Python runtime later derives in `src/striker/flight/mission_geometry.py`.

Current AMap JS API v2 docs still support the pieces we need:
- `MouseTool.rectangle()` with a `draw` event that returns the finished overlay
- `PolygonEditor` for editing an existing polygon after the initial selection
- `TileLayer.Satellite` + `TileLayer.RoadNet` for imagery mode
- terrain view only when the map is initialized with JS API `v2.1Beta`, `viewMode: "3D"`, and `terrain: true`

That means the most robust implementation is not to keep fighting the current freehand polygon draw mode. Instead, the field editor should use rectangle selection for fast boundary creation, convert that rectangle into the editor’s polygon model, and then hand refinement off to `PolygonEditor`.

## Goals / Non-Goals

**Goals:**
- Keep the map panel pinned to the browser viewport while the left control area scrolls independently.
- Replace the current boundary selection flow with a deterministic rectangle-first interaction that does not leave the cursor or editor in a stuck state.
- Support operator-selectable normal, satellite, and terrain-oriented map views using currently documented AMap APIs.
- Make field import/export coordinate handling consistent with the declared source coordinate system so repeated edits do not accumulate a systematic north/south shift.
- Surface planning outputs that match the project’s current runtime geometry logic closely enough for operators to validate touchdown, approach, scan, and takeoff setup before export.
- Show explicit safety warnings for obviously unsafe descent or climb geometry as editor-time guidance.

**Non-Goals:**
- Replacing AMap with a different map provider.
- Rebuilding the field editor in a frontend framework.
- Changing the Python runtime mission-generation algorithms beyond mirroring their current behavior in the editor.
- Introducing flight-controller parameter tuning or autonomous behavior changes in this change.

## Decisions

- Use a fixed-height two-column shell (`100vh`) with the sidebar and map column each managing their own overflow.
  - Alternative considered: keep the current document-flow layout and only reduce panel sizes. Rejected because the core complaint is viewport instability, not visual density.
- Change the initial boundary creation interaction from `MouseTool.polygon()` to `MouseTool.rectangle()`, then convert the resulting rectangle bounds into a polygon and refine it with `PolygonEditor`.
  - Alternative considered: keep freehand polygon drawing and only add more cleanup around event listeners. Rejected because the requirement specifically calls out rectangle selection reliability, and the documented rectangle draw flow is simpler and less error-prone.
- Introduce an explicit interaction reset path that closes MouseTool modes, closes the polygon editor, clears pending runway clicks, and updates status text before entering another interaction.
  - Alternative considered: continue layering independent mode handlers. Rejected because the current inconsistent states come from partially overlapping interaction lifecycles.
- Switch AMap loader initialization to `v2.1Beta` so the editor can expose a terrain-oriented mode using documented `terrain: true` initialization, while still supporting standard and satellite modes.
  - Alternative considered: simulate “terrain-like” mode only with style changes. Rejected because current AMap docs expose real terrain rendering only through `v2.1Beta` initialization.
- Preserve the editor’s internal map geometry in GCJ-02, but make import respect the incoming `coordinate_system` instead of always assuming WGS84.
  - Alternative considered: force every imported file through WGS84 conversion regardless of metadata. Rejected because it explains the observed repeated-offset bug when existing GCJ-02 files are reopened and re-exported.
- Extend the editor-side derived output model so it mirrors current project geometry: touchdown facts, derived landing approach, scan preview count, and takeoff/climbout preview derived from the same runway/altitude assumptions as `src/striker/flight/mission_geometry.py`.
  - Alternative considered: only show the current approach preview. Rejected because the requirement is to make the editor useful for planning, not only for field shape editing.
- Treat unsafe descent/climb indicators as advisory warnings, not blocking validation failures.
  - Alternative considered: make those conditions blocking. Rejected because these thresholds are heuristic operator guidance rather than hard runtime invariants today.

## Risks / Trade-offs

- [AMap `v2.1Beta` behaves differently from `2.0`] → Keep the map abstraction shallow, preserve current plugins only, and regression-test the editor logic separately from map bootstrapping.
- [Rectangle draw loses arbitrary-shape flexibility] → Convert the rectangle into a polygon immediately and keep `PolygonEditor` plus text editing for refinement.
- [Editor-side geometry drifts from Python runtime logic] → Mirror the current Python mission-geometry formulas directly and add tests around the shared assumptions.
- [Existing GCJ-02 field files remain ambiguous] → Respect explicit `coordinate_system` metadata and keep export normalized to WGS84 for runtime compatibility.

## Migration Plan

1. Add the remaining R3 OpenSpec specs/tasks so the new behavior is explicit before code changes.
2. Refactor field-editor state and interaction handling around rectangle-first selection, basemap switching, and viewport-stable layout.
3. Add editor logic tests for coordinate-system handling and planning summaries.
4. Run targeted web/editor and export validation tests.

## Open Questions

- Whether the repo should eventually normalize all checked-in field files to WGS84 once the editor import path is fixed.
- Whether future iterations should let operators drag the derived approach/takeoff helper points directly, or keep them strictly derived from runway and altitude facts.
