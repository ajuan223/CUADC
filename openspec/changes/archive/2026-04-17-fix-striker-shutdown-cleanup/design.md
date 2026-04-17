## Context

Striker starts multiple long-lived async subsystems from `src/striker/app.py`, then relies on a signal-triggered shutdown watcher to stop them. The current shutdown path only stops the FSM, flight recorder, and MAVLink connection, leaving other tasks and transports without an explicit stop path. This is especially visible in the vision receiver, whose TCP/UDP listener may keep the configured port bound after the operator presses `Ctrl+C`.

## Goals / Non-Goals

**Goals:**
- Make `SIGINT`/`SIGTERM` stop every subsystem created by the app main loop.
- Ensure vision receiver transports are explicitly closed before process exit.
- Ensure background loops terminate cleanly during shutdown instead of relying on process death.
- Add tests that prove shutdown releases the configured vision port.

**Non-Goals:**
- Changing mission-state behavior unrelated to process shutdown.
- Adding a new process supervisor or external lifecycle manager.
- Changing the user-facing vision protocol or port configuration model.

## Decisions

- Introduce a complete app-level shutdown sequence in `src/striker/app.py` that stops all started subsystems, including heartbeat monitor, safety monitor, vision receiver, and recorder, then disconnects MAVLink as the final transport cleanup step.
  - Alternative considered: rely on `asyncio.TaskGroup` cancellation alone. Rejected because several loops are controlled by internal `_running` flags and the app already exposes explicit `stop()` methods that should own resource release.
- Make background loops shutdown-aware instead of unconditional `while True` loops.
  - Alternative considered: cancel the tasks externally without changing loop conditions. Rejected because explicit shutdown conditions make cleanup deterministic and easier to test.
- Keep receiver-level cleanup in the receiver implementations (`TcpReceiver.stop()`, `UdpReceiver.stop()`), while the app is responsible for calling them during shutdown.
  - Alternative considered: let receiver internals depend on garbage collection or connection teardown side effects. Rejected because socket release must be deterministic.
- Add lifecycle tests around app shutdown and receiver cleanup rather than only unit-testing helper methods.
  - Alternative considered: test only receiver `stop()` in isolation. Rejected because the bug occurs in app orchestration, not just receiver internals.

## Risks / Trade-offs

- [Shutdown ordering bug] → Stop producer/consumer loops before disconnecting the shared MAVLink connection so tasks do not keep touching torn-down resources.
- [Hanging shutdown] → Ensure all loops observe a stop condition and receiver `stop()` awaits server closure.
- [Test flakiness around ports] → Use ephemeral test ports or controlled per-test port values and verify bind/rebind behavior directly.
