## ADDED Requirements

### Requirement: SITL default field configuration file exists
The system SHALL provide a valid field profile JSON file at `data/fields/sitl_default/field.json` that can be loaded by `load_field_profile("sitl_default")`.

#### Scenario: Loading sitl_default field profile succeeds
- **WHEN** `load_field_profile("sitl_default")` is called
- **THEN** a valid `FieldProfile` object is returned without raising `ConfigError` or `ValidationError`

#### Scenario: SITL field profile passes geographic validation
- **WHEN** the sitl_default field.json is validated
- **THEN** the derived landing approach and touchdown point are inside the geofence boundary polygon
- **AND** the scan and attack-run sections are sufficient for procedural mission generation

#### Scenario: Field profile contains required sections
- **WHEN** `data/fields/sitl_default/field.json` is parsed
- **THEN** it contains `name`, `boundary` (with `polygon`), `landing` (with `touchdown_point`), `scan` (with `altitude_m`, `spacing_m`, and `heading_deg`), `attack_run`, and `safety_buffer_m`
