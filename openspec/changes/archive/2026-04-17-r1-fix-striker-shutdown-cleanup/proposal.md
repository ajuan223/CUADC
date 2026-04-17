## Why

Striker does not shut down cleanly on `Ctrl+C`: the app disconnects the MAVLink connection before heartbeat and safety background loops have stopped, so those loops misinterpret operator-initiated shutdown as a comms failure. This produces repeated shutdown errors, false emergency transitions, and can block reliable interrupt-driven exit during iterative SITL or field testing.

## What Changes

- Define a coordinated shutdown flow for operator-initiated termination.
- Require heartbeat and safety monitoring loops to stop before the MAVLink connection is disconnected.
- Require shutdown-in-progress state to suppress false heartbeat timeout and safety-failure escalation caused by intentional disconnect.
- Require background loops involved in monitoring and cleanup to terminate promptly once shutdown begins.
- Add shutdown-focused verification covering `Ctrl+C` exit, monitor shutdown ordering, and absence of shutdown-induced emergency transitions.

## Capabilities

### New Capabilities
- `graceful-shutdown`: Coordinated shutdown behavior for the Striker app, including monitor stop ordering, connection teardown, and suppression of false fault handling during intentional shutdown.

### Modified Capabilities
<!-- none -->

## Impact

- Affected code: `src/striker/app.py`, `src/striker/comms/heartbeat.py`, `src/striker/comms/connection.py`, and the safety monitoring implementation
- Likely affected tests: app lifecycle, interrupt handling, and shutdown/monitor coordination tests
- Operator impact: `Ctrl+C` becomes a reliable way to stop Striker without shutdown log storms or false emergency behavior
