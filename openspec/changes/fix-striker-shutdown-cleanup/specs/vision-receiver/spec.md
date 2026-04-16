## MODIFIED Requirements

### Requirement: VisionReceiver Protocol with start/stop/get_latest methods
Vision receiver implementations SHALL provide `start()`, `stop()`, and `get_latest()` methods, and `stop()` SHALL deterministically release any bound server or transport owned by the receiver.

#### Scenario: TCP receiver is stopped during shutdown
- **WHEN** the application calls `stop()` on a started TCP receiver
- **THEN** the receiver closes its listening server
- **AND** the previously bound host/port becomes available for reuse

#### Scenario: UDP receiver is stopped during shutdown
- **WHEN** the application calls `stop()` on a started UDP receiver
- **THEN** the receiver closes its datagram transport
- **AND** the previously bound host/port becomes available for reuse
