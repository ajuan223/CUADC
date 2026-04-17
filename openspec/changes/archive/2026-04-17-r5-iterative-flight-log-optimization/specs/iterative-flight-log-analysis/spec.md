## ADDED Requirements

### Requirement: Iterative flight-log analysis SHALL be persisted for every optimization round
The system MUST preserve a written analysis artifact for each closed-loop optimization round instead of keeping conclusions only in transient terminal output.

#### Scenario: First optimization round writes an analysis artifact
- **WHEN** the first full `zjg` closed-loop optimization run completes
- **THEN** the workflow MUST write `flight_log_analysis_1.md`
- **AND** that file MUST summarize the observed takeoff, route-tracking, strike, and landing behavior from the preserved run evidence
- **AND** it MUST record at least one bounded software-side hypothesis for the next round

#### Scenario: Later rounds append with monotonic numbering
- **WHEN** subsequent optimization rounds complete
- **THEN** the workflow MUST write `flight_log_analysis_2.md`, `flight_log_analysis_3.md`, and so on without overwriting earlier analyses
- **AND** each analysis MUST be attributable to exactly one preserved run directory and copied flight log

### Requirement: Iterative flight-log analysis SHALL correlate recorder output with stack logs
The analysis workflow MUST use preserved `flight_log.csv` together with Striker/SITL/MAVProxy evidence so behavioral conclusions are grounded in mission phase context rather than raw coordinates alone.

#### Scenario: Analysis explains a mission-phase behavior with preserved evidence
- **WHEN** a round exhibits unstable, unsafe, or otherwise undesirable flight behavior
- **THEN** the analysis MUST cite the relevant mission phase or milestone from preserved logs
- **AND** it MUST connect that observation to the corresponding segment of the preserved flight log before proposing a software-side change

#### Scenario: Analysis reports terminal landing telemetry from preserved recorder fields
- **WHEN** a preserved round reaches late landing or touchdown monitoring
- **THEN** the written analysis MUST summarize a bounded terminal telemetry window from the preserved flight log using already-recorded fields such as relative altitude, airspeed, groundspeed, attitude, mode, and armed state
- **AND** it MUST make clear that this terminal telemetry window is the preferred landing-quality evidence when the final CSV row is captured shortly before shutdown rather than after the aircraft has settled on the ground
