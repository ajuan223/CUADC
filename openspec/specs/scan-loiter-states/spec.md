# scan-loiter-states

## Requirements

- REQ-SCAN-001: ScanState shall monitor mission progress while the aircraft executes the uploaded scan segment in AUTO
- REQ-SCAN-002: ScanState shall transition directly to ENROUTE when scan completion is observed
- REQ-SCAN-003: ScanState shall resolve the drop point from vision first, then field fallback point, then computed midpoint
- REQ-SCAN-004: The standard mission flow shall not require a LOITER or FORCED_STRIKE state between SCAN and ENROUTE
