# safety-monitor

## Requirements

- REQ-SAFE-001: SafetyMonitor shall run as continuous coroutine from start to termination (RL-02)
- REQ-SAFE-002: Battery check shall trigger EmergencyEvent when voltage below threshold
- REQ-SAFE-003: GPS check shall verify fix type and satellite count
- REQ-SAFE-004: Heartbeat check shall use heartbeat monitor health status
- REQ-SAFE-005: Airspeed check shall warn when below configurable stall speed
- REQ-SAFE-006: Geofence check shall trigger EmergencyEvent when outside boundary
- REQ-SAFE-007: Override detector shall monitor FC mode changes and emit OverrideEvent (RL-03)
- REQ-SAFE-008: Check interval configurable via settings (default 1s)
- REQ-SAFE-009: Geofence polygon from FieldProfile boundary data
- REQ-SAFE-010: OverrideEvent is terminal — no automatic recovery (RL-03)
