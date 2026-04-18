---
name: sitl-autodebug-loop
description: Automatically iterate SITL flight debugging for Striker fixed-wing missions. Use when the task is to repeatedly launch SITL, run Striker, inspect logs, diagnose mismatches against the required takeoff-scan-release-landing flow, patch code, and rerun. Never use this skill to modify field JSON, merged params, safety constraints, or to disable existing checks.
---

Automatically iterate SITL flight debugging for Striker fixed-wing missions until the full chain passes: takeoff -> strict scan path -> payload release -> landing on the same runway.

**Input**: No required input. Optionally specify field name (defaults to `zjg2`).

**Goal**: Not "it flew" — the **only** acceptable outcome is:
1. Same-runway takeoff, no early deviation
2. Strict scan waypoint order, no skips or boundary violations
3. Enter release phase and complete payload drop
4. Approach and land on the same runway via proper approach geometry

## Red Lines

**NEVER** modify:
- `data/fields/**` — field JSON is immutable ground truth (except adding new optional fields like fallback_drop_point)
- `*.param`, `sitl_merged.param`, ArduPilot defaults
- Existing safety constraints (geofence must remain strict, airspeed, landing corridor, mission gating)
- Do not attribute problems to "SITL randomness" without log evidence
- **Geofence must be strictly enforced** — aircraft must never be outside boundary. Turn radius margin is handled by scan waypoint inset (`scan_boundary_margin_m`), not by relaxing the geofence check.

**Allowed** modification scope:
- `src/striker/flight/` — path planning, trajectory generation, approach/landing geometry
- `src/striker/core/states/` — task switching, scan/release/landing state gating
- `src/striker/telemetry/`, `src/striker/safety/` — logging, observation, timing logic (without relaxing constraints)
- Test and debug helper code

## Startup Sequence (Every Round)

1. **Clean residual processes and ports**
   ```bash
   pkill -f "python -m striker" || true
   pkill -f mavproxy.py || true
   pkill -f arduplane || true
   ```
   Then verify ports 5760, 14550, 14551 are free:
   ```bash
   ss -ltnup | grep -E ':5760|:14550|:14551'
   ```
   If still occupied, use `lsof` to identify and kill specific processes.

2. **Launch SITL stack**
   ```bash
   cd ~/dev-zju/cuax-autodriv && scripts/run_sitl.sh zjg2
   ```
   From its output, extract these paths:
   - `MAVProxy log: ...`
   - `Flight log target: ...`
   - `Artifact dir: ...`
   Ignore `SITL log`.

3. **Launch Striker** (after SITL stack is ready)
   ```bash
   cd ~/dev-zju/cuax-autodriv
   STRIKER_TRANSPORT=udp \
   STRIKER_MAVLINK_URL=udp:127.0.0.1:14550 \
   STRIKER_ARM_FORCE_BYPASS=1 \
   STRIKER_DRY_RUN=true \
   STRIKER_CRUISE_SPEED_MPS=12 \
   .venv/bin/python -m striker --field zjg2
   ```

4. **Monitor Striker** until it prints `stopped`, the process exits, or it clearly hangs/fails.

5. **Collect evidence and diagnose** (see sections below).

6. **Patch code**, then loop back to step 1.

## Required Evidence Collection (Every Round)

Check all three artifacts:

1. **MAVProxy log** — flight plan uploads, waypoint events, servo commands
2. **Flight log CSV** (`Flight log target`) — position, altitude, airspeed, mission sequence
3. **Artifact dir** — especially `striker.log` and any derived diagnostics

If `Flight log target` doesn't exist or artifact dir has no Striker logs, that IS the failure — record as one of:
- Striker didn't start normally
- Striker didn't connect to MAVLink
- Flight recorder didn't start
- Process exited early

## Expected Behavior Checklist

Compare actual behavior against this chain every round:

