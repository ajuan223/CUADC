# fsm-engine

## Requirements

- REQ-FSM-001: MissionStateMachine shall register states in a dict with string keys
- REQ-FSM-002: process_event shall delegate to current state's handle method
- REQ-FSM-003: Global interceptor: OverrideEvent → OVERRIDE from any state (RL-03)
- REQ-FSM-004: Global interceptor: EmergencyEvent → EMERGENCY from any state
- REQ-FSM-005: State transitions shall call old.on_exit() → new.on_enter() in order
- REQ-FSM-006: All transitions shall be logged via structlog
- REQ-FSM-007: BaseState ABC shall define on_enter/execute/on_exit lifecycle
- REQ-FSM-008: MissionContext shall hold shared mutable state and subsystem references
- REQ-FSM-009: Events shall be typed (enum + dataclasses), not raw strings
- REQ-FSM-010: python-statemachine library used with rtc=False for async support
