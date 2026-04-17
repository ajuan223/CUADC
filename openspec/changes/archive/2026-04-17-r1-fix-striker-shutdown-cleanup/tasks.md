## 1. Shutdown sequencing

- [x] 1.1 Verify `src/striker/app.py` preserves the required cleanup order: stop FSM/monitors/recorder, stop vision receiver, then disconnect MAVLink
- [x] 1.2 Tighten shutdown coordination so intentional teardown state is available to monitor loops that might still be mid-cycle

## 2. Monitor stop behavior

- [x] 2.1 Update `src/striker/comms/heartbeat.py` so `stop()` wakes blocked waits and prevents shutdown-induced heartbeat timeout logs
- [x] 2.2 Update the safety monitoring path so intentional shutdown cannot emit false emergency or safety-failure events during teardown

## 3. Regression coverage

- [x] 3.1 Extend shutdown tests to cover prompt monitor termination and absence of false fault emission after stop
- [x] 3.2 Run targeted shutdown tests to confirm clean `Ctrl+C`-style exit behavior
