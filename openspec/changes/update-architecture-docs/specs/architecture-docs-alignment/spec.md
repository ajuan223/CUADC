## ADDED Requirements

### Requirement: Document the Preburned Mission state chain
The user manual and relevant architecture documents SHALL document the current mission state sequence exactly as: `INIT → STANDBY → SCAN_MONITOR → GUIDED_STRIKE → RELEASE_MONITOR → LANDING_MONITOR → COMPLETED`.

#### Scenario: Reading the user manual state chain
- **WHEN** a developer reads the `user_manual.md` section on the mission chain
- **THEN** they see the `STANDBY`, `SCAN_MONITOR`, and `GUIDED_STRIKE` states instead of obsolete `PREFLIGHT` and `TAKEOFF` states

### Requirement: Remove Procedural Generation references
The user manual and SITL setup guides SHALL NOT describe programmatic generation of takeoff, scan, or landing geometries, as these features were removed in the `preburned-mission-refactor`.

#### Scenario: Reading the SITL validation guide
- **WHEN** a developer reads the SITL setup guide
- **THEN** they find instructions on downloading preburned missions and monitoring `DO_REPOSITION` takeovers, without any mention of procedurally derived 573m landing approach distances or Boustrophedon sweeps

### Requirement: Archive the Procedural Generation Vision
The `init愿景.md` document SHALL be moved to `docs/archive/procedural_generation_vision.md` and marked as historical, as its thesis directly contradicts the current preburned mission architecture.

#### Scenario: Navigating repository documentation
- **WHEN** a developer browses the root directory
- **THEN** they do not see `init愿景.md`, but instead find it preserved in the `docs/archive/` folder for historical reference
