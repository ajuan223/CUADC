## Requirements

### Requirement: Procedural mission geometry derives landing approach from runway facts
The system SHALL derive the fixed-wing landing approach waypoint from field configuration facts instead of consuming a user-authored approach coordinate. The derived approach geometry SHALL use `touchdown_point`, `heading_deg`, `approach_alt_m`, and `glide_slope_deg` as the authoritative inputs.

#### Scenario: Derive approach waypoint from touchdown and glide slope
- **WHEN** the field profile provides touchdown point, heading 180°, touchdown altitude 0m, approach altitude 30m, and glide slope 3°
- **THEN** the system SHALL compute the landing approach waypoint at approximately 572m opposite the runway heading (i.e. heading 0°) from the touchdown point
- **AND** the computed waypoint altitude SHALL be 30m

#### Scenario: Approach geometry uses touchdown-relative altitude delta
- **WHEN** the touchdown altitude is non-zero (e.g. 5m above home)
- **THEN** the system SHALL compute horizontal approach distance from `(approach_alt_m - touchdown_alt_m) / tan(glide_slope_deg)`
- **AND** it SHALL NOT assume touchdown altitude is always zero

#### Scenario: Reject invalid glide slope inputs
- **WHEN** `glide_slope_deg` is zero, negative, or otherwise produces a non-finite descent geometry
- **THEN** the system SHALL reject landing geometry generation with an explicit glide-slope validation error

### Requirement: Procedural mission geometry validates derived landing sequence
The system SHALL validate the computed landing geometry before mission generation. Invalid geometry MUST be rejected explicitly instead of silently using a bad approach point.

#### Scenario: Reject non-descending approach geometry
- **WHEN** `approach_alt_m` is less than or equal to touchdown altitude
- **THEN** the system SHALL reject landing geometry generation with an explicit validation error

#### Scenario: Reject out-of-bounds derived approach point
- **WHEN** the computed approach waypoint falls outside the field geofence
- **THEN** the system SHALL reject landing geometry generation with an explicit validation error that identifies the landing approach geometry as invalid

### Requirement: Procedural mission geometry generates scan path using Boustrophedon algorithm
The system SHALL generate scan mission waypoints using a deterministic Boustrophedon (lawnmower) coverage path planning algorithm from field boundary and scan constraint inputs, rather than requiring the field file to enumerate scan waypoints directly.

#### Scenario: Generate deterministic lawnmower scan path
- **WHEN** the field profile provides a valid boundary polygon (1km x 1km), scan altitude 80m, scan spacing 100m, and scan heading 0° (north-south sweeps)
- **THEN** the system SHALL generate approximately 10 sweep lines with ~20 waypoints in Boustrophedon order
- **AND** the generated path SHALL be suitable for direct mission upload without additional hand-authored scan waypoints

#### Scenario: Scan path covers the entire polygon
- **WHEN** the Boustrophedon algorithm is applied to a convex polygon
- **THEN** every point inside the polygon SHALL be within `scan_spacing_m` of at least one sweep line

#### Scenario: Reject invalid polygon for scan generation
- **WHEN** the boundary polygon has fewer than 3 vertices
- **THEN** the system SHALL raise a validation error

### Requirement: Procedural mission geometry generates takeoff path from runway facts
The system SHALL generate fixed-wing takeoff mission geometry from runway/location facts instead of requiring users to pre-author takeoff mission points.

#### Scenario: Takeoff follows runway axis
- **WHEN** the field profile provides touchdown at (30.261, 120.095), heading 180°, runway length 200m, takeoff alt 80m
- **THEN** the system SHALL compute a takeoff start point approximately 80m behind the runway midpoint along heading 0°
- **AND** the climb-out waypoint SHALL be 200m beyond the touchdown along heading 180° at 80m altitude

#### Scenario: Reject zero or negative runway length
- **WHEN** `runway_length_m` is 0 or negative
- **THEN** the system SHALL raise a validation error

#### Scenario: Reject takeoff altitude below runway
- **WHEN** `takeoff_alt_m` is less than or equal to the runway altitude
- **THEN** the system SHALL raise a validation error

### Requirement: Unified mission geometry result object
The procedural mission geometry module SHALL produce a unified result object that bundles all generated mission items and key sequence indices for consumption by the mission upload pipeline.

#### Scenario: MissionGeometryResult computes correct indices
- **WHEN** a result has 8 scan waypoints and `include_dummy_home=True`
- **THEN** `takeoff_start_seq` SHALL be 1
- **AND** `scan_start_seq` SHALL be 3
- **AND** `scan_end_seq` SHALL be 10
- **AND** `landing_start_seq` SHALL be 11
