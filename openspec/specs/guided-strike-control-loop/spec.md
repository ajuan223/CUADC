# guided-strike-control-loop Specification

## Purpose
Define the definitive core control architecture of Striker ("一燃到底 + GUIDED 领航 + 切门投弹"). This specification supersedes all prior architectures involving dynamic mission uploading, ballistic recalculation, and sequence-syncing. It establishes the "One Preburned Mission" doctrine coupled with mid-flight `GUIDED` mode intervention.

## Requirements

### Requirement: "一燃到底" (One Preburned Mission) - Unified Mission Lifecycle
The system SHALL operate on a single, pre-uploaded flight plan encompassing the entire mission lifecycle (Takeoff → Scan → Landing) without ever uploading a temporary attack mission.

#### Scenario: Preflight mission burn
- **WHEN** the aircraft enters the `Standby` state
- **THEN** the system SHALL upload the complete mission containing takeoff, the boustrophedon scan pattern, and the landing sequence.
- **AND** the system SHALL NOT modify or upload new mission items during the flight.

### Requirement: "GUIDED 领航" (GUIDED Takeover) - Dynamic Strike Axis Navigation
Striker SHALL hijack control from the flight controller's internal mission planner strictly during the strike phase by using `GUIDED` mode and `MAV_CMD_DO_REPOSITION` commands.

#### Scenario: Striker intervenes and controls the attack axis
- **WHEN** the scan monitor completes and a drop point is resolved
- **THEN** Striker SHALL switch the aircraft from `AUTO` to `GUIDED` mode.
- **AND** Striker SHALL calculate an `approach_point` and an `exit_point` perfectly aligned across the target drop point, oriented into the wind or along a fallback heading.
- **AND** Striker SHALL command the aircraft to the `approach_point` using `MAV_CMD_DO_REPOSITION`.
- **AND** upon reaching the `approach_point` radius, Striker SHALL command the aircraft to the `exit_point` using `MAV_CMD_DO_REPOSITION`, enforcing a straight flight path over the target gate.

#### Scenario: Handover back to preburned landing
- **WHEN** the payload release has been executed and the release monitor completes
- **THEN** Striker SHALL switch the aircraft back to `AUTO` mode.
- **AND** Striker SHALL set the `mission_current` pointer to the `DO_LAND_START` sequence item defined in the preburned mission, seamlessly resuming the landing sequence.

### Requirement: "切门投弹" (Gate Crossing Release) - Zero-Latency Trigger
Striker SHALL treat the external target coordinate as the absolute spatial release point (no ballistic compensation needed). Striker SHALL strictly monitor the aircraft's cross-track geometry on the attack axis and fire the payload release immediately when crossing the drop point's vertical plane.

#### Scenario: Dropping payload exactly at target gate
- **WHEN** the aircraft's projected progress (`target_frac`) along the attack axis reaches or exceeds the exact target point projection
- **AND** the cross-track error is within the configurable tolerance (e.g., `cross_track_limit`)
- **THEN** Striker SHALL issue the payload release command synchronously via a fire-and-forget `MAV_CMD_DO_SET_SERVO` command.
- **AND** the system SHALL NOT use wide proximity acceptance zones (e.g., 35m) to trigger early drops, relying solely on the gate crossing.

#### Scenario: Extreme proximity fallback
- **WHEN** the aircraft's physical distance to the target falls within a strictly minimized fallback radius (e.g., 2.0 meters) before crossing the gate
- **THEN** Striker SHALL trigger the payload release as a physical contact fail-safe.
