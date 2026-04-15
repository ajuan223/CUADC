## ADDED Requirements

### Requirement: SITL default field configuration file exists
The system SHALL provide a valid field profile JSON file at `data/fields/sitl_default/field.json` that can be loaded by `load_field_profile("sitl_default")`.

#### Scenario: Loading sitl_default field profile succeeds
- **WHEN** `load_field_profile("sitl_default")` is called
- **THEN** a valid `FieldProfile` object is returned without raising `ConfigError` or `ValidationError`

#### Scenario: SITL field profile passes geographic validation
- **WHEN** the sitl_default field.json is validated
- **THEN** all scan waypoints, landing approach, touchdown point, and loiter point are inside the geofence boundary polygon

#### Scenario: Field profile contains required sections
- **WHEN** `data/fields/sitl_default/field.json` is parsed
- **THEN** it contains `name`, `boundary` (with `polygon`), `landing` (with `approach_waypoint` and `touchdown_point`), `scan_waypoints` (with `waypoints` and `altitude_m`), `loiter_point`, and `safety_buffer_m`
