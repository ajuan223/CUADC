# sitl-stack-debug-workflow Specification

## Purpose
TBD - created by archiving change r4-sitl-mavproxy-striker-fullchain-debug. Update Purpose after archive.
## Requirements
### Requirement: SITL stack debug workflow SHALL classify failures by stack layer before applying repairs
The debug workflow MUST distinguish stack bring-up failures from transport, mission-upload, mission-progression, and landing/release failures so the repair path matches the actual fault.

#### Scenario: A failing run is classified before retry
- **WHEN** a project-venv SITL validation run fails
- **THEN** the workflow MUST classify the failure into at least one of these layers: process bring-up, MAVLink routing, mission upload, mission progression, release, landing, or override handover
- **AND** it MUST use that classification to choose the next diagnostic step instead of retrying the same command blindly

### Requirement: SITL stack debug workflow SHALL check the validated launch invariants first
The first diagnostic pass MUST verify the launch assumptions already known to be required by this repository’s successful SITL runs.

#### Scenario: Launch invariant check catches common misconfiguration
- **WHEN** the full-chain stack does not come up cleanly
- **THEN** the workflow MUST check the ArduPlane binary path, the `Tools/autotest/models/plane.parm` path, the field-specific `sitl_merged.param`, the explicit Zijingang home position, the repo-local MAVProxy executable, and Striker UDP transport configuration before deeper mission debugging continues

### Requirement: SITL stack debug workflow SHALL preserve diagnostic evidence for each repair attempt
The debug workflow MUST keep the evidence from each validation attempt so behavior changes can be compared across fixes.

#### Scenario: Repair attempt retains evidence
- **WHEN** the workflow reruns the stack after a code or launch adjustment
- **THEN** the new attempt MUST preserve its own log and recorder artifacts separately from prior attempts
- **AND** it MUST leave enough evidence to compare whether the failure mode changed, progressed, or cleared

