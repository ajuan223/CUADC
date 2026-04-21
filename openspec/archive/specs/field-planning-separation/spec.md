## ADDED Requirements

### Requirement: Independent management of planning fields
The Field Editor SHALL manage planning-only configuration parameters (such as `scan.spacing_m`, `scan.heading_deg`, `scan.boundary_margin_m`, `landing.glide_slope_deg`, `landing.approach_alt_m`, `landing.runway_length_m`, and `landing.use_do_land_start`) independently from the runtime `field.json` payload.

#### Scenario: Exporting a planning bundle
- **WHEN** the user finalizes planning parameters in the Field Editor
- **THEN** the Field Editor MUST NOT include these planning fields in the generated `field.json`
- **AND** the Field Editor MAY export them into a separate `planning.json` bundle to preserve reproducibility

### Requirement: Removal of ghost fields from runtime context
The Striker `FieldProfile` payload SHALL strictly represent the runtime and shared parameters. Any attempt to supply planning fields into `load_field_profile()` via legacy JSON configurations SHOULD be explicitly ignored or trigger validation errors.

#### Scenario: Legacy JSON consumption
- **WHEN** an older `field.json` containing `scan.spacing_m` is loaded by Striker
- **THEN** Striker MUST NOT parse or retain `scan.spacing_m` in its `FieldProfile` representation
