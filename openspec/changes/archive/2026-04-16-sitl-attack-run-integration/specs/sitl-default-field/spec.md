## MODIFIED Requirements

### Requirement: Field profile contains required sections
The system SHALL provide a valid field profile JSON file at `data/fields/sitl_default/field.json` that can be loaded by `load_field_profile("sitl_default")`.

#### Scenario: Field profile contains required sections
- **WHEN** `data/fields/sitl_default/field.json` is parsed
- **THEN** it contains `name`, `boundary` (with `polygon`), `landing` (with `approach_waypoint` and `touchdown_point`), `scan_waypoints` (with `waypoints` and `altitude_m`), `loiter_point`, `attack_run` (with `approach_distance_m`, `exit_distance_m`, `release_acceptance_radius_m`), and `safety_buffer_m`

#### Scenario: Attack run config values are reasonable for SITL field
- **WHEN** the `attack_run` section of `data/fields/sitl_default/field.json` is validated
- **THEN** `approach_distance_m` and `exit_distance_m` SHALL be <= 300m (field is ~1km across), ensuring approach/exit points remain within or near the geofence for center-field drop points

#### Scenario: Attack run config loads with correct defaults
- **WHEN** `load_field_profile("sitl_default")` is called
- **THEN** the returned `FieldProfile.attack_run` SHALL have `approach_distance_m=200`, `exit_distance_m=200`, `release_acceptance_radius_m=0`
