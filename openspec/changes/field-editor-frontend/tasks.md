## 1. Scaffold the static field editor

- [ ] 1.1 Create `src/field_editor/` with a buildless static app skeleton (`index.html`, `app.js`, `styles.css`)
- [ ] 1.2 Add a two-pane layout: sidebar form + map canvas, with room for validation messages and import/export controls

## 2. Implement AMap bootstrap and credential management

- [ ] 2.1 Add a credential form for the AMap JS API 2.0 initialization flow, including persistence to `localStorage`
- [ ] 2.2 Add actions to retry map initialization, update stored credentials, and clear invalid credentials
- [ ] 2.3 Initialize the map at Zijingang (`30.27, 120.095`) zoom 15 only after credentials are available

## 3. Define editor state to mirror `FieldProfile`

- [ ] 3.1 Create a frontend state object that mirrors the current Python `FieldProfile` schema exactly
- [ ] 3.2 Initialize new documents with backend-compatible defaults for fields such as `coordinate_system`, `attack_run`, and `landing.use_do_land_start`
- [ ] 3.3 Keep sidebar form controls and map overlays synchronized through a single source of truth

## 4. Add coordinate conversion utilities

- [ ] 4.1 Implement GCJ-02 → WGS84 conversion for export
- [ ] 4.2 Implement WGS84 → GCJ-02 conversion for import and map rendering
- [ ] 4.3 Add focused tests for round-trip conversion accuracy on representative China coordinates

## 5. Implement boundary drawing and polygon editing

- [ ] 5.1 Use AMap drawing tools to create a boundary polygon on the map
- [ ] 5.2 Use polygon editing capabilities to support dragging, adding, and removing boundary vertices
- [ ] 5.3 Sync boundary vertex edits back into sidebar coordinate fields in real time
- [ ] 5.4 Enforce blocking validation for fewer than 3 distinct boundary vertices
- [ ] 5.5 Ensure exported polygons are closed (`first == last`)

## 6. Implement landing editing and derived approach preview

- [ ] 6.1 Add touchdown placement and dragging on the map, synchronized with `landing.touchdown_point`
- [ ] 6.2 Add form inputs for `heading_deg`, `glide_slope_deg`, `approach_alt_m`, `runway_length_m`, and `use_do_land_start`
- [ ] 6.3 Render touchdown heading and derived landing approach preview using the same semantics as `derive_landing_approach()` in `mission_geometry.py`
- [ ] 6.4 Add blocking validation for touchdown outside geofence, non-positive runway length, invalid approach altitude, approach distance below 200m, and derived approach outside geofence

## 7. Implement loiter point editing

- [ ] 7.1 Add loiter marker placement and dragging on the map
- [ ] 7.2 Add form inputs for loiter altitude and radius, and render the loiter circle live
- [ ] 7.3 Add blocking validation for loiter center outside geofence
- [ ] 7.4 Add advisory-only warning when the loiter circle crosses the boundary

## 8. Implement scan parameter editing and preview

- [ ] 8.1 Add form inputs for `scan.altitude_m`, `scan.spacing_m`, and `scan.heading_deg`
- [ ] 8.2 Port the current boustrophedon scan-generation semantics from `generate_boustrophedon_scan()` to the frontend preview layer
- [ ] 8.3 Render scan preview as a polyline and update it in real time when inputs change
- [ ] 8.4 Add blocking validation for non-positive scan spacing

## 9. Implement attack run parameter editing

- [ ] 9.1 Add form inputs for `attack_run.approach_distance_m`, `attack_run.exit_distance_m`, and `attack_run.release_acceptance_radius_m`
- [ ] 9.2 Preserve these values on import/export without claiming a runtime-authoritative attack path preview
- [ ] 9.3 Add explanatory UI copy that actual attack approach geometry is runtime-dependent

## 10. Implement import and export

- [ ] 10.1 Import `field.json`, validate basic structure, convert coordinates for map display, and populate editor state
- [ ] 10.2 Fit the map to imported geometry and restore all supported overlays
- [ ] 10.3 Export the current state as WGS84 `field.json` matching the backend schema exactly
- [ ] 10.4 Disable export while blocking validation errors exist and render a clear error list
- [ ] 10.5 Add a backend smoke check that exported JSON passes `FieldProfile.model_validate()`

## 11. Validate end-to-end behavior

- [ ] 11.1 Manual test: create a new field from scratch, export it, and verify backend validation succeeds
- [ ] 11.2 Manual test: import `data/fields/sitl_default/field.json`, modify it, re-export it, and verify backend validation succeeds
- [ ] 11.3 Manual test: boundary with too few vertices, touchdown outside fence, loiter outside fence, invalid approach geometry, zero/negative spacing, and zero/negative safety buffer
- [ ] 11.4 Confirm the UI distinguishes blocking validation errors from advisory warnings