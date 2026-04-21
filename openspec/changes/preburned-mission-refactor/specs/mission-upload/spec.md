## MODIFIED Requirements

### Requirement: Upload shall follow strict MAVLink micro-protocol regardless of whether mission items are hand-authored or procedurally generated
The existing `upload_mission()` function SHALL be preserved as-is for full mission uploads. A new `partial_write_mission()` function SHALL be added alongside it.

#### Scenario: Full upload protocol unchanged
- **WHEN** `upload_mission(conn, items)` is called
- **THEN** the existing MISSION_CLEAR_ALL → MISSION_COUNT → MISSION_REQUEST_INT → MISSION_ACK protocol SHALL execute unchanged

### Requirement: Scan waypoints generated from procedural field constraints
This requirement is **suspended** for the preburned mission flow. Scan waypoints are preburned via Mission Planner.

#### Scenario: No scan waypoint generation in preburned mode
- **WHEN** the system operates in preburned mission mode
- **THEN** the upload pipeline SHALL NOT generate or upload scan waypoints
- **AND** scan waypoints SHALL be read from the preburned mission via download

### Requirement: Landing sequence generated from procedural landing config
This requirement is **suspended** for the preburned mission flow. Landing sequence is preburned via Mission Planner.

#### Scenario: No landing sequence generation in preburned mode
- **WHEN** the system operates in preburned mission mode
- **THEN** the upload pipeline SHALL NOT generate or upload landing sequences
- **AND** landing sequence SHALL be part of the preburned mission

## REMOVED Requirements

### Requirement: upload_full_mission
**Reason**: Full mission upload replaced by preburned mission + partial write.
**Migration**: Use StandbyState mission download + LoiterHold partial write.

### Requirement: upload_attack_mission
**Reason**: Attack mission upload replaced by partial write of reserved slots.
**Migration**: Use `partial_write_mission()` in LOITER_HOLD state.

### Requirement: upload_landing_mission
**Reason**: Landing-only mission upload no longer needed; landing is preburned.
**Migration**: Flight controller automatically proceeds to preburned landing after attack slots.
