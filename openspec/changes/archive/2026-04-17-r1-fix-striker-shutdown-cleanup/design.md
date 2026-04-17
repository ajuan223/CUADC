## Context

Striker already routes `SIGINT`/`SIGTERM` into an app-level shutdown path in `src/striker/app.py`, and the current orchestration stops `fsm`, `heartbeat_monitor`, `safety_monitor`, `recorder`, `vision_receiver`, then disconnects MAVLink. However, the background monitor tasks are still built around blocking waits (`asyncio.wait_for()` in the heartbeat watchdog, periodic safety checks in `SafetyMonitor.run()`), so stopping them by only flipping `_running = False` can still allow one more timeout/fault cycle after shutdown has begun. The design needs to make shutdown deterministic: background loops must stop promptly, must not emit false faults during intentional teardown, and must release shared resources before exit.

## Goals / Non-Goals

**Goals:**
- Guarantee operator-triggered shutdown stops monitor loops before MAVLink teardown is treated as a fault.
- Make heartbeat and safety loops exit promptly once shutdown begins, without waiting for another timeout window.
- Prevent shutdown-induced `Heartbeat timeout`, `Safety check failed`, or emergency transitions.
- Preserve idempotent cleanup behavior and regression-test the shutdown path.

**Non-Goals:**
- Redesigning the full app lifecycle around a new supervisor framework.
- Changing mission-state behavior unrelated to intentional shutdown.
- Introducing new external dependencies or process managers.

## Decisions

- Keep app-level orchestration in `src/striker/app.py`, with the shutdown sequence remaining: stop FSM and monitors, stop recorder/vision receiver, then disconnect MAVLink.
  - Alternative considered: disconnect first and rely on task cancellation. Rejected because shared-resource teardown before loop stop recreates the original race and contradicts the current explicit-stop architecture.
- Make `HeartbeatMonitor.stop()` actively wake internal waiters so the sender/watchdog coroutines exit immediately instead of sleeping until the next timeout.
  - Alternative considered: accept a final timeout log after shutdown. Rejected because the user requirement is clean `Ctrl+C` exit without false errors or emergency side effects.
- Treat intentional shutdown as a suppressor for safety escalation: once shutdown begins, monitor loops must not publish new unhealthy/emergency signals derived from the teardown itself.
  - Alternative considered: only reorder shutdown calls. Rejected because ordering alone does not eliminate races when a loop is already blocked inside a wait or midway through a check cycle.
- Keep verification focused on app shutdown orchestration and monitor behavior, with unit tests around `_shutdown_app()`, `_shutdown_watcher()`, and monitor stop semantics.
  - Alternative considered: only test the happy-path cleanup calls. Rejected because the regression is caused by timing/race behavior, not missing method invocations.

## Risks / Trade-offs

- [Hidden race remains in monitor internals] → Wake blocked waits explicitly and assert no post-stop fault emission in tests.
- [Shutdown logic becomes split across components] → Keep the app responsible for sequencing and the monitors responsible only for prompt self-termination.
- [Tests become timing-sensitive] → Use direct coroutine control and mocks rather than real sleeps where possible.

## Migration Plan

1. Tighten monitor stop semantics so stop requests unblock internal waits.
2. Add regression tests for shutdown ordering and no-false-fault behavior.
3. Re-run targeted shutdown tests before any broader SITL verification.

## Open Questions

- Whether a shared `shutdown_event` should be threaded into monitor implementations, or whether local wake-up events in each monitor are sufficient.
- Whether any additional recorder or vision tasks also need explicit wake-up behavior beyond their current stop paths.
