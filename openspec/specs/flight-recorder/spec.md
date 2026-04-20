# flight-recorder

## Requirements

- REQ-REC-001: CSV recording with configurable fields, and the default recorder output for post-flight analysis includes release-event and drop-result columns alongside the existing telemetry columns
- REQ-REC-002: Configurable sample rate via settings
- REQ-REC-003: async run() coroutine writing periodic telemetry snapshots
- REQ-REC-004: Auto-flush on shutdown
- REQ-REC-005: Output directory from settings (default: runtime_data/)
- REQ-REC-006: GCS reporter interface (reserved, not implemented)

### Requirement: Flight recorder MUST persist release timing within the main flight log
The system MUST persist release timing information inside the main `flight_log` CSV instead of requiring a separate release-event log.

#### Scenario: Release event becomes observable in flight log
- **WHEN** the mission triggers payload release successfully
- **THEN** the recorder MUST write flight-log rows that mark release as triggered
- **AND** the flight log MUST contain a release timestamp value that can be used to identify the release moment during replay

#### Scenario: Flight without release keeps release fields empty or false
- **WHEN** a mission completes without a successful payload release
- **THEN** the recorder MUST preserve the flight log structure
- **AND** release-related fields MUST remain empty or false rather than fabricating a release event

### Requirement: Flight recorder MUST persist post-flight drop-result fields in the main flight log
The system MUST persist the mission's available actual drop-result fields inside the main `flight_log` CSV so replay consumers can read a single file.

#### Scenario: Vision-confirmed drop result appears in flight log
- **WHEN** the mission confirms an actual drop point from vision or another runtime source
- **THEN** subsequent flight-log rows MUST include the actual drop latitude and longitude
- **AND** the flight log MUST annotate the source of that drop result

#### Scenario: Drop result is unavailable during mission
- **WHEN** no actual drop point is confirmed before logging stops
- **THEN** the flight log MUST still be written successfully
- **AND** actual-drop fields MUST remain empty rather than blocking recording
