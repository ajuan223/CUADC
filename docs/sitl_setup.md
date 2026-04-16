# SITL Setup Guide

## Overview

This project now validates the **field-driven procedural mission generation** flow against ArduPlane SITL. The simulated aircraft starts from the configured field location, receives a procedurally generated full mission, completes scan, uploads an attack mission, releases payload, and enters landing.

## Validated Mission Chain

```text
INIT → PREFLIGHT → TAKEOFF → SCAN → ENROUTE → RELEASE → LANDING
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

### 1. Start ArduPlane SITL

```bash
/home/xbp/ardupilot/build/sitl/bin/arduplane \
  -w --model plane --speedup 1 -I 0 \
  --home 30.2610,120.0950,0,180 \
  --defaults /home/xbp/dev-zju/cuax-autodriv/data/fields/sitl_default/sitl_merged.param \
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
  --daemon \
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
/home/xbp/dev-zju/cuax-autodriv/.venv/bin/python -m striker \
  &>/tmp/striker.log
```

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

## Expected Log Milestones

In `/tmp/striker.log` you should see:

- `Landing approach derived`
- `Boustrophedon scan generated`
- `Takeoff geometry generated`
- `Mission upload complete`
- `Vehicle armed`
- `FSM transition` to `scan`
- later `FSM transition` to `enroute`
- `Attack mission uploaded`
- `Payload released (native DO_SET_SERVO)`
- `FSM transition` to `landing`

## Latest Validation Result

Latest successful SITL verification covered:

- full mission upload: `16 items`
- attack mission upload: `8 items`
- successful state chain:
  ```text
  INIT → PREFLIGHT → TAKEOFF → SCAN → ENROUTE → RELEASE → LANDING
  ```
- landing sequence trigger after payload release

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

### `address already in use` on 9876

Kill old Striker processes:

```bash
pkill -9 -f 'python.*striker'
```

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
