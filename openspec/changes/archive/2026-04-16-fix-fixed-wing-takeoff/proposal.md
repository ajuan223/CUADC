## Why

Striker currently issues a direct `COMMAND_LONG MAV_CMD_NAV_TAKEOFF` from `TakeoffState`, but ArduPlane fixed-wing rejects that path in SITL and real fixed-wing semantics expect takeoff to be initiated from an AUTO mission. We need to align the takeoff flow with ArduPlane's mission model so the mission can progress from takeoff into scan and later jump into the pre-uploaded landing sequence.

## What Changes

- Replace the direct fixed-wing `MAV_CMD_NAV_TAKEOFF` command path with a pre-uploaded AUTO mission whose first item is `NAV_TAKEOFF`.
- Upload a single fixed-wing mission during PREFLIGHT that contains takeoff, scan waypoints, and the landing sequence in one consistent index space.
- Start takeoff by selecting mission index `0` and entering `AUTO`, and trigger landing by jumping to the precomputed landing start index from the same uploaded mission.
- Add focused unit coverage for mission upload/start behavior so this fixed-wing contract does not regress.

## Capabilities

### New Capabilities
- `fixed-wing-takeoff-sequence`: Define the fixed-wing mission upload and AUTO-start contract for takeoff, scan continuation, and landing jump behavior.

### Modified Capabilities
- `utils-skill`: Landing sequence triggering must remain compatible with a full pre-uploaded mission whose first item is a takeoff command.

## Impact

- Affected code: `src/striker/flight/controller.py`, `src/striker/flight/mission_upload.py`, `src/striker/core/states/preflight.py`, `src/striker/core/states/takeoff.py`, `src/striker/core/states/landing.py`, `src/striker/core/context.py`, related tests.
- Affected runtime behavior: PREFLIGHT mission upload, TAKEOFF mission start, LANDING mission index selection.
- External dependency/behavior: ArduPlane AUTO mission semantics and `NAV_TAKEOFF` mission-item behavior.
