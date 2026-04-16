# payload-release

## Requirements

- REQ-RELEASE-001: ReleaseController Protocol with async trigger() method
- REQ-RELEASE-002: MAVLink channel: DO_SET_SERVO with COMMAND_ACK verification
- REQ-RELEASE-003: GPIO channel: gpiod direct drive with configurable pin
- REQ-RELEASE-004: Channel selection via config.json release_method field
- REQ-RELEASE-005: DRY_RUN mode: all release actions skipped + logged
- REQ-RELEASE-006: ACK verification loop filtering for correct command ID
