# target-tracker

## Requirements

- REQ-TRACKER-001: Sliding window (deque) for coordinate buffering
- REQ-TRACKER-002: 0 Hz input: maintain last state, no target available
- REQ-TRACKER-003: Single reception: immediately adopt, no smoothing
- REQ-TRACKER-004: Low frequency (<1Hz): each update adopted directly
- REQ-TRACKER-005: High frequency (>1Hz): N-frame median smoothing
- REQ-TRACKER-006: Stale detection: configurable timeout marks target expired
- REQ-TRACKER-007: Window size configurable via settings
