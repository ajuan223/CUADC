# mission-upload

## Requirements

- REQ-MISSION-001: Upload shall follow strict MAVLink micro-protocol
- REQ-MISSION-002: Step 1: MISSION_CLEAR_ALL → verify MISSION_ACK
- REQ-MISSION-003: Step 2: MISSION_COUNT with total item count
- REQ-MISSION-004: Step 3: Respond to MISSION_REQUEST_INT per item by index
- REQ-MISSION-005: Step 4: Final MISSION_ACK verification (type == ACCEPTED)
- REQ-MISSION-006: Timeout handling for each protocol step
- REQ-MISSION-007: Scan waypoints generated from FieldProfile scan_waypoints
- REQ-MISSION-008: Landing sequence from FieldProfile landing config
