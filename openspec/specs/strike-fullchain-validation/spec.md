# strike-fullchain-validation Specification

## Purpose
TBD - created by archiving change r4-sitl-mavproxy-striker-fullchain-debug. Update Purpose after archive.
## Requirements
### Requirement: Strike full-chain validation SHALL cover iterative optimization rounds on the selected field profile
The project MUST provide runnable validation for the full SITL mission chain from startup through mission completion, and it MUST support repeated optimization rounds on the selected field profile rather than only a one-off `sitl_default` validation.

#### Scenario: Normal strike path completes end-to-end on the optimization field
- **WHEN** the validated SITL stack is available and a full-chain optimization validation runs for `zjg`
- **THEN** the run MUST assert successful startup and mission upload
- **AND** it MUST verify the ordered mission progression through `preflight`, `takeoff`, `scan`, `enroute`, `release`, and `landing`
- **AND** it MUST verify that the run reaches its intended terminal outcome with preserved artifacts for later round-to-round comparison
- **AND** the temporary attack mission used for the strike handoff MUST be allowed to use a software-controlled altitude that better matches the derived landing approach when the optimization loop is explicitly reducing landing-window energy

#### Scenario: Missing optimization-field SITL prerequisites stop the round with an actionable reason
- **WHEN** the required local SITL stack prerequisites for the selected optimization field are unavailable or incompatible in a development environment
- **THEN** the full-chain optimization validation MUST stop rather than fail ambiguously
- **AND** it MUST report which prerequisite prevented a meaningful `zjg` run, such as missing merged params, mismatched home configuration, or incompatible field-coordinate data

### Requirement: Strike full-chain validation SHALL preserve mission-progress observability needed by the state machine
The full-chain workflow MUST explicitly preserve the mission-progress signals that Striker uses to advance from scan to attack and landing phases.

#### Scenario: Validation requests mission-progress messages after link startup
- **WHEN** the validated SITL stack connects through MAVProxy and starts the autonomous chain
- **THEN** the workflow MUST explicitly request the `MISSION_CURRENT` and `MISSION_ITEM_REACHED` messages needed by the mission state machine
- **AND** it MUST not rely solely on the transport's default message stream to decide whether scan or attack progression is happening

## REMOVED Requirements

### Requirement: Strike full-chain validation SHALL reject stale mission-progress readings after mission replacement
**Reason**: Mission replacement and temporary attack missions have been eliminated. There is no longer a need to sync mission sequence progress across dynamic uploads.
**Migration**: Validation runs naturally test the continuous preburned mission + GUIDED takeover.

#### Scenario: Fallback strike path remains isolated from stale vision publishers
- **WHEN** the fallback full-chain validation runs without a resolved vision drop point
- **THEN** the harness MUST isolate that run from mock-vision publishers left over from prior validations
- **AND** it MUST prevent a stale external vision client from reconnecting and converting the fallback scenario into the vision path


### Requirement: Strike full-chain validation SHALL preserve runtime budgets consistent with the validated mission duration
The full-chain workflow MUST use timeout budgets that reflect the observed end-to-end mission duration of the validated SITL stack, rather than stale shorter cutoffs inherited from earlier placeholder coverage.

#### Scenario: Normal strike path uses a budget large enough for the validated `sitl_default` chain
- **WHEN** the guarded normal-path validation runs against the current `sitl_default` stack
- **THEN** the shared full-chain timeout budget MUST be at least as large as the longest preserved green run needed to reach `Mission completed successfully!`
- **AND** normal-path assertions SHOULD inherit that shared budget instead of overriding it with a second divergent timeout value

### Requirement: Strike full-chain validation SHALL preserve per-run observability artifacts
Each validation run MUST preserve the evidence needed to debug launch, mission-progression, and landing failures.

#### Scenario: Run artifacts are written to a dedicated output location
- **WHEN** a full-chain validation run starts
- **THEN** the workflow MUST write the SITL log, MAVProxy log, Striker log, and flight-recorder CSV to a run-specific artifact location
- **AND** it MUST avoid overwriting artifacts from a previous validation run in the same workflow

### Requirement: Strike full-chain validation SHALL cover fallback and override mission paths
The validation workflow MUST exercise the non-happy-path scenarios already represented in the integration test surface.

#### Scenario: Fallback strike path completes without a vision target
- **WHEN** the full-chain validation runs without a resolved vision drop point
- **THEN** the workflow MUST verify that Striker follows the fallback attack path and still reaches release and landing milestones

#### Scenario: Human override interrupts the autonomous chain
- **WHEN** the operator or test harness injects the override condition during the full-chain mission
- **THEN** the validation MUST verify that autonomous progression stops
- **AND** it MUST verify that the run reports the override handover outcome explicitly
- **AND** it MUST preserve the per-run flight recorder artifact even when override terminates the mission before a normal completion path
