## Why

The project still lacks a reliable, repo-local way to run the full SITL → MAVProxy → Striker validation chain from the project venv and debug failures until the strike mission closes the loop successfully. Without that workflow, regressions in takeoff, scan, strike/release, or landing remain hard to reproduce and the autonomous mission path cannot be trusted end-to-end.

## What Changes

- Define a project-venv-based full-chain validation workflow that launches SITL, MAVProxy, and Striker from the repository’s own Python environment instead of relying on ad-hoc system Python setups.
- Establish a debug-first process for bringing up the complete simulation stack, identifying blocking faults, and iterating until the chain is stable.
- Define end-to-end validation requirements for the full strike loop: startup, MAVLink connection, takeoff, scan, strike/release, landing, and clean mission completion.
- Capture required observability and pass/fail signals so failures in SITL startup, MAVProxy routing, mission progression, release behavior, or landing can be diagnosed consistently.
- Require regression coverage or repeatable validation artifacts so the closed-loop flow can be rerun after fixes.

## Capabilities

### New Capabilities
- `project-venv-sitl-stack`: Running the full SITL, MAVProxy, and Striker stack from the project’s internal venv with documented launch, environment, and dependency expectations.
- `strike-fullchain-validation`: Repeatable validation of the closed-loop autonomous mission from startup through takeoff, scan, strike/release, landing, and successful completion.
- `sitl-stack-debug-workflow`: Structured diagnosis of full-chain simulation failures, including stack bring-up, transport wiring, mission-state progression, and closure criteria.

### Modified Capabilities
<!-- none -->

## Impact

- Affected areas: project venv invocation scripts or commands, SITL/MAVProxy/Striker integration workflow, and validation/test assets around full-mission execution
- External systems: ArduPlane SITL, MAVProxy routing, and MAVLink transport configuration used by Striker
- Operator/developer impact: the team gets a consistent way to debug and verify that the strike mission can complete takeoff → scan → release → landing end-to-end before field use
