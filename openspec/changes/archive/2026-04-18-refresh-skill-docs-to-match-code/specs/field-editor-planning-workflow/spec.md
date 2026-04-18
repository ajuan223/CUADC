## ADDED Requirements

### Requirement: Field editor planning workflow SHALL expose scan boundary margin editing
The field editor MUST allow operators to inspect and edit `scan.boundary_margin_m` as part of the planning workflow, so scan preview and exported field data remain consistent with runtime mission geometry.

#### Scenario: Boundary margin is editable in planning UI
- **WHEN** an operator edits scan planning parameters in the field editor
- **THEN** the workflow MUST expose `scan.boundary_margin_m`
- **AND** the exported field profile MUST preserve the configured value

### Requirement: Field editor planning workflow SHALL expose fallback drop point and attack preview
The field editor MUST allow operators to place `attack_run.fallback_drop_point` and see the derived attack approach/exit preview associated with that fallback point.

#### Scenario: Fallback drop point is visible and exportable
- **WHEN** an operator sets a fallback drop point in the field editor
- **THEN** the editor MUST display the point and derived attack-run preview
- **AND** the exported field profile MUST include the configured fallback drop point
