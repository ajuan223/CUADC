# SITL Setup Guide

## Overview

This project validates the **preburned mission + GUIDED takeover** flow against ArduPlane SITL. The simulated aircraft starts from the configured field location, executes a preburned full mission (takeoff → scan → loiter → landing), Striker downloads the mission, monitors scan progress, then takes over in GUIDED mode for the strike run before handing back to AUTO for landing.

## Validated Mission Chains

```text
Normal vision path:
INIT → STANDBY → SCAN_MONITOR → GUIDED_STRIKE → RELEASE_MONITOR → LANDING_MONITOR → COMPLETED

Fallback path:
INIT → STANDBY → SCAN_MONITOR → GUIDED_STRIKE(fallback_drop_point) → RELEASE_MONITOR → LANDING_MONITOR → COMPLETED

Override path:
INIT → STANDBY → SCAN_MONITOR → OVERRIDE
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

### Preburned Mission Parsing

The system reads the preburned mission from the flight controller and identifies the start of the scan (LOITER_UNLIM) and landing (DO_LAND_START) sequences.

Validated result:

- Mission correctly downloaded
- `loiter_seq` correctly parsed
- `landing_start_seq` correctly parsed

### Mission-progress observability

After link startup, Striker explicitly requests:

- `MISSION_CURRENT`
- `MISSION_ITEM_REACHED`

so the progression of GUIDED_STRIKE does not depend on MAVProxy default stream behavior.

### Override handover behavior

The override validation injects MANUAL mode over MAVLink, then verifies:

- `Autonomy relinquished`
- `Human override`
- no `Payload released (native DO_SET_SERVO)`
- no `Mission completed successfully!`

## Expected Log Milestones

In the preserved `striker.log` you should see:

### Normal vision path

- `Preburned mission validated`
- `Reached loiter seq`
- `Starting guided strike`
- `Phase: APPROACH`
- `Phase: STRIKE`
- `Payload released (native DO_SET_SERVO)`
- `Guided strike completed`
- `Mission completed successfully!`

### Fallback path

- `Using fallback_field drop point`
- `Starting guided strike`
- `Payload released (native DO_SET_SERVO)`
- `Guided strike completed`
- `Mission completed successfully!`

### Override path

- `Autonomy relinquished`
- `Human override`
- no completion milestone after the handover

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
