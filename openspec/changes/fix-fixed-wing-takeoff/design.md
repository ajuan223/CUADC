## Context

Striker now connects cleanly to ArduPlane SITL and reaches `takeoff`, but the current implementation still sends `COMMAND_LONG MAV_CMD_NAV_TAKEOFF` from `src/striker/flight/controller.py`. MCP/Context7-backed ArduPilot documentation indicates that fixed-wing automatic takeoff is expected to run as a `NAV_TAKEOFF` mission item in `AUTO` mode. The codebase already assumes mission-based landing: `LandingState` jumps into a pre-uploaded landing sequence with `MAV_CMD_MISSION_SET_CURRENT`, and `mission_upload.py` already contains the MAVLink mission upload protocol.

The design constraint is therefore not “how to make ArduPlane accept one more command”, but “how to make takeoff, scan, and landing share one mission model”. The uploaded mission must preserve the existing scan/landing state flow while removing the fixed-wing-incompatible direct takeoff command.

## Goals / Non-Goals

**Goals:**
- Make fixed-wing takeoff start through a pre-uploaded AUTO mission instead of direct `COMMAND_LONG MAV_CMD_NAV_TAKEOFF`.
- Upload one coherent mission in PREFLIGHT that contains takeoff, scan, and landing items.
- Preserve the existing state-machine structure (`takeoff -> scan -> ... -> landing`) while making mission indices deterministic.
- Keep the landing jump behavior aligned with the uploaded mission indices.

**Non-Goals:**
- Rework scan completion logic to consume real `MISSION_ITEM_REACHED` events.
- Redesign non-fixed-wing or quadplane takeoff behavior.
- Solve unrelated flight-recorder flushing issues in this change.

## Decisions

### 1. Use a full pre-uploaded mission for fixed-wing flight
We will upload a single mission during PREFLIGHT with this order:
1. `NAV_TAKEOFF`
2. scan waypoints
3. landing sequence (`DO_LAND_START`, approach waypoint, `NAV_LAND`)

This matches ArduPlane’s AUTO mission model and keeps takeoff, scan, and landing in the same index space.

**Alternatives considered**
- **Keep direct `COMMAND_LONG MAV_CMD_NAV_TAKEOFF`**: rejected because fixed-wing ArduPlane returns command failure.
- **Use Plane TAKEOFF mode instead of mission upload**: rejected because the rest of Striker already assumes mission-index-based landing entry and mission continuity after takeoff.
- **Upload scan and landing as separate missions**: rejected because each upload clears the previous mission and breaks the landing jump contract.

### 2. Start takeoff by selecting mission item 0 and entering AUTO
`FlightController.takeoff()` will stop issuing direct `MAV_CMD_NAV_TAKEOFF`. Instead it will select mission item `0` and switch to `AUTO`, which starts the uploaded takeoff mission.

**Alternatives considered**
- **Rely on AUTO alone without setting current mission index**: possible, but less explicit and more fragile when the mission pointer was changed earlier.
- **Send `MAV_CMD_MISSION_START`**: not chosen because the documented Plane/SITL workflow is mission item + AUTO sequencing, and the current code already uses mission-current jumps for landing.

### 3. Persist landing start index in mission context
PREFLIGHT will store the landing sequence start index produced when building/uploading the full mission. `LandingState` will jump to that stored index instead of recomputing a partial index that ignores the takeoff item.

**Alternatives considered**
- **Recompute `len(scan_waypoints)` in `LandingState`**: rejected because takeoff now occupies mission item `0`, so the existing formula becomes off by one.

## Risks / Trade-offs

- **[Mission upload fails during PREFLIGHT]** → Keep the state in PREFLIGHT, log the failure, and avoid advancing to TAKEOFF.
- **[Mission index drift between builder and landing trigger]** → Store the computed landing start index in mission context at upload time instead of deriving it ad hoc later.
- **[State-machine scan timing diverges from actual mission progress]** → Accept for this change; real mission progress monitoring remains out of scope and can be handled separately.
