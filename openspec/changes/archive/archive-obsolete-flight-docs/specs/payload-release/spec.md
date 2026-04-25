## MODIFIED Requirements

### Requirement: MAVLink channel: DO_SET_SERVO with zero-latency execution
The system SHALL execute the MAVLink payload release command using a non-blocking, fire-and-forget `send_command` wrapper to ensure zero latency at the precise gate crossing.

#### Scenario: Fire-and-forget MAVLink release execution
- **WHEN** the release trigger condition is met during non-dry-run mode
- **THEN** the system SHALL send `MAV_CMD_DO_SET_SERVO` over MAVLink
- **AND** it SHALL NOT block waiting for `COMMAND_ACK`, ensuring instantaneous release action

## REMOVED Requirements

### Requirement: MAVLink channel: DO_SET_SERVO with COMMAND_ACK verification
**Reason**: Waiting for COMMAND_ACK caused unacceptable jitter and delays at the exact moment of gate crossing.
**Migration**: Use the fire-and-forget implementation detailed in the modified requirement.
