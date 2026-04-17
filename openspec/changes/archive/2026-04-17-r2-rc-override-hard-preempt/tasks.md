## 1. Override preemption contract

- [x] 1.1 Add a persistent autonomy-control lock that trips when override/manual takeover is detected
- [x] 1.2 Wire FSM override processing to disable autonomous control immediately for the current run

## 2. Command gating

- [x] 2.1 Guard `FlightController` command paths so manual takeover blocks further autonomous control messages
- [x] 2.2 Guard mission upload and payload release paths so they fail closed after override instead of sending MAVLink commands
- [x] 2.3 Use recognized manual takeover modes as an immediate command-blocking signal even before later state transitions settle

## 3. Regression coverage

- [x] 3.1 Add tests proving override processing disables autonomy and blocks outbound control commands
- [x] 3.2 Run targeted unit tests for override, flight control, mission upload, and related state-machine behavior
