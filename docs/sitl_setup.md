# SITL Setup Guide

## Overview

This project now validates the **field-driven procedural mission generation** flow against ArduPlane SITL. The simulated aircraft starts from the configured field location, receives a procedurally generated full mission, completes scan, uploads an attack mission, releases payload, and then either lands successfully or hands over cleanly on human override.

## Validated Mission Chains

```text
Normal vision path:
INIT → PREFLIGHT → TAKEOFF → SCAN → ENROUTE → RELEASE → LANDING → COMPLETED

Fallback path:
INIT → PREFLIGHT → TAKEOFF → SCAN → ENROUTE(fallback midpoint) → RELEASE → LANDING → COMPLETED

Override path:
INIT → PREFLIGHT → TAKEOFF → SCAN → OVERRIDE
```

## Prerequisites

- Linux
- Python 3.13+
- ArduPilot checkout under `~/ardupilot` or custom `ARDUPILOT_DIR`
- Built `arduplane` SITL binary
- Project virtualenv with `mavproxy.py`

## Important Notes

### Correct default params path

Do **not** use:

```text
Tools/autotest/default_params/plane.parm
```

Use:

```text
Tools/autotest/models/plane.parm
```

### Correct SITL home position

The aircraft home must match the configured field area. For `sitl_default`, use:

```text
30.2610,120.0950,0,180
```

If you omit `--home`, ArduPlane will default to Canberra and the mission geometry will be generated for the wrong map.

## Start Sequence

### Preferred manual launcher

Use the validated repo launcher first:

```bash
./scripts/run_sitl.sh <field>
```

It will:

- derive `--home` from the selected field profile
- use `data/fields/<field>/sitl_merged.param`
- use `~/ardupilot/Tools/autotest/models/plane.parm`
- start MAVProxy from the repository `.venv`
- start Striker dry-run against UDP `14550`
- preserve stack logs under `runtime_data/manual_sitl/<field>/<timestamp>/`

### 1. Start ArduPlane SITL manually

```bash
/home/xbp/ardupilot/build/sitl/bin/arduplane \
  -w --model plane --speedup 1 -I 0 \
  --home <derived-from-field-profile> \
  --defaults /home/xbp/dev-zju/cuax-autodriv/data/fields/<field>/sitl_merged.param \
  --defaults /home/xbp/ardupilot/Tools/autotest/models/plane.parm \
  --sim-address=127.0.0.1 \
  &>/tmp/arduplane_sitl.log
```

Verify:

```bash
grep -a "Home:\|PANIC\|Waiting" /tmp/arduplane_sitl.log
```

Expected:

```text
Home: 30.261000 120.095000 alt=0.000000m hdg=180.000000
```

### 2. Start MAVProxy

```bash
/home/xbp/dev-zju/cuax-autodriv/.venv/bin/mavproxy.py \
  --master tcp:127.0.0.1:5760 \
  --out 127.0.0.1:14550 \
  --out 127.0.0.1:14551 \
  &>/tmp/mavproxy.log
```

Verify:

```bash
grep -a "online\|Ready\|Mode" /tmp/mavproxy.log
```

Expected output includes:

- `online system 1`
- `AP: ArduPilot Ready`
- `Mode MANUAL`

### 3. Start Striker

```bash
STRIKER_TRANSPORT=udp \
STRIKER_ARM_FORCE_BYPASS=1 \
STRIKER_RECORDER_OUTPUT_PATH=runtime_data/manual_sitl/latest/flight_log.csv \
/home/xbp/dev-zju/cuax-autodriv/.venv/bin/python -m striker --field sitl_default \
  &>runtime_data/manual_sitl/latest/striker.log
```

## Integration Validation Workflow

The guarded project-venv integration path is in `tests/integration/test_sitl_full_mission.py`.

### Run the three R4 full-chain validations directly

```bash
/home/xbp/dev-zju/cuax-autodriv/.venv/bin/pytest \
  tests/integration/test_sitl_full_mission.py \
  -k "test_normal_path_vision or test_normal_path_fallback or test_human_override" \
  -vv
```

`pytest -k` is the current documented way to select targeted tests by name with boolean expressions, and this repository also marks these tests with `@pytest.mark.integration` for broader integration-only selection.

### Run all integration-marked SITL tests

```bash
/home/xbp/dev-zju/cuax-autodriv/.venv/bin/pytest -m integration -vv
```

## Preserved Artifacts

Each integration run writes a dedicated artifact directory under:

```text
runtime_data/integration_runs/<test-nodeid>-<timestamp>/
```

Full-chain runs preserve:

