## ADDED Requirements

### Requirement: Closed-loop run artifact retention SHALL preserve every optimization round without overwrite
The optimization workflow MUST preserve the raw stack artifacts and a stable copied flight-log filename for each `zjg` tuning round.

#### Scenario: Optimization round stores raw and copied artifacts
- **WHEN** an optimization round starts for `zjg`
- **THEN** the workflow MUST preserve the raw integration-run directory under a round-specific archive location
- **AND** it MUST copy the round's flight log into a stable monotonic filename such as `log_1.csv`, `log_2.csv`, or later round numbers without overwriting prior logs

#### Scenario: Later rounds do not overwrite earlier evidence
- **WHEN** a new optimization round is preserved after earlier rounds already exist
- **THEN** the workflow MUST allocate the next monotonic round number
- **AND** it MUST keep all earlier raw runs, copied logs, and derived artifacts intact

### Requirement: Closed-loop run artifact retention SHALL preserve operator-meaningful iteration history
Each preserved optimization round MUST include the analysis artifact that explains what changed and how the run behaved.

#### Scenario: Analysis artifact is stored with the round
- **WHEN** a round analysis is written after a preserved `zjg` run
- **THEN** it MUST be saved alongside the raw run directory and copied flight log using a stable filename such as `flight_log_analysis_1.md`
