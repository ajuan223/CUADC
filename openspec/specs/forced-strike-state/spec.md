# forced-strike-state

## Requirements

- REQ-FS-001: ForcedStrikeState activates after max_scan_cycles LOITER timeouts
- REQ-FS-002: Shall generate random point via forced_strike_point utility
- REQ-FS-003: Generated point must pass point_in_polygon validation (RL-10)
- REQ-FS-004: Shall fly to generated point and execute release
- REQ-FS-005: After release, shall transition to LANDING
- REQ-FS-006: DRY_RUN mode shall skip actual release but log the point
