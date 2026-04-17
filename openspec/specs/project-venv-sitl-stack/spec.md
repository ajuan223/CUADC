# project-venv-sitl-stack Specification

## Purpose
TBD - created by archiving change r4-sitl-mavproxy-striker-fullchain-debug. Update Purpose after archive.
## Requirements
### Requirement: Project-venv SITL stack SHALL use the validated raw ArduPlane → MAVProxy → Striker topology
The project MUST provide a repeatable launch workflow that starts ArduPlane SITL from the local ArduPilot checkout, routes MAVLink through MAVProxy installed in the repository `.venv`, and starts Striker from the project environment against the validated SITL field.

#### Scenario: Stack launch uses validated commands and topology
- **WHEN** an operator or integration harness starts the project-venv SITL stack for `sitl_default`
- **THEN** the workflow MUST launch the raw `arduplane` SITL binary with `--home 30.2610,120.0950,0,180`
- **AND** it MUST load both `data/fields/sitl_default/sitl_merged.param` and `~/ardupilot/Tools/autotest/models/plane.parm`
- **AND** it MUST launch MAVProxy from the repository `.venv` with TCP input `127.0.0.1:5760` and UDP outputs `14550` and `14551`
- **AND** it MUST launch Striker from the project environment with UDP transport against that routed MAVLink stream

### Requirement: Project-venv SITL stack SHALL fail fast when prerequisites are missing or inconsistent
The launch workflow MUST validate required local prerequisites before waiting on mission-level timeouts.

#### Scenario: Missing local dependency is reported directly
- **WHEN** the ArduPlane SITL binary, repo-local `mavproxy.py`, field parameter file, or ArduPilot `plane.parm` path is missing
- **THEN** the stack workflow MUST stop before mission startup
- **AND** it MUST report which prerequisite is missing or invalid

#### Scenario: Incorrect field home is rejected
- **WHEN** the launch workflow is asked to start the `sitl_default` stack without the validated home position near the field touchdown point
- **THEN** the workflow MUST refuse to treat the run as valid for full-chain mission verification
- **AND** it MUST surface that the field home configuration is inconsistent with the tested map geometry

### Requirement: Project-venv SITL stack SHALL expose transport health before mission validation begins
The workflow MUST make transport-layer readiness observable before higher-level mission assertions run.

#### Scenario: Bring-up health passes before mission execution
- **WHEN** the stack starts successfully
- **THEN** the validation workflow MUST confirm that ArduPlane is listening on the expected upstream endpoint
- **AND** it MUST confirm that MAVProxy is producing the expected UDP outputs
- **AND** it MUST confirm that Striker can establish MAVLink connectivity before mission-state assertions begin

