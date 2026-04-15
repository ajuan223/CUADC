"""Unit tests for business states."""

from __future__ import annotations

import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from striker.core.events import SystemEvent, Transition
from striker.core.machine import MissionStateMachine
from striker.core.states.base import BaseState
from striker.core.states.init import InitState
from striker.core.states.preflight import PreflightState
from striker.core.states.takeoff import TakeoffState
from striker.core.states.scan import ScanState
from striker.core.states.loiter import LoiterState
from striker.core.states.enroute import EnrouteState
from striker.core.states.landing import LandingState
from striker.core.states.completed import CompletedState
from striker.core.states.override import OverrideState
from striker.core.states.emergency import EmergencyState


def _mock_context() -> MagicMock:
    ctx = MagicMock()
    ctx.settings = MagicMock()
    ctx.settings.loiter_timeout_s = 5.0
    ctx.settings.max_scan_cycles = 3
    ctx.settings.dry_run = False
    ctx.field_profile = MagicMock()
    ctx.field_profile.scan_waypoints.waypoints = [MagicMock(), MagicMock()]
    ctx.field_profile.scan_waypoints.altitude_m = 100.0
    ctx.current_position = None
    ctx.scan_cycle_count = 0
    ctx.last_target = None
    ctx.flight_controller = AsyncMock()
    ctx.flight_recorder = MagicMock()
    ctx.target_tracker = MagicMock()
    ctx.target_tracker.get_smoothed_target.return_value = None
    return ctx


class TestPreflightState:
    @pytest.mark.asyncio
    async def test_resets_scan_cycle_count(self) -> None:
        state = PreflightState()
        ctx = _mock_context()
        ctx.scan_cycle_count = 5
        await state.on_enter(ctx)
        assert ctx.scan_cycle_count == 0

    @pytest.mark.asyncio
    async def test_transitions_to_takeoff(self) -> None:
        state = PreflightState()
        ctx = _mock_context()
        await state.on_enter(ctx)
        # First execute: uploads complete
        result = await state.execute(ctx)
        assert result is None  # first call sets _uploads_complete
        # Second execute: should transition
        result = await state.execute(ctx)
        assert result is not None
        assert result.target_state == "takeoff"


class TestTakeoffState:
    @pytest.mark.asyncio
    async def test_waits_for_altitude(self) -> None:
        state = TakeoffState()
        ctx = _mock_context()
        await state.on_enter(ctx)

        # No position yet
        result = await state.execute(ctx)
        assert result is None  # waiting

    @pytest.mark.asyncio
    async def test_transitions_at_target_altitude(self) -> None:
        state = TakeoffState()
        ctx = _mock_context()
        await state.on_enter(ctx)

        # Simulate arm + takeoff
        await state.execute(ctx)
        await state.execute(ctx)

        # Simulate altitude reached
        pos = MagicMock()
        pos.alt_m = 95.0  # 95% of 100m target
        ctx.current_position = pos
        result = await state.execute(ctx)
        assert result is not None
        assert result.target_state == "scan"


class TestScanState:
    @pytest.mark.asyncio
    async def test_increments_cycle_counter(self) -> None:
        state = ScanState()
        ctx = _mock_context()
        ctx.scan_cycle_count = 0
        await state.on_enter(ctx)
        assert ctx.scan_cycle_count == 1

    @pytest.mark.asyncio
    async def test_transitions_to_loiter_on_complete(self) -> None:
        state = ScanState()
        ctx = _mock_context()
        await state.on_enter(ctx)
        # Execute enough times to consume waypoints
        for _ in range(3):
            result = await state.execute(ctx)
        assert result is not None
        assert result.target_state == "loiter"


class TestLoiterState:
    @pytest.mark.asyncio
    async def test_timeout_cycle_lt_max_transitions_to_scan(self) -> None:
        state = LoiterState()
        ctx = _mock_context()
        ctx.scan_cycle_count = 1
        ctx.settings.loiter_timeout_s = 0.1
        ctx.settings.max_scan_cycles = 3
        await state.on_enter(ctx)

        # Wait for timeout
        await asyncio.sleep(0.2)
        result = await state.execute(ctx)
        assert result is not None
        assert result.target_state == "scan"

    @pytest.mark.asyncio
    async def test_timeout_cycle_gte_max_transitions_to_forced_strike(self) -> None:
        state = LoiterState()
        ctx = _mock_context()
        ctx.scan_cycle_count = 3  # >= max_scan_cycles
        ctx.settings.loiter_timeout_s = 0.1
        ctx.settings.max_scan_cycles = 3
        await state.on_enter(ctx)

        await asyncio.sleep(0.2)
        result = await state.execute(ctx)
        assert result is not None
        assert result.target_state == "forced_strike"

    @pytest.mark.asyncio
    async def test_target_received_transitions_to_enroute(self) -> None:
        state = LoiterState()
        ctx = _mock_context()
        ctx.scan_cycle_count = 1
        target = MagicMock()
        ctx.target_tracker.get_smoothed_target.return_value = target
        await state.on_enter(ctx)

        result = await state.execute(ctx)
        assert result is not None
        assert result.target_state == "enroute"


class TestLandingState:
    @pytest.mark.asyncio
    async def test_transitions_to_completed_on_landing(self) -> None:
        state = LandingState()
        ctx = _mock_context()
        await state.on_enter(ctx)

        # Simulate landing trigger
        await state.execute(ctx)
        assert state._landing_triggered

        # Simulate landing detection
        pos = MagicMock()
        pos.relative_alt_m = 0.5
        ctx.current_position = pos
        result = await state.execute(ctx)
        assert result is not None
        assert result.target_state == "completed"


class TestCompletedState:
    @pytest.mark.asyncio
    async def test_is_terminal(self) -> None:
        state = CompletedState()
        ctx = _mock_context()
        await state.on_enter(ctx)
        result = await state.execute(ctx)
        assert result is None  # terminal, no transitions


class TestFullStateChain:
    def test_fsm_full_chain_transitions(self) -> None:
        """Verify the FSM can traverse the full state chain."""
        sm = MissionStateMachine(rtc=False)
        assert sm.current_state_name == "init"
        sm.to_preflight()
        assert sm.current_state_name == "preflight"
        sm.to_takeoff()
        assert sm.current_state_name == "takeoff"
        sm.to_scan()
        assert sm.current_state_name == "scan"
        sm.to_loiter()
        assert sm.current_state_name == "loiter"
        sm.to_enroute()
        assert sm.current_state_name == "enroute"
        sm.to_approach()
        assert sm.current_state_name == "approach"
        sm.to_release()
        assert sm.current_state_name == "release"
        sm.to_landing()
        assert sm.current_state_name == "landing"
        sm.to_completed()
        assert sm.current_state_name == "completed"
