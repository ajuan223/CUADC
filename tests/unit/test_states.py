"""Unit tests for business states."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from striker.core.machine import MissionStateMachine
from striker.core.states.completed import CompletedState
from striker.core.states.emergency import EmergencyState
from striker.core.states.enroute import EnrouteState
from striker.core.states.landing import LandingState
from striker.core.states.preflight import PreflightState
from striker.core.states.scan import ScanState
from striker.core.states.takeoff import TakeoffState


def _mock_context() -> MagicMock:
    ctx = MagicMock()
    ctx.settings = MagicMock()
    ctx.settings.dry_run = False
    ctx.field_profile = MagicMock()
    ctx.field_profile.scan.waypoints = [MagicMock(), MagicMock()] if hasattr(ctx.field_profile.scan, 'waypoints') else []
    ctx.field_profile.scan.altitude_m = 100.0
    ctx.current_position = None
    ctx.mission_current_seq = 0
    ctx.current_wind = None
    ctx.active_drop_point = None
    ctx.drop_point_source = ""
    ctx.drop_point_tracker = MagicMock()
    ctx.drop_point_tracker.get_smoothed_drop_point.return_value = None
    ctx.landing_sequence_start_index = None
    ctx.scan_end_seq = 3
    ctx.flight_controller = AsyncMock()
    ctx.flight_recorder = MagicMock()

    def _set_drop_point(lat: float, lon: float, source: str) -> None:
        ctx.active_drop_point = (lat, lon)
        ctx.drop_point_source = source

    ctx.set_drop_point = MagicMock(side_effect=_set_drop_point)
    return ctx


class TestPreflightState:
    @pytest.mark.asyncio
    async def test_resets_landing_index(self) -> None:
        state = PreflightState()
        ctx = _mock_context()
        ctx.landing_sequence_start_index = 7
        await state.on_enter(ctx)
        assert ctx.landing_sequence_start_index is None

    @pytest.mark.asyncio
    async def test_uploads_full_mission_and_stores_landing_index(self) -> None:
        state = PreflightState()
        ctx = _mock_context()
        await state.on_enter(ctx)

        mock_geom = MagicMock()
        mock_geom.scan_end_seq = 3
        with patch("striker.core.states.preflight.generate_mission_geometry", return_value=mock_geom):
            with patch("striker.core.states.preflight.upload_full_mission", new=AsyncMock(return_value=4)) as upload:
                result = await state.execute(ctx)

        assert result is None
        upload.assert_awaited_once_with(ctx.connection, mock_geom)
        assert ctx.landing_sequence_start_index == 4

    @pytest.mark.asyncio
    async def test_transitions_to_takeoff(self) -> None:
        state = PreflightState()
        ctx = _mock_context()
        await state.on_enter(ctx)
        mock_geom = MagicMock()
        mock_geom.scan_end_seq = 3
        # First execute: uploads complete
        with patch("striker.core.states.preflight.generate_mission_geometry", return_value=mock_geom):
            with patch("striker.core.states.preflight.upload_full_mission", new=AsyncMock(return_value=4)):
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
    async def test_scan_complete_with_vision_drop_point(self) -> None:
        state = ScanState()
        ctx = _mock_context()
        ctx.mission_current_seq = 3  # >= scan_end_seq
        ctx.drop_point_tracker.get_smoothed_drop_point.return_value = (30.5, 120.5)
        await state.on_enter(ctx)

        result = await state.execute(ctx)
        assert result is not None
        assert result.target_state == "enroute"
        assert ctx.active_drop_point == (30.5, 120.5)
        assert ctx.drop_point_source == "vision"

    @pytest.mark.asyncio
    async def test_scan_complete_with_fallback_midpoint(self) -> None:
        state = ScanState()
        ctx = _mock_context()
        ctx.mission_current_seq = 3  # >= scan_end_seq
        ctx.drop_point_tracker.get_smoothed_drop_point.return_value = None

        landing_ref = MagicMock()
        landing_ref.lat = 30.28
        landing_ref.lon = 120.12
        ctx.field_profile.landing.touchdown_point = landing_ref

        # last_scan_waypoint returns a MagicMock with .lat/.lon — works with fallback_drop_point
        scan_end = MagicMock()
        scan_end.lat = 30.25
        scan_end.lon = 120.10
        ctx.last_scan_waypoint = scan_end

        await state.on_enter(ctx)
        result = await state.execute(ctx)
        assert result is not None
        assert result.target_state == "enroute"
        assert ctx.drop_point_source == "fallback_midpoint"
        assert ctx.active_drop_point is not None

    @pytest.mark.asyncio
    async def test_scan_not_complete_stays(self) -> None:
        state = ScanState()
        ctx = _mock_context()
        ctx.mission_current_seq = 0  # scan not started
        await state.on_enter(ctx)

        result = await state.execute(ctx)
        assert result is None


class TestEnrouteState:
    @pytest.mark.asyncio
    async def test_heads_to_drop_point(self) -> None:
        state = EnrouteState()
        ctx = _mock_context()
        ctx.active_drop_point = (30.5, 120.5)
        with patch("striker.core.states.enroute.generate_mission_geometry", return_value=MagicMock()):
            with patch("striker.core.states.enroute.upload_attack_mission", new=AsyncMock(return_value=(2, 5))):
                await state.on_enter(ctx)
        assert state._attack_active is True  # set in on_enter after upload

    @pytest.mark.asyncio
    async def test_transitions_at_drop_point(self) -> None:
        state = EnrouteState()
        ctx = _mock_context()
        ctx.active_drop_point = (30.25, 120.10)
        with patch("striker.core.states.enroute.generate_mission_geometry", return_value=MagicMock()):
            with patch("striker.core.states.enroute.upload_attack_mission", new=AsyncMock(return_value=(2, 5))):
                await state.on_enter(ctx)

        # Simulate mission progress past target waypoint
        ctx.mission_current_seq = 3  # > target_seq (2)
        result = await state.execute(ctx)
        assert result is not None
        assert result.target_state == "release"

    @pytest.mark.asyncio
    async def test_no_drop_point_stays(self) -> None:
        state = EnrouteState()
        ctx = _mock_context()
        ctx.active_drop_point = None
        await state.on_enter(ctx)
        result = await state.execute(ctx)
        assert result is None


class TestLandingState:
    @pytest.mark.asyncio
    async def test_transitions_to_completed_on_landing(self) -> None:
        state = LandingState()
        ctx = _mock_context()
        ctx.landing_sequence_start_index = 3
        await state.on_enter(ctx)

        # Simulate landing trigger
        await state.execute(ctx)
        assert state._landing_triggered
        ctx.flight_controller.send_command.assert_awaited_once()
        _, kwargs = ctx.flight_controller.send_command.await_args
        assert kwargs["param1"] == 3.0

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
        """Verify the FSM can traverse the simplified state chain."""
        sm = MissionStateMachine(rtc=False)
        assert sm.current_state_name == "init"
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
