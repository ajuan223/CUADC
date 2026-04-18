## ADDED Requirements

### Requirement: run_sitl.sh SHALL launch the full local debug stack
`scripts/run_sitl.sh` SHALL be documented and specified as a local debug launcher that starts ArduPlane SITL, MAVProxy, and the repository's Striker process in one flow for the selected field.

#### Scenario: Launcher responsibilities include Striker
- **WHEN** `scripts/run_sitl.sh <field>` is used for the local debug workflow
- **THEN** it MUST be treated as responsible for launching SITL, MAVProxy, and Striker
- **AND** documentation and Skills MUST NOT describe it as a SITL-only launcher if it starts the full chain

### Requirement: run_sitl.sh SHALL emit artifact paths for the active run
The local SITL launcher SHALL expose the active run's MAVProxy log path, flight-log target path, artifact directory, and Striker log path so downstream analysis workflows can consume them without manual path discovery.

#### Scenario: Launcher surfaces per-run artifacts
- **WHEN** the local debug launcher starts a new run
- **THEN** it MUST print the generated artifact/log targets for that run
- **AND** Skill guidance for SITL debugging MUST follow those emitted paths
