## ADDED Requirements

### Requirement: Field Editor MUST expose top-level planning and replay tabs
The system MUST present planning and replay as two distinct top-level tabs or equivalent mode selectors so operators do not perform post-flight replay inside the planning form flow.

#### Scenario: Operator opens the editor
- **WHEN** the Field Editor page loads
- **THEN** the UI MUST expose separate top-level entries for planning and replay
- **AND** one of them MUST be clearly active

### Requirement: Field Editor tab switching MUST preserve the shared workspace shell
The system MUST keep a consistent overall workspace layout when switching between planning and replay, while changing the sidebar content to match the selected workflow.

#### Scenario: Operator switches from planning to replay
- **WHEN** the operator activates the replay tab
- **THEN** the page MUST keep the same overall map-centered workspace shell
- **AND** the sidebar MUST switch from planning controls to replay controls without navigating to a different page

#### Scenario: Operator switches back to planning
- **WHEN** the operator returns to the planning tab
- **THEN** the planning controls MUST become available again
- **AND** the replay-specific controls MUST no longer occupy the planning workflow area
