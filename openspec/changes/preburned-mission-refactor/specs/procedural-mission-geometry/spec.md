## MODIFIED Requirements

### Requirement: Procedural mission geometry generates scan path using Boustrophedon algorithm
This requirement is **suspended** for the preburned mission flow. Scan path is preburned via Mission Planner.

#### Scenario: No scan path generation in preburned mode
- **WHEN** the system operates in preburned mission mode
- **THEN** the boustrophedon scan generator SHALL NOT be invoked
- **AND** scan path SHALL exist only in the preburned mission

### Requirement: Procedural mission geometry generates takeoff path from runway facts
This requirement is **suspended** for the preburned mission flow. Takeoff geometry is preburned via Mission Planner.

#### Scenario: No takeoff geometry generation in preburned mode
- **WHEN** the system operates in preburned mission mode
- **THEN** the takeoff geometry generator SHALL NOT be invoked

### Requirement: Procedural mission geometry derives landing approach from runway facts
This requirement is **suspended** for the preburned mission flow. Landing approach is preburned via Mission Planner.

#### Scenario: No landing approach derivation in preburned mode
- **WHEN** the system operates in preburned mission mode
- **THEN** the landing approach derivation SHALL NOT be invoked

## REMOVED Requirements

### Requirement: Unified mission geometry result object
**Reason**: MissionGeometryResult was the output container for full procedural geometry. With preburned missions, the result object is no longer the primary data source — critical seq numbers come from mission download instead.
**Migration**: Replace with `PreburnedMissionInfo` dataclass populated during StandbyState mission download, holding `loiter_seq`, `slot_start_seq`, `slot_end_seq`, `landing_start_seq`.

## ADDED Requirements

### Requirement: Simplified attack geometry for slot overwrite
The system SHALL compute approach and exit waypoints for the partial write slots, using the resolved drop point and the landing approach coordinates from the downloaded mission.

#### Scenario: Compute approach waypoint
- **WHEN** the drop point is at `(30.261, 120.095)` and landing approach is known
- **THEN** the system SHALL compute approach waypoint behind the target along the approach heading at configured `approach_distance_m`

#### Scenario: Compute exit waypoint
- **WHEN** the drop point and approach heading are known
- **THEN** the system SHALL compute exit waypoint ahead of the target along the approach heading at configured `exit_distance_m`
