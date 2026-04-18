# vision-receiver

## Requirements

- REQ-VISION-001: VisionReceiver Protocol with start/stop/get_latest methods
- REQ-VISION-002: TCP receiver shall accept JSON coordinate messages
- REQ-VISION-003: UDP receiver shall accept JSON coordinate messages
- REQ-VISION-004: Message format: {"lat": float, "lon": float, "confidence": float}
- REQ-VISION-005: GpsDropPoint validation: lat [-90, 90], lon [-180, 180]
- REQ-VISION-006: Invalid coordinates rejected with WARNING log
- REQ-VISION-007: Receiver selection via config (tcp/udp)

## Updated Requirement Detail

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
