# app-main-loop

## Requirements

- REQ-APP-001: Load and validate FieldProfile at startup (RL-08)
- REQ-APP-002: Refuse launch on invalid FieldProfile
- REQ-APP-003: Initialize all subsystems with dependency injection
- REQ-APP-004: Create MissionContext with all subsystem references
- REQ-APP-005: Launch async tasks via asyncio.TaskGroup
- REQ-APP-006: --field CLI argument for field profile selection
- REQ-APP-007: Graceful shutdown on SIGINT/SIGTERM
- REQ-APP-008: Structured logging of startup sequence

## Updated Requirement Detail

### Requirement: Graceful shutdown on SIGINT/SIGTERM
The application SHALL perform graceful shutdown on `SIGINT` and `SIGTERM` by signaling every long-running subsystem started by the main loop to stop, awaiting their cleanup, and releasing owned resources before process exit.

#### Scenario: Operator stops Striker with Ctrl+C
- **WHEN** the running application receives `SIGINT`
- **THEN** it stops the mission state machine, heartbeat monitor, safety monitor, flight recorder, vision receiver, and background dispatch loops
- **AND** it disconnects the MAVLink connection after subsystem stop has begun
- **AND** it exits without leaving application-owned listener ports bound

#### Scenario: Service manager stops Striker with SIGTERM
- **WHEN** the running application receives `SIGTERM`
- **THEN** it performs the same graceful shutdown sequence as `SIGINT`
- **AND** all started subsystems are given a deterministic stop path before process exit
