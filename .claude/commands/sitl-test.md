---
name: "SITL Full-Chain Test"
description: Launch ArduPlane SITL + MAVProxy + Striker full-chain integration test for a given field profile
category: Testing
tags: [sitl, integration, full-chain]
---

Launch the full SITL simulation stack and run Striker against a field profile.

**Input**: The argument after `/sitl-test` is the field name (e.g. `zjg`, `sitl_default`). Defaults to `sitl_default` if omitted.

**Prerequisites**
- ArduPlane SITL binary built: `~/ardupilot/build/sitl/bin/arduplane`
- Project venv exists: `.venv/bin/mavproxy.py` and `.venv/bin/python`
- Field profile exists: `data/fields/<field>/field.json` + `data/fields/<field>/sitl_merged.param`
- No leftover processes on ports 5760, 5501, 14550, 14551

**Steps**

1. **Determine field name**
   - Use provided argument, or default to `sitl_default`
   - Verify `data/fields/<field>/field.json` exists; abort if missing

2. **Kill residual processes**
   ```bash
   pkill -9 -f arduplane; pkill -9 -f mavproxy
   ```
   Wait until ports 5760, 5501, 14550, 14551 are all free (`ss -tlnup | grep -E '5760|5501|14550|14551'`).

3. **Compute field geometry** (read from field.json via Python)
   - Home string: `touchdown.lat, touchdown.lon, touchdown.alt, landing.heading`
   - Param file: `data/fields/<field>/sitl_merged.param`

4. **Launch SITL** (terminal 1 / background process)
   ```bash
   ~/ardupilot/build/sitl/bin/arduplane \
     -w --model plane --speedup 1 -I 0 \
     --home "<HOME_STRING>" \
     --defaults data/fields/<field>/sitl_merged.param \
     --defaults ~/ardupilot/Tools/autotest/models/plane.parm \
     --sim-address=127.0.0.1
   ```
   Monitor: wait for `bind port 5760 for SERIAL0` in stdout → TCP 5760 open.

5. **Launch MAVProxy** (terminal 2 / background process, after SITL binds 5760)
   ```bash
   .venv/bin/mavproxy.py \
     --master tcp:127.0.0.1:5760 \
     --sitl 127.0.0.1:5501 \
     --out udp:127.0.0.1:14550 \
     --out udp:127.0.0.1:14551 \
     --daemon
   ```
   Critical flags:
   - `--sitl 127.0.0.1:5501`: **MANDATORY** — bridges SITL sim packets (FG protocol). Without this, SITL hangs at "Smoothing reset" and never sends heartbeats.
   - `--out udp:` prefix: **MANDATORY** — `udp:` prefix required for Striker UDP transport. Bare `127.0.0.1:14550` opens a TCP listener which breaks Striker's MAVLink UDP connection.
   - `--daemon`: run headless without interactive console.

   Monitor: wait for heartbeat log in MAVProxy output → SITL should print `validate_structures` and `Loaded defaults`.

6. **Launch Striker** (terminal 3 / background process, after MAVProxy heartbeat confirmed)
   ```bash
   STRIKER_TRANSPORT=udp \
   STRIKER_MAVLINK_URL=udp:127.0.0.1:14550 \
   STRIKER_ARM_FORCE_BYPASS=1 \
   STRIKER_DRY_RUN=true \
   .venv/bin/python -m striker --field <field>
   ```
   Environment variables:
   - `STRIKER_TRANSPORT=udp`: connect via UDP
   - `STRIKER_MAVLINK_URL=udp:127.0.0.1:14550`: MAVProxy output port
   - `STRIKER_ARM_FORCE_BYPASS=1`: skip arming checks for SITL
   - `STRIKER_DRY_RUN=true`: no actual servo release
   - Remove `STRIKER_DRY_RUN` for live payload release test.

   Monitor: wait for `Striker starting` → `Preflight complete` → state transitions.

7. **Monitor flight**
   - Watch Striker logs for state machine transitions: `takeoff → scan → enroute → release → landing → completed`
   - Check `flight_log.csv` for altitude/position sanity (no uncommanded descents)
   - If testing with vision: start `scripts/mock_vision_server.py` on the vision port

8. **Cleanup** (when done or on failure)
   ```bash
   pkill -f "python -m striker"
   pkill -f mavproxy
   pkill -f arduplane
   ```

**Port Map**

| Port  | Protocol | Direction              | Service           | Description                     |
|-------|----------|------------------------|-------------------|---------------------------------|
| 5760  | TCP      | SITL ← MAVProxy       | SITL SERIAL0      | MAVLink command & control       |
| 5501  | UDP      | SITL ↔ MAVProxy       | FG protocol       | Sim data bridge (**critical**)  |
| 14550 | UDP      | MAVProxy → Striker    | UDP output        | Striker MAVLink telemetry       |
| 14551 | UDP      | MAVProxy → GCS/extra  | UDP output        | Secondary (e.g. QGroundControl) |

**Common Failures**

| Symptom | Cause | Fix |
|---------|-------|-----|
| SITL hangs at "Smoothing reset" | Missing `--sitl` flag on MAVProxy | Add `--sitl 127.0.0.1:5501` |
| "bind failed on port 5760" | Residual arduplane process | `pkill -9 -f arduplane` |
| Striker can't connect | MAVProxy `--out` missing `udp:` prefix | Use `--out udp:127.0.0.1:14550` |
| Crash during takeoff (steep bank → dive) | `TKOFF_ALT` > scan altitude | Lower `TKOFF_ALT` to match scan alt in `sitl_merged.param` |
| SITL exits after param load | `MIS_TOTAL > 0` with no items | Set `MIS_TOTAL=0` in `sitl_merged.param` |
| MAVProxy exits immediately | SITL not yet ready on 5760 | Wait for `bind port 5760` before launching MAVProxy |

**Speedup**
- Change `--speedup 1` to `--speedup 2` or `3` to run sim faster. Test with `--speedup 1` first to confirm stability.
