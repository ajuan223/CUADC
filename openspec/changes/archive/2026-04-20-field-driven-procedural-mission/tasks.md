## 1. Field schema and geometry contract

- [x] 1.1 Redesign `FieldProfile` schema (`src/striker/config/field_profile.py`) to express runway facts (`runway_length_m`, `takeoff_heading_deg`), landing constraints (`touchdown_point`, `heading_deg`, `approach_alt_m`, `glide_slope_deg`), and scan constraints (`scan_spacing_m`, `scan_heading_deg`) — remove `ApproachWaypoint` and `ScanWaypointsConfig.waypoints`
- [x] 1.2 Update default field JSON fixtures under `data/fields/` to the new schema: replace `landing.approach_waypoint` with `approach_alt_m` and `runway_length_m`; replace `scan_waypoints.waypoints` with scan constraint fields
- [x] 1.3 Add/refresh validation tests for the new field schema, including invalid runway facts and invalid landing constraint combinations

## 2. Procedural mission geometry implementation

- [x] 2.1 Create `src/striker/flight/mission_geometry.py` with `MissionGeometryResult` dataclass and entry point `generate_mission_geometry(field_profile) -> MissionGeometryResult` — see spec §Unified mission geometry result object
- [x] 2.2 Implement `derive_landing_approach()` in `mission_geometry.py` — see spec §Glide Slope Reverse Projection algorithm with `destination_point()` + `point_in_polygon()` validation
- [x] 2.3 Add landing geometry validation for non-descending approaches, minimum approach distance (< 200m), and geofence violations — see spec `derive_landing_approach()` code
- [x] 2.4 Implement `generate_boustrophedon_scan()` in `mission_geometry.py` — see spec §Boustrophedon Coverage Path Planning algorithm (polygon rotation → sweep line intersection → Boustrophedon ordering → inverse rotation)
- [x] 2.5 Implement `generate_takeoff_geometry()` in `mission_geometry.py` — see spec §Runway-Aligned Takeoff Geometry algorithm (midpoint → start point at 40% behind midpoint → climb-out beyond far end)
- [x] 2.6 Add unit tests for all three geometry generators: landing approach derivation, Boustrophedon scan, and takeoff geometry — each test scenario from spec requirements

## 3. Mission assembly and runtime integration

- [x] 3.1 Refactor `src/striker/flight/navigation.py` `build_waypoint_sequence()` to accept `MissionGeometryResult` instead of hand-authored scan waypoints and landing items — use `result.scan_waypoints`, `result.landing_approach`, `result.landing_touchdown`
- [x] 3.2 Update `src/striker/flight/landing_sequence.py` to consume `MissionGeometryResult.landing_approach` instead of `landing.approach_waypoint`
- [x] 3.3 Update `src/striker/core/states/preflight.py` and mission upload to call `generate_mission_geometry()` and pass `result.landing_start_seq` to context — see spec `MissionGeometryResult.compute_indices()`
- [x] 3.4 Update `src/striker/core/states/takeoff.py` to use generated takeoff geometry from `MissionGeometryResult` instead of static `NAV_TAKEOFF`
- [x] 3.5 Remove or migrate legacy code paths: `ApproachWaypoint` model, `ScanWaypointsConfig.waypoints` field, and any direct `landing.approach_waypoint` reads

## 4. Verification and migration

- [x] 4.1 Update unit and integration tests (`tests/unit/test_field_profile.py`, `test_states.py`, etc.) to match the new schema and generated mission behavior
- [ ] 4.2 Run SITL validation with `sitl_merged.param` for generated landing/takeoff/scan missions — verify approach point distance matches glide slope formula (3° × 30m ≈ 573m) — **needs live environment**
- [x] 4.3 Update `.agent/skills/sitl-param-merge-rules/SKILL.md` and `docs/` to reflect field-driven procedural model
