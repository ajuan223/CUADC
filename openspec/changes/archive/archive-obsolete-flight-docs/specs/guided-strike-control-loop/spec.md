## ADDED Requirements

### Requirement: Striker executes strike via GUIDED DO_REPOSITION
Striker SHALL execute the strike maneuver by taking over the preburned mission using `GUIDED` mode and issuing `MAV_CMD_DO_REPOSITION` commands.

#### Scenario: Striker intervenes and controls the attack axis
- **WHEN** the scan monitor completes and a drop point is resolved
- **THEN** Striker SHALL switch to `GUIDED` mode and command the aircraft to an approach point on the attack axis using `MAV_CMD_DO_REPOSITION`.
- **AND** upon reaching the approach point, Striker SHALL command the aircraft to the exit point on the attack axis, enforcing a straight flight path over the target gate.

### Requirement: Striker executes zero-latency release upon exact gate crossing
Striker SHALL strictly monitor the aircraft's cross-track geometry on the attack axis and fire the payload release immediately when crossing the drop point's vertical plane.

#### Scenario: Dropping payload exactly at target gate
- **WHEN** the aircraft's projected progress along the attack axis reaches the exact target point projection
- **THEN** Striker SHALL issue the payload release command synchronously without waiting for proximity acceptance zones to trigger early drops.
