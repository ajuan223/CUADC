# comms-mavlink-adapter

## Requirements

- REQ-COMMS-001: MAVLinkConnection shall support serial and UDP transport
- REQ-COMMS-002: Connection shall wait for first HEARTBEAT before reporting CONNECTED
- REQ-COMMS-003: Async rx_loop shall use recv_match(blocking=False) with yield sleep
- REQ-COMMS-004: Message dispatch via asyncio.Queue for consumer decoupling
- REQ-COMMS-005: Heartbeat watchdog shall detect connection loss within configurable timeout (default 3s)
- REQ-COMMS-006: All pymavlink imports confined to comms/ package (RL-04)
- REQ-COMMS-007: Telemetry data parsed to typed dataclasses immediately at reception
- REQ-COMMS-008: Connection state machine: DISCONNECTED → CONNECTING → CONNECTED → LOST
- REQ-COMMS-009: Periodic heartbeat transmission at configurable rate (default 1Hz)
- REQ-COMMS-010: send_command_long wrapper with ACK verification and timeout
