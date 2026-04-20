## ADDED Requirements

### Requirement: Takeoff path visualization
The field editor SHALL render a polyline from takeoff start point to climbout point when `derivedTakeoff` is available. The line SHALL use a distinct color from scan and landing paths.

#### Scenario: Takeoff path displayed when takeoff geometry is valid
- **WHEN** `derivedTakeoff` is computed and has valid coordinates
- **THEN** a polyline is drawn from `(start_lat, start_lon)` to `(climbout_lat, climbout_lon)`

#### Scenario: Takeoff path hidden when geometry is unavailable
- **WHEN** `derivedTakeoff` is null due to validation errors
- **THEN** no takeoff path overlay is rendered

### Requirement: Inter-segment connection lines
The field editor SHALL render dashed gray polylines connecting sequential flight phases: climbout → first scan waypoint, and last scan waypoint → landing approach point.

#### Scenario: Chain lines drawn when all phases are present
- **WHEN** `derivedTakeoff`, scan preview, and `derivedApproach` are all available
- **THEN** two dashed gray lines are drawn: climbout → scan[0] and scan[last] → approach

#### Scenario: Chain lines degrade gracefully
- **WHEN** scan preview is empty but takeoff and approach exist
- **THEN** a single dashed line is drawn from climbout to approach point

#### Scenario: Chain lines hidden when insufficient data
- **WHEN** takeoff or approach geometry is missing
- **THEN** no chain lines are rendered

### Requirement: Attack run preview label
The attack run approach/exit lines SHALL include a visual indicator that the displayed path is a static preview based on fallback drop point, not the actual dynamic flight path.

#### Scenario: Preview label visible on attack run
- **WHEN** a fallback drop point is configured and attack lines are displayed
- **THEN** the drop point marker label includes "(预览)" to indicate static preview

#### Scenario: No attack run when no drop point
- **WHEN** no fallback drop point is configured
- **THEN** no attack run overlays are rendered (existing behavior preserved)
