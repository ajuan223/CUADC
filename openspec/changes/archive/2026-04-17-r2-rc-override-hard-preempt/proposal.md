## Why

The current RC override handling is only a placeholder: detecting a manual takeover is not enough if the autonomous stack can still keep sending mode changes, mission commands, or release actions after the pilot has taken control. In ArduPlane, MANUAL hands control back to direct RC/servo behavior, so Striker must hard-yield immediately and never continue issuing autonomous commands once human takeover starts.

## What Changes

- Define a hard preemption path for RC/manual takeover that permanently relinquishes autonomous control for the rest of the run.
- Persistently lock out autonomous command send paths after override so flight control, mission upload, and payload release logic cannot continue issuing commands.
- Treat manual takeover modes as highest-priority authority and ensure the FSM transitions into terminal override handling immediately.
- Add regression coverage proving that once override/manual takeover is detected, the program does not send further autonomous commands.
- Capture the current ArduPilot/MAVLink behavior relevant to MANUAL mode and mode-setting acknowledgments in the design/spec artifacts so the implementation stays aligned with current docs.

## Capabilities

### New Capabilities
- `rc-override-hard-preempt`: Hard-yield behavior that permanently disables autonomous command emission once RC/manual takeover is detected and transitions the app into override handling.

### Modified Capabilities
<!-- none -->

## Impact

- Affected code: `src/striker/safety/monitor.py`, `src/striker/core/machine.py`, `src/striker/flight/controller.py`, mission upload/release command paths, and related tests
- Runtime impact: after manual takeover, Striker stops issuing autonomous commands instead of competing with the pilot
- Operator impact: RC/manual control becomes authoritative immediately, reducing the chance of command fights, unsafe mode flips, or unwanted release/navigation actions
