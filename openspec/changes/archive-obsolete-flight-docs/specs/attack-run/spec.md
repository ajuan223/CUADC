## REMOVED Requirements

### Requirement: Attack run geometry calculation

**Reason**: Replaced by `guided-strike-control-loop`. The attack run geometry is now part of the real-time GUIDED takeover rather than an offline mission calculation.
**Migration**: See `guided-strike-control-loop` spec.

### Requirement: Attack run mission generation

**Reason**: Striker no longer dynamically uploads an attack mission. The preburned mission strategy handles the full flight, and the strike is executed dynamically in GUIDED mode.
**Migration**: Use preburned mission + GUIDED mode intervention.

### Requirement: Enroute state executes attack run

**Reason**: The ENROUTE state concept transitioning based on `mission_current_seq` is obsolete. GuidedStrikeState now manages the approach and strike phases entirely.
**Migration**: See `guided-strike-control-loop` spec.

### Requirement: Release state confirms native release

**Reason**: Modified and moved to `payload-release`. Release confirmation now uses fire-and-forget `send_command` without waiting for native mission item completion.
**Migration**: See `payload-release` spec.

### Requirement: Landing state uses pre-uploaded mission

**Reason**: The landing sequence is now the tail end of the single preburned mission. Striker simply switches back to AUTO mode to resume landing.
**Migration**: See `guided-strike-control-loop` spec.