| Phase | Expected | Failure Pattern |
|-------|----------|-----------------|
| takeoff | Track from runway heading, no deviation | Early turn away from field |
| scan | Follow scan waypoints in strict order | Skip waypoints, scan out of bounds |
| release | Enter attack/release task chain after scan | Jump directly from scan to landing |
| landing | Proper approach → final → touchdown on runway | No approach evidence, "speed 0" in air, off-runway touchdown |

## Diagnosis Priority

When you see an anomaly, investigate in this order — don't guess "flight controller divergence" first:

1. Did the application state machine actually run? (FSM transitions in striker.log)
2. What mission was uploaded — and was it replaced mid-flight?
3. Did geometry generation produce out-of-bounds or wrong approach points?
4. Did a safety constraint legitimately block the next phase?
5. Is flight controller execution consistent with the uploaded mission?

## Log Reading Guide

### MAVProxy log — key patterns

- `AP: Flight plan received` — mission upload event
- `AP: Mission: N ...` — mission content
- `Reached waypoint` / `Passed waypoint` — waypoint progress
- `LandStart` — landing trigger
- `DO_SET_SERVO` — payload release
- `Distance from LAND point` — approach progress
- `SIM Hit ground` — touchdown/crash

**Interpretation rules**:
- Only one `Flight plan received`, scan followed immediately by `LandStart` = **no release chain**
- Early scan waypoint boundary violation = **suspect scan geometry generation**
- `Land` without approach/descent evidence = **suspect landing activation or approach geometry**

### Flight log CSV — key columns

- Position vs field boundary
- Current mission seq vs expected scan/release/landing phase
- Airspeed, altitude, groundspeed reasonableness per phase
- "Altitude airborne but speed zero" = invalid state

### Striker output / striker.log — key patterns

- `FSM transition`, `State entered/exited` — state machine progress
- `mission uploaded` — upload confirmation
- `scan`, `enroute`, `release`, `landing` — phase entries
- `stopped` — completion
- `warning` / `emergency` — safety events

If the app never enters `scan -> enroute -> release`, do NOT blame the payload mechanism.

## Debugging Discipline

**One causal category per round** — never mix:

| Category | What to change |
|----------|---------------|
| Geometry error | Only `mission_geometry`, `navigation`, `landing_sequence` |
| State transition error | Only state gating, mission progress interpretation |
| Observation error | Only telemetry, recorder, event detection |

After each code change:
1. Run CI/CD checks — `ruff check` and `mypy` on all changed Python files (must pass with zero errors before proceeding)
2. Add or update unit/regression tests
3. Run all unit tests (`pytest tests/ --ignore=tests/integration`) — must pass
4. Run a full SITL round
5. Verify the symptom is gone AND no new regressions appeared
6. Record in `./route_changelog/roundN.log`

## Round Changelog

Create `./route_changelog/` if it doesn't exist. Write `round1.log`, `round2.log`, etc. Each file must contain:

1. Timestamp
2. Artifact directory and log paths used
3. Observed actual behavior
4. Differences from expected chain
5. Code changes made
6. Rationale for changes
7. Verification results
8. Remaining issues for next round

The changelog's purpose: a future reader can pick up without re-reading all old logs — what was tried, what hypothesis was disproven, which symptoms are resolved, and where the remaining problem sits.

## Completion Criteria

All of the following must be satisfied in a single round:
- No boundary violation after takeoff
- Scan follows full planned path
- Scan -> release transition (not scan -> landing)
- Proper approach sequence before landing
- Touchdown within runway corridor
- Logs and code changes are self-consistent

**If not all satisfied, continue to next round.** Do not stop at "analysis complete".

## Guardrails

- Keep looping until completion criteria are met — don't stop mid-debug
- Only modify code in the allowed scope
- One causal category per round
- Always collect all three evidence sources before diagnosing
- Always record changelog before starting next round
- If stuck after 5 rounds on the same symptom, pause and report to the user
