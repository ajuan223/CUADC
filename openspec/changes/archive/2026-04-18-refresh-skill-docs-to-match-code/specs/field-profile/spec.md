## ADDED Requirements

### Requirement: ScanConfig SHALL include boundary margin
`ScanConfig` SHALL include `boundary_margin_m` as a field-profile-owned scan geometry parameter. Mission geometry generation and field-editor export/import MUST source scan boundary margin from the field profile rather than a detached global setting.

#### Scenario: Field profile owns scan boundary margin
- **WHEN** a field profile is loaded or exported with scan settings
- **THEN** `scan.boundary_margin_m` MUST be part of the field data model
- **AND** scan geometry generation MUST consume that field-owned value

### Requirement: AttackRunConfig SHALL support fallback drop point
`AttackRunConfig` SHALL allow an optional `fallback_drop_point` geographic coordinate so scan completion can fall back to an explicit field-defined release point when vision data is absent.

#### Scenario: Field profile preserves fallback drop point
- **WHEN** a field JSON contains `attack_run.fallback_drop_point`
- **THEN** `load_field_profile()` MUST expose it on `FieldProfile.attack_run.fallback_drop_point`
- **AND** export/import flows MUST preserve the coordinate
