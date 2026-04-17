## ADDED Requirements

### Requirement: Iterative flight-log analysis SHALL be persisted for every optimization round
Every preserved optimization round MUST produce a durable markdown analysis artifact rather than relying on terminal-only inspection.

#### Scenario: First optimization round produces analysis markdown
- **WHEN** the first full `zjg` closed-loop optimization run completes
- **THEN** the workflow MUST write `flight_log_analysis_1.md`
- **AND** later rounds MUST continue with monotonically increasing analysis filenames

### Requirement: Iterative flight-log analysis SHALL correlate recorder output with stack logs
Round analysis MUST use preserved recorder output together with mission-phase logs so takeoff, route tracking, strike, and landing behavior can be judged from durable evidence.

#### Scenario: Analysis cites both recorder and mission milestones
- **WHEN** a preserved round is analyzed
- **THEN** the analysis MUST summarize recorder-derived telemetry
- **AND** it MUST correlate that telemetry with mission milestones and stack logs before recommending the next bounded tuning step
