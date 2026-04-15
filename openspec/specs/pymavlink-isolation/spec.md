## ADDED Requirements

### Requirement: MAVLink command constants exported from comms layer
The system SHALL export MAVLink command IDs, mode flags, frame types, result codes, and type constants as module-level integer values from `striker.comms.messages`. Flight, payload, and all other non-comms modules SHALL NOT import `pymavlink` directly for these constants.

Constants to export: `MAV_CMD_COMPONENT_ARM_DISARM` (400), `MAV_CMD_NAV_TAKEOFF` (22), `MAV_CMD_DO_SET_MODE` (176), `MAV_CMD_DO_CHANGE_SPEED` (178), `MAV_CMD_DO_SET_SERVO` (183), `MAV_CMD_DO_LAND_START` (189), `MAV_CMD_NAV_LAND` (21), `MAV_CMD_NAV_WAYPOINT` (16), `MAV_CMD_MISSION_SET_CURRENT` (224), `MAV_MODE_FLAG_CUSTOM_MODE_ENABLED` (1), `MAV_MODE_FLAG_SAFETY_ARMED` (128), `MAV_RESULT_ACCEPTED` (0), `MAV_TYPE_GCS` (6), `MAV_AUTOPILOT_INVALID` (8), `MAV_FRAME_GLOBAL_RELATIVE_ALT` (3), `MAV_FRAME_GLOBAL_RELATIVE_ALT_INT` (6).

#### Scenario: FlightController uses comms constants instead of pymavlink
- **WHEN** `FlightController.arm()` is called
- **THEN** it imports `MAV_CMD_COMPONENT_ARM_DISARM` from `striker.comms.messages` and does NOT import `pymavlink.mavutil`

#### Scenario: MavlinkRelease uses comms constants instead of pymavlink
- **WHEN** `MavlinkRelease.release()` is called
- **THEN** it imports `MAV_CMD_DO_SET_SERVO` and `MAV_RESULT_ACCEPTED` from `striker.comms.messages` and does NOT import `pymavlink.mavutil`

#### Scenario: No pymavlink import outside comms package
- **WHEN** a grep for `from pymavlink` is run on `src/striker/` excluding `src/striker/comms/`
- **THEN** zero matches are found

#### Scenario: HeartbeatMonitor sends heartbeat via MAVLinkConnection
- **WHEN** `HeartbeatMonitor._heartbeat_sender()` runs
- **THEN** it constructs a heartbeat message using `striker.comms.messages` constants and sends via `conn.send()`, NOT by calling `conn.mav.mav.heartbeat_send()` directly
