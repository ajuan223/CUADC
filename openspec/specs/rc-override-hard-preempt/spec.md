# rc-override-hard-preempt Specification

## Purpose
TBD - created by archiving change r2-rc-override-hard-preempt. Update Purpose after archive.
## Requirements
### Requirement: Manual takeover MUST permanently preempt autonomy for the current run
The system MUST treat detected RC/manual takeover as the highest-priority authority and permanently relinquish autonomous control for the remainder of the run.

#### Scenario: Manual mode takeover is detected
- **WHEN** the vehicle flight mode changes into a configured manual takeover mode such as `MANUAL`, `STABILIZE`, or `FBWA`
- **THEN** the system MUST mark autonomous control as relinquished and MUST NOT re-enable it automatically during the same run

#### Scenario: Override event reaches the FSM
- **WHEN** an `OverrideEvent` is processed by the mission state machine
- **THEN** the FSM MUST transition to the terminal `override` state and autonomous control MUST remain disabled

### Requirement: Autonomous command paths MUST fail closed after override
After autonomy has been relinquished, the system MUST reject autonomous outbound command attempts instead of sending them to the flight controller.

#### Scenario: Flight controller command attempted after override
- **WHEN** any flight-control command path attempts to arm, change mode, upload navigation targets, or send a mission-control command after autonomy is disabled
- **THEN** the command MUST be blocked and MUST NOT be sent to MAVLink

#### Scenario: Mission upload attempted after override
- **WHEN** a mission upload path attempts to clear, count, or send mission items after autonomy is disabled
- **THEN** the upload MUST fail before sending mission-control traffic

#### Scenario: Payload release attempted after override
- **WHEN** a payload release path attempts to emit `DO_SET_SERVO` or equivalent release commands after autonomy is disabled
- **THEN** the release command MUST be blocked and MUST NOT be sent

### Requirement: Manual takeover modes MUST imply immediate yield even before later state transitions settle
The system MUST use recognized manual takeover modes as an immediate guardrail against autonomous command emission.

#### Scenario: Flight mode already indicates MANUAL
- **WHEN** the current vehicle mode is already a recognized manual takeover mode at the time a command path is invoked
- **THEN** the system MUST reject the autonomous command even if later override handling has not fully completed yet

### Requirement: Override handling MUST remain observable and testable
The runtime MUST provide regression coverage proving that manual takeover disables autonomous command emission.

#### Scenario: Override-triggered command suppression test
- **WHEN** automated tests simulate override/manual takeover and then invoke autonomous command paths
- **THEN** the tests MUST verify that no outbound MAVLink control command is sent

