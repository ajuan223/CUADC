# flight-controller

## Requirements

- REQ-FLIGHT-001: arm() shall send ARM command only after pre-arm checks pass (RL-01)
- REQ-FLIGHT-002: takeoff(alt_m) shall set AUTO mode with NAV_TAKEOFF mission item
- REQ-FLIGHT-003: goto(lat, lon, alt_m) shall use GUIDED mode with SET_POSITION_TARGET
- REQ-FLIGHT-004: set_mode(mode) shall verify mode change via ACK
- REQ-FLIGHT-005: set_speed(speed_mps) shall send MAV_CMD_DO_CHANGE_SPEED
- REQ-FLIGHT-006: ArduPlane mode enum covering MANUAL, FBWA, AUTO, GUIDED, LOITER, RTL
- REQ-FLIGHT-007: All GPS coordinates validated via validate_gps() before use (RL-05)
- REQ-FLIGHT-008: All configurable parameters from StrikerSettings (RL-06)
