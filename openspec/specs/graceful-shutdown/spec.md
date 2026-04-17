# graceful-shutdown Specification

## Purpose
TBD - created by archiving change r1-fix-striker-shutdown-cleanup. Update Purpose after archive.
## Requirements
### Requirement: Operator shutdown MUST stop monitors before transport teardown
The system MUST treat operator-initiated shutdown as a coordinated sequence that stops autonomous control and monitoring loops before disconnecting the shared MAVLink connection.

#### Scenario: Ctrl+C triggers ordered cleanup
- **WHEN** the operator sends `SIGINT` or `SIGTERM` while Striker is running
- **THEN** the app MUST stop the FSM, heartbeat monitor, safety monitor, and recorder before disconnecting the MAVLink connection

#### Scenario: Vision receiver cleanup participates in shutdown
- **WHEN** app shutdown begins
- **THEN** the vision receiver MUST be stopped before process exit completes

### Requirement: Monitor stop MUST be prompt and fault-free
Background monitors MUST exit promptly after stop is requested and MUST NOT emit heartbeat-loss, safety-failure, or emergency signals caused only by intentional shutdown.

#### Scenario: Heartbeat watchdog is waiting during shutdown
- **WHEN** `HeartbeatMonitor.stop()` is called while the watchdog is blocked waiting for a heartbeat
- **THEN** the watchdog MUST exit without logging a heartbeat timeout caused by the shutdown itself

#### Scenario: Safety monitor is active during shutdown
- **WHEN** shutdown begins while the safety monitor is still running
- **THEN** the safety monitor MUST stop without publishing new emergency events caused solely by connection teardown

### Requirement: Shutdown cleanup MUST remain idempotent
The app shutdown helper MUST be safe to call multiple times and MUST only execute resource cleanup once.

#### Scenario: Re-entrant shutdown call
- **WHEN** `_shutdown_app()` is called after cleanup has already started
- **THEN** it MUST return without stopping subsystems or disconnecting the connection a second time

### Requirement: Signal-driven shutdown MUST complete cleanly
The application MUST support `Ctrl+C` exit without leaving background tasks producing shutdown log storms or transitioning the FSM into emergency because of intentional teardown.

#### Scenario: Shutdown watcher handles operator interrupt
- **WHEN** the shutdown watcher observes the app shutdown event
- **THEN** it MUST invoke the coordinated cleanup path and allow the process to exit cleanly

#### Scenario: No false emergency during interrupt exit
- **WHEN** the operator interrupts the app during normal operation
- **THEN** shutdown logs MUST NOT include safety-failure or shutdown-induced emergency transitions caused by the intentional disconnect

