# business-states

## Requirements

- REQ-PREFLIGHT-001: PreflightState shall upload geofence to FC
- REQ-PREFLIGHT-002: PreflightState shall upload landing sequence to FC
- REQ-PREFLIGHT-003: PreflightState shall reset scan_cycle_count to 0
- REQ-TAKEOFF-001: TakeoffState shall send ARM + takeoff commands
- REQ-TAKEOFF-002: TakeoffState shall wait for target altitude before transitioning
- REQ-ENROUTE-001: EnrouteState shall use GUIDED goto to target coordinates
- REQ-ENROUTE-002: EnrouteState shall transition to APPROACH on approach distance
- REQ-LANDING-001: LandingState shall trigger landing sequence
- REQ-LANDING-002: LandingState shall detect landing and transition to COMPLETED
- REQ-COMPLETED-001: CompletedState shall be terminal state logging mission success
- REQ-COMPLETED-002: CompletedState shall stop flight recorder
