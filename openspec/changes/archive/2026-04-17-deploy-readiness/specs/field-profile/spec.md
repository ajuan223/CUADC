## MODIFIED Requirements

### Requirement: FieldProfile data model
The system SHALL define `FieldProfile(BaseModel)` with fields: `name` (str), `description` (str), `coordinate_system` (str), `boundary` (BoundaryConfig), `landing` (LandingConfig), `scan_waypoints` (ScanWaypointsConfig), `loiter_point` (LoiterPointConfig), `safety_buffer_m` (float), `attack_run` (AttackRunConfig).

`LandingConfig` SHALL include an optional `use_do_land_start` field (bool, default `True`). When `True`, the landing sequence generator SHALL produce DO_LAND_START + approach + NAV_LAND (3 items). When `False`, it SHALL produce approach (NAV_WAYPOINT) + NAV_LAND (2 items).

#### Scenario: Load valid field JSON with default landing config
- **WHEN** `load_field_profile()` is called with a field JSON that omits `landing.use_do_land_start`
- **THEN** `field_profile.landing.use_do_land_start` returns `True` (default)

#### Scenario: SITL field sets use_do_land_start to false
- **WHEN** `load_field_profile("sitl_default")` is called and `data/fields/sitl_default/field.json` contains `"use_do_land_start": false`
- **THEN** `field_profile.landing.use_do_land_start` returns `False` and landing sequence produces 2 items (NAV_WAYPOINT + NAV_LAND)

#### Scenario: Real field uses DO_LAND_START by default
- **WHEN** `load_field_profile("zijingang")` is called and the field JSON does not specify `use_do_land_start`
- **THEN** `field_profile.landing.use_do_land_start` returns `True` and landing sequence produces 3 items (DO_LAND_START + approach + NAV_LAND)
