## 1. App shutdown orchestration

- [x] 1.1 Update `src/striker/app.py` shutdown flow to stop every started subsystem, including heartbeat monitor, safety monitor, vision receiver, recorder, and FSM, before final disconnect
- [x] 1.2 Make background app loops exit on shutdown instead of running as unconditional infinite loops
- [x] 1.3 Add a shutdown-safe cleanup path in `src/striker/app.py` that still releases resources if startup or task execution raises

## 2. Vision receiver cleanup

- [x] 2.1 Verify and tighten `TcpReceiver.stop()` so the listening server is fully closed before shutdown completes
- [x] 2.2 Verify and tighten `UdpReceiver.stop()` so the bound datagram transport is fully closed before shutdown completes

## 3. Regression coverage

- [x] 3.1 Add tests covering graceful shutdown on signal-triggered app stop
- [x] 3.2 Add tests proving a stopped vision receiver releases its configured port for immediate reuse
- [x] 3.3 Run targeted tests for app lifecycle and vision receiver shutdown behavior
