## MODIFIED Requirements

### Requirement: Field editor planning workflow SHALL expose runtime-relevant derived geometry during editing
The field editor MUST derive and display planning outputs during editing so operators can validate runway, approach, takeoff, and scan setup before exporting `field.json`.

#### Scenario: Landing approach preview is available
- **WHEN** the field profile contains a valid boundary, touchdown point, glide slope, and approach altitude
- **THEN** the editor MUST display the derived approach point, approach altitude, and approach distance in the planning summary

#### Scenario: Takeoff/climb preview is available
- **WHEN** the field profile contains a valid runway heading, runway length, touchdown altitude, and scan altitude
- **THEN** the editor MUST display the derived takeoff direction and climbout preview derived from the same runway facts

#### Scenario: Scan preview summary is available
- **WHEN** the boundary and scan spacing are valid
- **THEN** the editor MUST display a scan preview summary including at least the generated pass count or waypoint count

#### Scenario: Exported field profile excludes loiter input
- **WHEN** the operator exports a field profile for the current standard mission flow
- **THEN** the exported payload MUST not include `loiter_point`
