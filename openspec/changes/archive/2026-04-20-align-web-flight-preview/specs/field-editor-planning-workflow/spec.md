## MODIFIED Requirements

### Requirement: Boustrophedon scan path generation
The field editor SHALL generate Boustrophedon scan waypoints using the same algorithm as the Python backend `generate_boustrophedon_scan` in `mission_geometry.py`, including midpoint polygon inclusion check and endpoint inset.

#### Scenario: Scan waypoints match Python backend output
- **WHEN** a valid boundary polygon, scan spacing, heading, and boundary margin are provided
- **THEN** generated waypoints SHALL be identical to Python `generate_boustrophedon_scan` output for the same inputs, including midpoint filtering and endpoint inset

#### Scenario: Midpoint check filters invalid segments
- **WHEN** a horizontal scan line produces an intersection pair whose midpoint falls outside the shrunk polygon
- **THEN** that segment SHALL be skipped (no waypoints generated)

#### Scenario: Endpoint inset applied to all valid segments
- **WHEN** a valid scan line segment is found with width > 0
- **THEN** entry and exit points SHALL be inset by `min(5.0, max(segment_width / 10.0, 1.0))` meters from the polygon intersection points

### Requirement: Takeoff climbout distance
The takeoff preview SHALL compute the climbout point at `0.5 × runway_length_m` beyond the touchdown point along the takeoff heading, matching the Python `generate_takeoff_geometry` calculation.

#### Scenario: Climbout distance matches backend
- **WHEN** takeoff geometry is derived from a field profile
- **THEN** the climbout point SHALL be at distance `runway_length_m * 0.5` from touchdown along the runway heading (not `1.0 × runway_length_m`)
