# vision-receiver

## Requirements

- REQ-VISION-001: VisionReceiver Protocol with start/stop/get_latest methods
- REQ-VISION-002: TCP receiver shall accept JSON coordinate messages
- REQ-VISION-003: UDP receiver shall accept JSON coordinate messages
- REQ-VISION-004: Message format: {"lat": float, "lon": float, "confidence": float}
- REQ-VISION-005: GpsTarget validation: lat [-90, 90], lon [-180, 180]
- REQ-VISION-006: Invalid coordinates rejected with WARNING log
- REQ-VISION-007: Receiver selection via config (tcp/udp)
