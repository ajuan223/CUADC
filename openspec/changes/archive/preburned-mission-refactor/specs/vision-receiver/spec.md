## MODIFIED Requirements

### Requirement: Vision receiver interface changed to global variable
The vision receiver SHALL change from external TCP/UDP receiver to an in-process Python global variable interface. The existing `TcpReceiver` and `DropPointTracker` SHALL be replaced by `global_var.py` accessor functions.

#### Scenario: Vision program sets drop point via global variable
- **WHEN** the vision program running in the same Python process calls `set_vision_drop_point(lat, lon)`
- **THEN** the drop point SHALL be stored in the module-level global variable protected by a threading lock

#### Scenario: Striker reads drop point via global variable
- **WHEN** Striker's LOITER_HOLD state calls `get_vision_drop_point()`
- **THEN** it SHALL receive the latest coordinates set by the vision program, or None if not set

## REMOVED Requirements

### Requirement: TCP receiver for vision data
**Reason**: Vision program runs in the same Python process; TCP communication is unnecessary overhead.
**Migration**: Replace `TcpReceiver` usage with `get_vision_drop_point()` from `striker/vision/global_var.py`.

### Requirement: UDP receiver for vision data
**Reason**: Same as TCP receiver removal.
**Migration**: Same as above.

### Requirement: DropPointTracker median smoothing
**Reason**: With a single global variable read at LOITER_HOLD time, median smoothing over a stream is not applicable. The vision program is expected to provide the final computed drop point.
**Migration**: Direct read from global variable in LOITER_HOLD state. If smoothing is needed, the vision program should perform it before setting the global variable.
