## Context

R2 addresses a safety-critical gap in Striker’s override handling. The current codebase detects manual-mode changes in `SafetyMonitor` and sends an `OverrideEvent` into the FSM, but command-producing paths remain distributed across `FlightController`, mission upload, and payload release code. That means manual takeover can race with in-flight autonomous command emission. Current ArduPilot documentation describes MANUAL mode as handing control to direct RC/servo behavior, and current MAVLink documentation still relies on custom mode switching via `MAV_CMD_DO_SET_MODE` with `MAV_MODE_FLAG_CUSTOM_MODE_ENABLED`, so once the vehicle is in a pilot-takeover mode the companion should yield rather than keep trying to command around it.

## Goals / Non-Goals

**Goals:**
- Make pilot/manual takeover the highest-priority authority in the runtime.
- Permanently disable autonomous command emission after override is detected in a run.
- Ensure the FSM transitions to terminal override handling immediately and does not resume autonomous behavior.
- Cover command-producing code paths with regression tests so override cannot silently regress.

**Non-Goals:**
- Changing ArduPilot FC parameters or RC mapping.
- Implementing low-level RC stick decoding in Striker.
- Redesigning heartbeat/safety infrastructure beyond what is needed for hard preemption.

## Decisions

- Introduce a persistent autonomy-control lock at the connection/control layer, not just in the FSM state machine.
  - Alternative considered: rely only on the FSM reaching `override`. Rejected because asynchronous state handlers and helper modules outside the FSM can still emit commands unless command paths are explicitly gated.
- Treat manual takeover as both an event-driven and command-gating concern: once override is observed, future command paths must fail closed.
  - Alternative considered: block only after the FSM fully enters `override`. Rejected because a race can exist between detection and later FSM settling.
- Use the same manual takeover mode family already recognized by safety monitoring (`MANUAL`, `STABILIZE`, `FBWA`) as the immediate guardrail for command suppression.
  - Alternative considered: only suppress when a separate override flag is set. Rejected because direct flight mode knowledge provides an earlier and more explicit indicator of pilot control.
- Gate every autonomous command-producing path that can materially affect the aircraft: flight mode/mission/navigation commands, mission upload, and payload release.
  - Alternative considered: only guard `FlightController`. Rejected because mission upload and payload release bypass it today.

## Risks / Trade-offs

- [Some command path remains ungated] → Audit every outbound command-producing module and add regression tests around the known paths.
- [False positives block valid autonomous startup] → Allow autonomous control until a recognized manual takeover mode or explicit override lock is present.
- [Override lock is difficult to reset] → Make the lock intentionally one-way for a run; recovery belongs to an explicit restart, not automatic re-entry.

## Migration Plan

1. Add a persistent autonomy lock and manual-mode guard in the control/connection layer.
2. Wire FSM override handling to trip the autonomy lock immediately.
3. Guard all autonomous command-producing modules.
4. Add tests for override-triggered command suppression and rerun targeted unit coverage.

## Open Questions

- Whether future work should also suppress heartbeat-like non-command traffic after override, or only command/control messages.
- Whether additional manual-takeover modes beyond `MANUAL`, `STABILIZE`, and `FBWA` should become configurable once field behavior is validated.
