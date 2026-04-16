# scan-loiter-states

## Requirements

- REQ-SCAN-001: ScanState shall set AUTO mode and execute scan waypoint sequence
- REQ-SCAN-002: scan_cycle_count shall increment on each SCAN entry
- REQ-SCAN-003: scan_cycle_count shall reset to 0 in PreflightState
- REQ-SCAN-004: SCAN complete shall transition to LOITER
- REQ-LOITER-001: LoiterState shall set LOITER mode with configured radius
- REQ-LOITER-002: LOITER shall start configurable timeout timer (loiter_timeout_s)
- REQ-LOITER-003: On timeout: cycle < max_scan_cycles → transition back to SCAN
- REQ-LOITER-004: On timeout: cycle >= max_scan_cycles → transition to FORCED_STRIKE
- REQ-LOITER-005: On valid target received → transition to ENROUTE immediately
- REQ-LOITER-006: LOITER radius and timeout configurable from settings
