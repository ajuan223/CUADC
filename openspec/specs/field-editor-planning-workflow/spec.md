# field-editor-planning-workflow Specification

## Purpose
TBD - created by archiving change r3-field-editor-map-selector-fixes. Update Purpose after archive.
## Requirements
### Requirement: Field editor planning workflow SHALL expose runtime-relevant derived geometry during editing
The field editor MUST derive and display planning outputs during editing so operators can validate runway, approach, takeoff, loiter, and scan setup before exporting `field.json`.

#### Scenario: Landing approach preview is available
- **WHEN** the field profile contains a valid boundary, touchdown point, glide slope, and approach altitude
- **THEN** the editor MUST display the derived approach point, approach altitude, and approach distance in the planning summary

#### Scenario: Takeoff/climb preview is available
- **WHEN** the field profile contains a valid runway heading, runway length, touchdown altitude, and scan altitude
- **THEN** the editor MUST display the derived takeoff direction and climbout preview derived from the same runway facts

#### Scenario: Scan preview summary is available
- **WHEN** the boundary and scan spacing are valid
- **THEN** the editor MUST display a scan preview summary including at least the generated pass count or waypoint count

### Requirement: Field editor SHALL surface advisory safety warnings for unsafe geometry
The field editor MUST show explicit advisory warnings when the edited geometry implies unsafe descent or climb characteristics.

#### Scenario: Descent geometry is unsafe
- **WHEN** the configured landing glide slope or derived approach geometry exceeds the editor's unsafe descent threshold
- **THEN** the editor MUST add an advisory warning that the descent setup is unsafe

#### Scenario: Climb geometry is unsafe
- **WHEN** the configured takeoff runway length and target climb altitude imply a climb angle above the editor's unsafe climb threshold
- **THEN** the editor MUST add an advisory warning that the climb setup is unsafe

