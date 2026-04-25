# scan-loiter-states

## Requirements

- REQ-SCAN-001: ScanMonitorState shall monitor mission progress while the aircraft executes the preburned scan segment in AUTO
- REQ-SCAN-002: ScanMonitorState shall transition directly to GUIDED_STRIKE when the loiter hold point (NAV_LOITER_UNLIM) is reached
- REQ-SCAN-003: GuidedStrikeState shall resolve the drop point from vision first, then field fallback_drop_point
- REQ-SCAN-004: The standard mission flow shall not require intermediate LOITER or FORCED_STRIKE states between scan and strike
