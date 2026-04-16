## 1. Mission model updates

- [x] 1.1 Build and upload a full fixed-wing mission in PREFLIGHT with `NAV_TAKEOFF`, scan waypoints, and landing sequence items.
- [x] 1.2 Store the uploaded landing sequence start index in mission context for later landing jumps.

## 2. State and controller changes

- [x] 2.1 Replace direct fixed-wing `MAV_CMD_NAV_TAKEOFF` usage with mission-current selection plus `AUTO` start behavior.
- [x] 2.2 Update `LandingState` to jump to the stored landing-sequence index from the pre-uploaded full mission.

## 3. Regression coverage

- [x] 3.1 Add or update unit tests for fixed-wing takeoff mission start behavior.
- [x] 3.2 Add or update unit tests for PREFLIGHT mission upload and landing index usage.
