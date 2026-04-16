# ballistic-solver

## Requirements

- REQ-BALL-001: Free-fall parabolic trajectory: t_fall = sqrt(2h/g)
- REQ-BALL-002: Wind compensation in displacement calculation
- REQ-BALL-003: Release point via geopy geodesic reverse projection (WGS-84)
- REQ-BALL-004: Known-answer tests: error < 0.1m for 3+ test cases
- REQ-BALL-005: Physical parameter dataclasses for ballistic config
- REQ-BALL-006: Altitude <= 0 returns target coordinates unchanged
