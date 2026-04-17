# field-editor-coordinate-consistency Specification

## Purpose
TBD - created by archiving change r3-field-editor-map-selector-fixes. Update Purpose after archive.
## Requirements
### Requirement: Field editor import/export SHALL respect declared coordinate systems
The field editor MUST honor the source `coordinate_system` when importing a field file so repeated edits do not introduce a systematic coordinate offset.

#### Scenario: Importing WGS84 field data
- **WHEN** the imported field file declares `coordinate_system` as `WGS84`
- **THEN** the editor MUST convert those coordinates into internal GCJ-02 map coordinates for display and interaction

#### Scenario: Importing GCJ-02 field data
- **WHEN** the imported field file declares `coordinate_system` as `GCJ-02`
- **THEN** the editor MUST preserve those coordinates for internal map editing instead of applying an additional WGS84-to-GCJ conversion

#### Scenario: Exporting edited field data
- **WHEN** the operator exports a field profile from the editor
- **THEN** the output `field.json` MUST be normalized to `WGS84` coordinates for runtime consumption

