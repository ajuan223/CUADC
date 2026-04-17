## ADDED Requirements

### Requirement: Closed-loop run artifact retention SHALL preserve every optimization round without overwrite
The optimization workflow MUST preserve the raw stack artifacts and a stable copied flight-log filename for each `zjg` tuning round.

#### Scenario: Round artifacts are written to a dedicated non-overwriting location
- **WHEN** an optimization round starts for `zjg`
- **THEN** the workflow MUST create a dedicated round artifact directory under `runtime_data/`
- **AND** that directory MUST preserve the run's `sitl.log`, `mavproxy.log`, `striker.log`, and `flight_log.csv`
- **AND** it MUST also preserve a copied round-scoped flight log named `log_1.csv`, `log_2.csv`, `log_3.csv`, and so on without overwriting prior rounds

#### Scenario: Analysis artifact stays colocated with the preserved round evidence
- **WHEN** a round analysis is written
- **THEN** the corresponding `flight_log_analysis_N.md` MUST be stored with or directly adjacent to the preserved round evidence for the same iteration
- **AND** the workflow MUST make it unambiguous which copied log and raw run directory belong to that analysis

### Requirement: Closed-loop run artifact retention SHALL preserve operator-meaningful iteration history
The optimization workflow MUST keep a durable, human-readable ordering of rounds so the user can compare behavior across tuning iterations.

#### Scenario: Reviewing multiple rounds shows chronological progression
- **WHEN** at least three optimization rounds have been run
- **THEN** the retained artifacts MUST expose a monotonic round order
- **AND** a developer MUST be able to inspect round 1, round 2, and round 3 without relying on overwritten default filenames or shell history
