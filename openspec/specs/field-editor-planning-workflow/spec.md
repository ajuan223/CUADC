# field-editor-planning-workflow Specification

## Purpose

Define the planning-time geometry, warnings, and export behavior the field editor must expose so operators can validate runway, scan, and attack-run setup before runtime.
## Requirements
### Requirement: Field editor planning workflow SHALL expose runtime-relevant derived geometry during editing
The field editor MUST derive and display planning outputs during editing so operators can validate runway, approach, takeoff, and scan setup before exporting `field.json`, and this planning workflow MUST live inside the planning tab rather than sharing a mixed control surface with replay controls.

#### Scenario: Landing approach preview is available
- **WHEN** the field profile contains a valid boundary, touchdown point, glide slope, and approach altitude inside the planning tab
- **THEN** the editor MUST display the derived approach point, approach altitude, and approach distance in the planning summary

#### Scenario: Takeoff/climb preview is available
- **WHEN** the field profile contains a valid runway heading, runway length, touchdown altitude, and scan altitude inside the planning tab
- **THEN** the editor MUST display the derived takeoff direction and climbout preview derived from the same runway facts

#### Scenario: Scan preview summary is available
- **WHEN** the boundary and scan spacing are valid in the planning tab
- **THEN** the editor MUST display a scan preview summary including at least the generated pass count or waypoint count

#### Scenario: Exported field profile excludes loiter input
- **WHEN** the operator exports a field profile for the current standard mission flow from the planning tab
- **THEN** the exported payload MUST not include `loiter_point`

### Requirement: Field editor SHALL surface advisory safety warnings for unsafe geometry
The field editor MUST show explicit advisory warnings when the edited geometry implies unsafe descent or climb characteristics, and those warnings MUST remain part of the planning tab workflow.

#### Scenario: Descent geometry is unsafe
- **WHEN** the configured landing glide slope or derived approach geometry exceeds the editor's unsafe descent threshold in the planning tab
- **THEN** the editor MUST add an advisory warning that the descent setup is unsafe

#### Scenario: Climb geometry is unsafe
- **WHEN** the configured takeoff runway length and target climb altitude imply a climb angle above the editor's unsafe climb threshold in the planning tab
- **THEN** the editor MUST add an advisory warning that the climb setup is unsafe

### Requirement: Field editor planning workflow SHALL expose scan boundary margin editing
The field editor MUST allow operators to inspect and edit `scan.boundary_margin_m` as part of the planning workflow, and this editing capability MUST remain in the planning tab after replay is separated.

#### Scenario: Boundary margin is editable in planning UI
- **WHEN** an operator edits scan planning parameters in the planning tab
- **THEN** the workflow MUST expose `scan.boundary_margin_m`
- **AND** the exported field profile MUST preserve the configured value

### Requirement: Field editor planning workflow SHALL expose fallback drop point and attack preview
The field editor MUST allow operators to place `attack_run.fallback_drop_point` and see the derived attack approach/exit preview associated with that fallback point, and this interaction MUST remain part of the planning tab rather than the replay tab.

#### Scenario: Fallback drop point is visible and exportable
- **WHEN** an operator sets a fallback drop point in the planning tab
- **THEN** the editor MUST display the point and derived attack-run preview
- **AND** the exported field profile MUST include the configured fallback drop point
