## Why

Striker currently does not shut down cleanly on `SIGINT`/`SIGTERM`: some async tasks keep running and the vision receiver socket can remain bound after the operator tries to stop the process. This makes iterative SITL and LAN integration work unreliable because a stopped session may still occupy the configured vision port.

## What Changes

- Ensure shutdown stops every long-running subsystem started by the app main loop, not just the FSM, recorder, and MAVLink connection.
- Ensure the vision receiver is explicitly closed during shutdown so its listening port is released.
- Ensure background dispatch loops terminate when shutdown begins instead of running forever.
- Add shutdown-focused tests covering signal-triggered termination and port release behavior.

## Capabilities

### New Capabilities
<!-- none -->

### Modified Capabilities
- `app-main-loop`: graceful shutdown must stop all launched subsystems and wait for cleanup before process exit.
- `vision-receiver`: receiver implementations must release their bound transport/server during application shutdown.

## Impact

- Affected code: `src/striker/app.py`, `src/striker/vision/tcp_receiver.py`, `src/striker/vision/udp_receiver.py`
- Likely affected tests: app lifecycle / integration tests around shutdown behavior
- Operator impact: `Ctrl+C` becomes a reliable way to stop Striker without leaving the vision port occupied