- `sitl.log`
- `mavproxy.log`
- `striker.log`
- `flight_log.csv`
- `vision.log` for vision/fallback runs

Recent validated examples:

- vision path: `runtime_data/integration_runs/tests-integration-test_sitl_full_mission.py-TestSITLFullMission-test_normal_path_vision-1776376734602/`
- fallback path: `runtime_data/integration_runs/tests-integration-test_sitl_full_mission.py-TestSITLFullMission-test_normal_path_fallback-1776380076063/`
- override path: `runtime_data/integration_runs/tests-integration-test_sitl_full_mission.py-TestSITLFullMission-test_human_override-1776388107026/`

The override run also preserves `flight_log.csv`; the recorder now flushes each sample so a short handover path still leaves a readable CSV before shutdown.

## What Gets Validated

### Procedural landing geometry

The landing approach point is automatically derived from:

- `landing.touchdown_point`
- `landing.heading_deg`
- `landing.approach_alt_m`
- `landing.glide_slope_deg`

For the default field:

- glide slope: `3°`
- approach altitude: `30m`
- derived distance: about `572.4m`
- theoretical value: about `573m`

### Procedural scan geometry

The scan path is generated from:

- boundary polygon
- scan spacing
- scan heading

Validated result:

- `10 waypoints`
- `5 sweeps`
- `200m spacing`

### Procedural takeoff geometry

Takeoff points are generated from runway facts rather than static mission items.

### Mission-progress observability

After link startup, Striker explicitly requests:

- `MISSION_CURRENT`
- `MISSION_ITEM_REACHED`

so scan/enroute and attack-run progression do not depend on MAVProxy default stream behavior.

### Override handover behavior

The override validation injects MANUAL mode over MAVLink, then verifies:

- `Autonomy relinquished`
- `Human override`
- no `Payload released (native DO_SET_SERVO)`
- no `Mission completed successfully!`

## Expected Log Milestones

In the preserved `striker.log` you should see:

### Normal vision path

- `Landing approach derived`
- `Boustrophedon scan generated`
- `Takeoff geometry generated`
- `Preflight: mission uploaded`
- `Target altitude reached`
- `Scan complete`
- `Using vision drop point`
- `Attack mission uploaded`
- `Attack run initiated`
- `Payload released (native DO_SET_SERVO)`
- `Landing detected`
- `Mission completed successfully!`

### Fallback path

- `Using fallback midpoint drop point`
- `Attack mission uploaded`
- `Payload released (native DO_SET_SERVO)`
- `Landing detected`
- `Mission completed successfully!`

### Override path

- `Autonomy relinquished`
- `Human override`
- no completion milestone after the handover

## Known Fixes Applied During Validation

### 1. Landing mission seq bug

A bug in `src/striker/flight/navigation.py` caused landing items to keep old sequence numbers, which made SITL repeatedly re-request item 13.

Fix: re-sequence landing items before appending them into the built mission.

### 2. Wrong defaults path

Older docs referenced a nonexistent `default_params/plane.parm` path.

### 3. Wrong SITL home

Using default Canberra home invalidated local field validation because the aircraft started on the wrong map.

### 4. Wrong transport mode

If `STRIKER_TRANSPORT=udp` is not set, Striker tries to open `/dev/serial0` and fails in SITL.

### 5. Missing mission-progress streams

If `MISSION_CURRENT` / `MISSION_ITEM_REACHED` are not requested explicitly after startup, scan and attack-run progression can stall even while the aircraft continues flying.

### 6. Stale vision publisher contamination

The fallback path must not share a fixed vision TCP port. The integration harness now allocates a per-run vision socket so stale mock-vision publishers cannot reconnect and silently convert fallback coverage into the vision path.

### 7. Short override runs dropping recorder output

The flight recorder now flushes each sample so `flight_log.csv` is preserved even when the override path terminates the run quickly after the handover event.

## Troubleshooting

### `No module named striker.main`

Use:

```bash
python -m striker
```

Not:

```bash
python -m striker.main
```

### `could not open port /dev/serial0`

Set:

```bash
STRIKER_TRANSPORT=udp
```

### Fallback unexpectedly uses a vision drop point

Check whether a stale external vision publisher is still reconnecting. The integration harness isolates its own port per run, but manual validation can still be contaminated by unrelated clients.

### `PANIC: Failed to load defaults`

Check:

- defaults path exists
- use `Tools/autotest/models/plane.parm`
- `sitl_merged.param` path is correct

### Wrong aircraft location

Check SITL log for:

```text
Home: 30.261000 120.095000
```

If you see Canberra coordinates, restart SITL with the correct `--home`.
