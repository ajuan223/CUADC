import re

def rewrite():
    try:
        with open('tasks.md', 'r') as f:
            content = f.read()
    except FileNotFoundError:
        print("tasks.md not found.")
        return

    # Add geopy/pymavlink context query
    content = content.replace(
        "### 3.1 Package Scaffold\n\n- [ ] 3.1.1 Create",
        "### 3.1 Package Scaffold\n\n- [ ] 3.1.0 Use Context7 MCP to query `pymavlink` and `geopy` documentation for best practices\n- [ ] 3.1.1 Create"
    )

    # Change ConnectionError to MavlinkConnectionError
    content = content.replace(
        "`ConnectionError`",
        "`MavlinkConnectionError`"
    )

    # Add phase 3 Verification & Commit
    content = content.replace(
        "\n---\n\n## Phase 4",
        "\n### 3.10 Phase 3 Verification & Commit\n\n- [ ] 3.10.1 Run incremental unit tests for all Phase 3 modules (`pytest tests/unit/test_connection.py`, etc.)\n- [ ] 3.10.2 Perform full project dry-run for Phase 3 components.\n- [ ] 3.10.3 IF BUG DETECTED: Insert debug iteration block, fix bugs until dry-run passes.\n- [ ] 3.10.4 Git Commit Phase 3 changes with message: `feat(comms): 完成阶段3 MAVLink底层通信模块实现与基本SITL集成`\n\n---\n\n## Phase 4"
    )

    # Add context7 query for python-statemachine + update FSM section
    content = content.replace(
        "### 4.5 FSM Engine\n\n- [ ] 4.5.1 Create",
        "### 4.5 FSM Engine\n\n- [ ] 4.5.0 Use Context7 MCP to query `python-statemachine` declarative syntax and edge cases\n- [ ] 4.5.1 Create"
    )

    # Rewrite FSM Engine list
    fsm_engine_old = """- [ ] 4.5.2 Implement state registration dict in MissionStateMachine
- [ ] 4.5.3 Implement `register_state(name, state)` method
- [ ] 4.5.4 Implement `process_event(event)` with current state delegation
- [ ] 4.5.5 Implement global interceptor for OverrideEvent → OVERRIDE state
- [ ] 4.5.6 Implement global interceptor for EmergencyEvent → EMERGENCY state
- [ ] 4.5.7 Implement transition execution: old.on_exit() → new.on_enter()
- [ ] 4.5.8 Implement transition logging via structlog
- [ ] 4.5.9 Implement `async run()` main loop with event processing
- [ ] 4.5.10 Implement `current_state` property"""

    fsm_engine_new = """- [ ] 4.5.2 Define `MissionStateMachine` using `python-statemachine` declarative syntax (`State`, `Event`)
- [ ] 4.5.3 Set `rtc=False` on the state machine to prevent run-to-completion deadlocks in async contexts
- [ ] 4.5.4 Support delayed initialization explicitly via `activate_initial_state()` integration
- [ ] 4.5.5 Implement global transition handlers via `python-statemachine` event hooks for OverrideEvent / EmergencyEvent
- [ ] 4.5.6 Implement transition execution using `on_enter_` and `on_exit_` decorators/methods
- [ ] 4.5.7 Implement transition logging via structlog hooking into the router
- [ ] 4.5.8 Implement `async run()` main loop to pump events safely
- [ ] 4.5.9 Add robust exception handling inside state transitions (Code Robustness)
- [ ] 4.5.10 Implement `current_state` property wrapping statemachine state"""
    
    content = content.replace(fsm_engine_old, fsm_engine_new)

    # Add fixtures directory task
    content = re.sub(
        r"### 4.7 FSM Unit Tests\n\n- \[ \] 4.7.1 Create `tests/unit/test_state_machine.py`",
        "### 4.7 FSM Unit Tests\n\n- [ ] 4.7.0 Create `tests/fixtures/` directory for test mock data\n- [ ] 4.7.1 Create `tests/unit/test_state_machine.py`",
        content
    )

    # Add phase 4 Verification & Commit
    content = content.replace(
        "\n### 4.15 GCS Reporter (Reserved)\n\n- [ ] 4.15.1 Create `src/striker/telemetry/reporter.py`\n- [ ] 4.15.2 Define `GcsReporter` Protocol with reserved interface (no implementation)\n\n---",
        "\n### 4.15 GCS Reporter (Reserved)\n\n- [ ] 4.15.1 Create `src/striker/telemetry/reporter.py`\n- [ ] 4.15.2 Define `GcsReporter` Protocol with reserved interface (no implementation)\n\n### 4.16 Phase 4 Verification & Commit\n\n- [ ] 4.16.1 Run incremental unit tests for all Phase 4 modules (FSM, Safety, Telemetry).\n- [ ] 4.16.2 Perform full project dry-run for Phase 4 components.\n- [ ] 4.16.3 IF BUG DETECTED: Insert debug iteration block for FSM/Safety.\n- [ ] 4.16.4 Git Commit Phase 4 changes with message: `feat(core): 完成阶段4 状态机引擎与安全检查模块，重构为python-statemachine声明式`\n\n---"
    )

    # Phase 5: Add MISSION_ITEM_REACHED
    content = content.replace(
        "- [ ] 5.9.4 Implement ScanState.execute: monitor waypoint progress",
        "- [ ] 5.9.4 Implement ScanState.execute: monitor waypoint progress via MISSION_ITEM_REACHED MAVLink messages"
    )
    # Robustness in Phase 5 Controller
    content = content.replace(
        "- [ ] 5.3.8 Implement GPS validation in all coordinate-accepting methods (RL-05)",
        "- [ ] 5.3.8 Implement GPS validation in all coordinate-accepting methods (RL-05)\n- [ ] 5.3.9 Add robustness: Handle GPS signal loss or timeout during GUIDED coordinate commands"
    )

    # Phase 5 Verification
    content = content.replace(
        "\n---",
        "\n### 5.19 Phase 5 Verification & Commit\n\n- [ ] 5.19.1 Run incremental unit tests for all Phase 5 modules (Flight, Navigation).\n- [ ] 5.19.2 Perform full project dry-run (SITL Takeoff/Scan execution).\n- [ ] 5.19.3 IF BUG DETECTED: Insert debug iteration block.\n- [ ] 5.19.4 Git Commit Phase 5 changes with message: `feat(flight): 完成阶段5 飞行控制、扫描与降落业务状态机`\n\n---",
        1 # Only 1st occurrence if multiple, but we can do a targeted replace replacing "\n---" before Phase 6
    )

    # Let's use regex for safer phase verification insertions
    content = re.sub(
        r"(### 5\.18 SITL Integration Tests[\s\S]*?- \[ \] 5\.18\.6.*?)\n\n---",
        r"\1\n\n### 5.19 Phase 5 Verification & Commit\n\n- [ ] 5.19.1 Run incremental unit tests for all Phase 5 modules (Flight, Navigation).\n- [ ] 5.19.2 Perform full project dry-run (SITL Takeoff/Scan execution).\n- [ ] 5.19.3 IF BUG DETECTED: Insert debug iteration block.\n- [ ] 5.19.4 Git Commit Phase 5 changes with message: `feat(flight): 完成阶段5 飞行控制、扫描与降落业务状态机`\n\n---",
        content
    )

    # Phase 6 SharedMemReceiver and map_pixel_to_gps
    content = content.replace(
        "### 6.4 TCP Receiver",
        "### 6.3b Shared Memory Receiver\n\n- [ ] 6.3b.1 Create `src/striker/vision/shared_mem_receiver.py` (Reserved Interface)\n- [ ] 6.3b.2 Define base stubs for reading targets via SHM\n\n### 6.4 TCP Receiver"
    )

    content = content.replace(
        "- [ ] 6.10.4 Implement `gps_to_ned(lat, lon) → tuple[float, float]`",
        "- [ ] 6.10.4 Implement `gps_to_ned(lat, lon) → tuple[float, float]`\n- [ ] 6.10.4b Implement `map_pixel_to_gps(pixel_x, pixel_y, camera_params) → tuple[float, float]`"
    )

    content = re.sub(
        r"(### 6\.15 Utils Tests[\s\S]*?- \[ \] 6\.15\.24.*?)\n\n---",
        r"\1\n\n### 6.16 Phase 6 Verification & Commit\n\n- [ ] 6.16.1 Run incremental unit tests for Phase 6 modules (Vision, Utils).\n- [ ] 6.16.2 Perform full project dry-run.\n- [ ] 6.16.3 IF BUG DETECTED: Insert debug iteration block.\n- [ ] 6.16.4 Git Commit Phase 6 changes with message: `feat(vision): 完成阶段6 视觉目标接收器与坐标转换工具库`\n\n---",
        content
    )

    # Phase 7 Protocol and Config Additions
    content = content.replace(
        "- [ ] 7.2.3 Define `ReleaseConfig` dataclass (method, channel, pwm_value, gpio_pin)",
        "- [ ] 7.2.3 Define `ReleaseConfig` dataclass (method, channel, pwm_open, pwm_close, gpio_pin, gpio_active_high)"
    )

    content = content.replace(
        "- [ ] 7.3.2 Define `ReleaseController` Protocol with `async trigger() → bool`",
        "- [ ] 7.3.2 Define `ReleaseController` Protocol with: `async arm()`, `async release()`, `is_armed: bool`, `is_released: bool`"
    )

    # Added SequencedRelease
    content = content.replace(
        "### 7.7 Approach State",
        "### 7.6b Sequenced Release\n\n- [ ] 7.6b.1 Create `src/striker/payload/sequenced_release.py` (Reserved Interface)\n- [ ] 7.6b.2 Define interval/pattern-based multi-drop stubs\n\n### 7.7 Approach State"
    )

    content = re.sub(
        r"(### 7\.10 Payload Tests[\s\S]*?- \[ \] 7\.10\.20.*?)\n\n---",
        r"\1\n\n### 7.11 Phase 7 Verification & Commit\n\n- [ ] 7.11.1 Run incremental unit tests for Phase 7 modules (Payload, Ballistics).\n- [ ] 7.11.2 Perform full project dry-run payload drop simulation.\n- [ ] 7.11.3 IF BUG DETECTED: Insert debug iteration block.\n- [ ] 7.11.4 Git Commit Phase 7 changes with message: `feat(payload): 完成阶段7 投掷物释放控制与弹道解算模块`\n\n---",
        content
    )

    # Phase 8 list fields CLI
    content = content.replace(
        "- [ ] 8.2.2 Implement CLI argument parsing (--field, --dry-run)",
        "- [ ] 8.2.2 Implement CLI argument parsing (--field, --dry-run, --list-fields)"
    )

    content += "\n### 8.10 Phase 8 Verification & Commit\n\n- [ ] 8.10.1 Run incremental unit tests for Phase 8 integration points.\n- [ ] 8.10.2 Perform full project dry-run for complete end-to-end mission loop in SITL.\n- [ ] 8.10.3 IF BUG DETECTED: Insert debug iteration block.\n- [ ] 8.10.4 Git Commit Phase 8 changes with message: `feat(app): 完成阶段8 完整应用集成，配置项完善及CLI入口`\n"

    with open('tasks.md', 'w') as f:
        f.write(content)
        
    print("Rewritten successfully.")

rewrite()
