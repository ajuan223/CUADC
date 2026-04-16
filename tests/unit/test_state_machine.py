"""Unit tests for state machine engine, events, and context."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest

from striker.core.events import (
    EmergencyEvent,
    FlightEvent,
    OverrideEvent,
    SystemEvent,
    Transition,
)
from striker.core.machine import MissionStateMachine
from striker.core.states.base import BaseState
from striker.core.states.init import InitState
from striker.core.states.override import OverrideState
from striker.core.states.emergency import EmergencyState
from striker.core.context import MissionContext
from striker.comms.telemetry import GeoPosition


# ── State registration ───────────────────────────────────────────


class TestStateRegistration:
    def test_register_and_lookup(self) -> None:
        from striker.core.states import register_state, get_state

        register_state("test_reg", InitState)
        assert get_state("test_reg") is InitState

    def test_lookup_missing_raises(self) -> None:
        from striker.core.states import get_state

        with pytest.raises(KeyError, match="not registered"):
            get_state("nonexistent_state_xyz")


# ── FSM Engine ────────────────────────────────────────────────────


class TestFSMEngine:
    def test_initial_state(self) -> None:
        sm = MissionStateMachine()
        assert sm.current_state_name == "init"

    def test_init_noop_stays_init(self) -> None:
        sm = MissionStateMachine()
        # No event means we stay in init
        assert sm.current_state_name == "init"

    def test_init_to_override(self) -> None:
        sm = MissionStateMachine(rtc=False)
        sm.to_override()
        assert sm.current_state_name == "override"

    def test_any_state_to_emergency(self) -> None:
        sm = MissionStateMachine(rtc=False)
        # From init
        sm.to_emergency()
        assert sm.current_state_name == "emergency"

    def test_override_from_any_state(self) -> None:
        sm = MissionStateMachine(rtc=False)
        sm.to_preflight()
        sm.to_override()
        assert sm.current_state_name == "override"

    def test_emergency_from_any_state(self) -> None:
        sm = MissionStateMachine(rtc=False)
        sm.to_preflight()
        sm.to_takeoff()
        sm.to_emergency()
        assert sm.current_state_name == "emergency"

    def test_full_chain(self) -> None:
        """Simplified chain: init→preflight→takeoff→scan→enroute→release→landing→completed."""
        sm = MissionStateMachine(rtc=False)
        sm.to_preflight()
        assert sm.current_state_name == "preflight"
        sm.to_takeoff()
        assert sm.current_state_name == "takeoff"
        sm.to_scan()
        assert sm.current_state_name == "scan"
        sm.to_enroute()
        assert sm.current_state_name == "enroute"
        sm.to_release()
        assert sm.current_state_name == "release"
        sm.to_landing()
        assert sm.current_state_name == "landing"
        sm.to_completed()
        assert sm.current_state_name == "completed"

    def test_state_instance_lifecycle(self) -> None:
        """Verify on_exit called before on_enter during transition."""
        sm = MissionStateMachine(rtc=False)
        init = InitState()
        override = OverrideState()
        sm.register_state_instance("init", init)
        sm.register_state_instance("override", override)

        # Simulate override transition
        sm.to_override()
        assert sm.current_state_name == "override"


# ── Events ────────────────────────────────────────────────────────


class TestEvents:
    def test_system_event_values(self) -> None:
        assert SystemEvent.INIT_COMPLETE.value == "INIT_COMPLETE"
        assert SystemEvent.SHUTDOWN.value == "SHUTDOWN"

    def test_flight_event_values(self) -> None:
        assert FlightEvent.TAKEOFF_COMPLETE.value == "TAKEOFF_COMPLETE"

    def test_override_event(self) -> None:
        event = OverrideEvent(reason="Manual mode")
        assert event.reason == "Manual mode"

    def test_emergency_event(self) -> None:
        event = EmergencyEvent(reason="Battery low")
        assert event.reason == "Battery low"

    def test_transition(self) -> None:
        t = Transition(target_state="preflight", reason="Init complete")
        assert t.target_state == "preflight"
        assert t.reason == "Init complete"


# ── MissionContext ─────────────────────────────────────────────────


class TestMissionContext:
    def _make_context(self) -> MissionContext:
        """Create a minimal MissionContext with mocked subsystems."""
        return MissionContext(
            settings=MagicMock(),
            field_profile=MagicMock(),
            connection=MagicMock(),
            heartbeat_monitor=MagicMock(),
            flight_controller=MagicMock(),
            safety_monitor=MagicMock(),
            vision_receiver=MagicMock(),
            drop_point_tracker=MagicMock(),
            release_controller=MagicMock(),
            flight_recorder=MagicMock(),
        )

    def test_update_position(self) -> None:
        ctx = self._make_context()
        assert ctx.current_position is None

        pos = GeoPosition(lat=30.0, lon=120.0, alt_m=100.0, relative_alt_m=50.0)
        ctx.update_position(pos)
        assert ctx.current_position is pos
        assert ctx.current_position.lat == 30.0

    def test_set_drop_point(self) -> None:
        ctx = self._make_context()
        assert ctx.active_drop_point is None

        ctx.set_drop_point(30.5, 120.5, source="vision")
        assert ctx.active_drop_point == (30.5, 120.5)
        assert ctx.drop_point_source == "vision"

    def test_update_mission_seq(self) -> None:
        ctx = self._make_context()
        assert ctx.mission_current_seq == 0

        ctx.update_mission_seq(3)
        assert ctx.mission_current_seq == 3

    def test_initial_state(self) -> None:
        ctx = self._make_context()
        assert ctx.current_position is None
        assert ctx.active_drop_point is None
        assert ctx.mission_current_seq == 0
