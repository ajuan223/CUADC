# app-main-loop

## Requirements

- REQ-APP-001: Load and validate FieldProfile at startup (RL-08)
- REQ-APP-002: Refuse launch on invalid FieldProfile
- REQ-APP-003: Initialize all subsystems with dependency injection
- REQ-APP-004: Create MissionContext with all subsystem references
- REQ-APP-005: Launch async tasks via asyncio.TaskGroup
- REQ-APP-006: --field CLI argument for field profile selection
- REQ-APP-007: Graceful shutdown on SIGINT/SIGTERM
- REQ-APP-008: Structured logging of startup sequence
