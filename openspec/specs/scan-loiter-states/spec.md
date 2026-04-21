# scan-loiter-states

## Requirements

- REQ-SCAN-001: ScanMonitorState shall monitor mission progress while the aircraft executes the uploaded scan segment in AUTO
- REQ-SCAN-002: ScanMonitorState shall transition directly to LOITER_HOLD when scan completion is observed
- REQ-SCAN-003: LoiterHoldState shall resolve the drop point from vision first, then field fallback point
- REQ-SCAN-004: The standard mission flow shall not require a LOITER or FORCED_STRIKE state between SCAN and ENROUTE
