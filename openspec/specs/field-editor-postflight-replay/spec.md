## Requirements

### Requirement: Field Editor MUST support post-flight trajectory replay from historical flight logs
The system MUST allow an operator to load a historical `flight_log` into Field Editor and replay the recorded aircraft trajectory on the map without requiring a live telemetry connection, and this workflow MUST be entered through a dedicated replay tab rather than embedded directly in the planning form area.

#### Scenario: Operator loads a historical flight log
- **WHEN** the operator opens the replay tab and selects a valid historical `flight_log` for a completed mission
- **THEN** Field Editor MUST parse the recorded samples and render the full aircraft trajectory on the map
- **AND** the replay workflow MUST not require a live MAVLink or Web telemetry session

#### Scenario: Operator inspects current replay position
- **WHEN** the replay tab timeline is positioned at a specific recorded sample
- **THEN** Field Editor MUST display the aircraft position corresponding to that sample on the map
- **AND** the displayed position MUST move as the replay timeline advances

### Requirement: Field Editor MUST provide basic replay controls for post-flight analysis
The system MUST provide replay controls sufficient for post-flight inspection, including play, pause, progress seeking, playback speed selection, and fitting the map view to the replayed trajectory, and these controls MUST reside in the replay tab.

#### Scenario: Operator plays and pauses replay
- **WHEN** the operator starts or pauses replay from the replay tab
- **THEN** Field Editor MUST advance or stop the replay cursor accordingly

#### Scenario: Operator seeks within replay timeline
- **WHEN** the operator drags the replay progress control in the replay tab to a different point in the mission
- **THEN** Field Editor MUST update the displayed aircraft position and map overlays to the selected recorded sample

#### Scenario: Operator adjusts replay speed
- **WHEN** the operator selects a supported playback speed in the replay tab
- **THEN** Field Editor MUST advance the replay according to that multiplier relative to recorded sample order

#### Scenario: Operator fits trajectory into view
- **WHEN** the operator requests a trajectory fit action from the replay tab
- **THEN** Field Editor MUST adjust the map viewport to contain the replayed flight path

### Requirement: Field Editor MUST overlay post-flight replay with planning geometry and drop results
The system MUST display replay data together with planning-time field geometry so operators can compare actual flight behavior and drop outcomes against the configured field profile, but the entry point for this comparison MUST remain the replay tab.

#### Scenario: Replay shows planning geometry
- **WHEN** a replay is opened in the replay tab for a field profile with boundary, runway, scan preview, or attack-run preview
- **THEN** Field Editor MUST render those planning overlays together with the replay trajectory

#### Scenario: Replay shows planned and actual drop points
- **WHEN** the loaded replay data in the replay tab contains planned drop context and an actual drop result
- **THEN** Field Editor MUST display both the planned drop point reference and the actual drop point on the map

#### Scenario: Replay without actual drop result remains viewable
- **WHEN** the loaded replay data in the replay tab does not contain a confirmed actual drop point
- **THEN** Field Editor MUST still allow trajectory replay
- **AND** the UI MUST indicate that the actual drop result is unavailable rather than failing the replay flow

### Requirement: Field Editor MUST remain a post-flight analysis tool rather than a live ground-station view
The system MUST scope this capability to historical replay and MUST NOT require or imply real-time aircraft position streaming as part of this change.

#### Scenario: Operator enters replay mode
- **WHEN** the operator uses the replay tab capability
- **THEN** the workflow MUST operate on historical mission data
- **AND** the workflow MUST NOT depend on a live telemetry stream
