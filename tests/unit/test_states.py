"""Unit tests for business states."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from striker.comms.messages import MAV_CMD_MISSION_SET_CURRENT
from striker.core.machine import MissionStateMachine
from striker.core.states.completed import CompletedState
from striker.core.states.enroute import (
    ATTACK_HANDOFF_ALT_BUFFER_M,
    EnrouteState,
    _calculate_approach_heading,
    _calculate_exit_waypoint,
    _select_attack_altitude,
)
from striker.core.states.landing import LandingState
from striker.core.states.preflight import PreflightState
from striker.core.states.release import ReleaseState
from striker.core.states.scan import ScanState
from striker.core.states.takeoff import TakeoffState
from striker.utils.geo import haversine_distance


def _mock_context() -> MagicMock:
    ctx = MagicMock()
    ctx.settings = MagicMock()
    ctx.settings.dry_run = False
    ctx.field_profile = MagicMock()
    scan_waypoints = [MagicMock(), MagicMock()] if hasattr(ctx.field_profile.scan, "waypoints") else []
    ctx.field_profile.scan.waypoints = scan_waypoints
    ctx.field_profile.scan.altitude_m = 100.0
    ctx.current_position = None
    ctx.mission_current_seq = 0
    ctx.mission_item_reached_seq = -1
    ctx.current_wind = None
    ctx.active_drop_point = None
    ctx.drop_point_source = ""
    ctx.drop_point_tracker = MagicMock()
    ctx.drop_point_tracker.get_smoothed_drop_point.return_value = None
    ctx.landing_sequence_start_index = None
    ctx.scan_start_seq = 1
    ctx.scan_end_seq = 3
    ctx.flight_controller = AsyncMock()
    ctx.flight_recorder = MagicMock()
    ctx.last_status_text = ""
    ctx.field_profile.attack_run.exit_distance_m = 200.0
    ctx.field_profile.attack_run.approach_distance_m = 200.0
    ctx.field_profile.landing.runway_length_m = 200.0

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
        ctx.scan_start_seq = 4
        ctx.scan_end_seq = 9
        ctx.mission_current_seq = 5
        ctx.mission_item_reached_seq = 6
        await state.on_enter(ctx)
        assert ctx.landing_sequence_start_index is None
        assert ctx.scan_start_seq is None
        assert ctx.scan_end_seq is None
        assert ctx.mission_current_seq == 0
        assert ctx.mission_item_reached_seq == -1

    @pytest.mark.asyncio
    async def test_uploads_full_mission_and_stores_landing_index(self) -> None:
        state = PreflightState()
        ctx = _mock_context()
        await state.on_enter(ctx)

        mock_geom = MagicMock()
        mock_geom.scan_start_seq = 3
        mock_geom.scan_end_seq = 3
        with (
            patch("striker.core.states.preflight.generate_mission_geometry", return_value=mock_geom),
            patch("striker.core.states.preflight.upload_full_mission", new=AsyncMock(return_value=4)) as upload,
        ):
            result = await state.execute(ctx)

        assert result is None
        upload.assert_awaited_once_with(ctx.connection, mock_geom)
        assert ctx.landing_sequence_start_index == 4
        assert ctx.scan_start_seq == 3

    @pytest.mark.asyncio
    async def test_transitions_to_takeoff(self) -> None:
        state = PreflightState()
        ctx = _mock_context()
        await state.on_enter(ctx)
        mock_geom = MagicMock()
        mock_geom.scan_start_seq = 3
        mock_geom.scan_end_seq = 3
        # First execute: uploads complete
        with (
            patch("striker.core.states.preflight.generate_mission_geometry", return_value=mock_geom),
            patch("striker.core.states.preflight.upload_full_mission", new=AsyncMock(return_value=4)),
        ):
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
        ctx.scan_start_seq = 2
        ctx.mission_current_seq = 3  # >= scan_end_seq
        ctx.mission_item_reached_seq = -1
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
        ctx.scan_start_seq = 2
        ctx.mission_current_seq = 3  # >= scan_end_seq
        ctx.mission_item_reached_seq = -1
        ctx.drop_point_tracker.get_smoothed_drop_point.return_value = None
        ctx.field_profile.attack_run.fallback_drop_point = None

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
        ctx.scan_start_seq = 2
        ctx.mission_current_seq = 0  # scan not started
        ctx.mission_item_reached_seq = -1
        await state.on_enter(ctx)

        result = await state.execute(ctx)
        assert result is None
    @pytest.mark.asyncio
    async def test_scan_completes_from_mission_item_reached(self) -> None:
        state = ScanState()
        ctx = _mock_context()
        ctx.scan_start_seq = 2
        ctx.mission_current_seq = 1
        ctx.mission_item_reached_seq = 3
        ctx.drop_point_tracker.get_smoothed_drop_point.return_value = (30.5, 120.5)
        await state.on_enter(ctx)

        result = await state.execute(ctx)
        assert result is not None
        assert result.target_state == "enroute"

    @pytest.mark.asyncio
    async def test_scan_ignores_stale_out_of_range_seq_until_scan_progress_observed(self) -> None:
        state = ScanState()
        ctx = _mock_context()
        ctx.scan_start_seq = 3
        ctx.scan_end_seq = 12
        ctx.mission_current_seq = 20
        ctx.mission_item_reached_seq = 20
        await state.on_enter(ctx)

        result = await state.execute(ctx)
        assert result is None

        ctx.mission_current_seq = 3
        ctx.mission_item_reached_seq = 3
        result = await state.execute(ctx)
        assert result is None

        ctx.mission_current_seq = 12
        ctx.mission_item_reached_seq = 12
        ctx.drop_point_tracker.get_smoothed_drop_point.return_value = (30.5, 120.5)
        result = await state.execute(ctx)
        assert result is not None
        assert result.target_state == "enroute"


class TestEnrouteState:
    def test_prefers_landing_approach_bearing_without_wind(self) -> None:
        ctx = _mock_context()
        geometry = MagicMock()
        geometry.landing_approach = (30.266148, 120.095, 30.0)

        heading = _calculate_approach_heading(
            context=ctx,
            geometry=geometry,
            target_lat=30.260502367023822,
            target_lon=120.09718108499997,
        )

        assert heading == pytest.approx(341.55, abs=0.1)

    def test_prefers_published_landing_corridor_when_target_is_at_landing_approach(self) -> None:
        ctx = _mock_context()
        ctx.field_profile.landing.heading_deg = 155.18309494177925
        geometry = MagicMock()
        geometry.landing_approach = (30.30041700564638, 120.0720231438355, 21.4)

        heading = _calculate_approach_heading(
            context=ctx,
            geometry=geometry,
            target_lat=30.30041700564638,
            target_lon=120.0720231438355,
        )

        assert heading == pytest.approx(335.18309494177925)

    def test_caps_exit_leg_before_landing_approach_without_wind(self) -> None:
        ctx = _mock_context()
        ctx.field_profile.attack_run.exit_distance_m = 200.0
        ctx.field_profile.attack_run.approach_distance_m = 200.0
        ctx.field_profile.landing.runway_length_m = 98.0
        geometry = MagicMock()
        geometry.landing_approach = (30.266148, 120.095, 30.0)

        exit_lat, exit_lon = _calculate_exit_waypoint(
            context=ctx,
            geometry=geometry,
            target_lat=30.265,
            target_lon=120.095,
            approach_heading=0.0,
        )

        # Exit should remain south of landing approach and not extend beyond it.
        assert exit_lat < geometry.landing_approach[0]
        assert exit_lon == pytest.approx(120.095)

        handoff_leg_m = haversine_distance(
            exit_lat,
            exit_lon,
            geometry.landing_approach[0],
            geometry.landing_approach[1],
        )
        assert handoff_leg_m == pytest.approx(98.0, abs=1.5)

    def test_caps_exit_leg_for_round8_style_handoff_spacing(self) -> None:
        ctx = _mock_context()
        ctx.field_profile.attack_run.exit_distance_m = 100.0
        ctx.field_profile.attack_run.approach_distance_m = 100.0
        ctx.field_profile.landing.runway_length_m = 98.0
        geometry = MagicMock()
        geometry.landing_approach = (30.30041700564638, 120.0720231438355, 21.4)
        target_lat = 30.30186889085492
        target_lon = 120.07155599218392
        approach_heading = 164.5

        exit_lat, exit_lon = _calculate_exit_waypoint(
            context=ctx,
            geometry=geometry,
            target_lat=target_lat,
            target_lon=target_lon,
            approach_heading=approach_heading,
        )

        handoff_leg_m = haversine_distance(
            exit_lat,
            exit_lon,
            geometry.landing_approach[0],
            geometry.landing_approach[1],
        )
        assert handoff_leg_m == pytest.approx(98.0, abs=1.5)

    def test_allows_zero_exit_when_target_is_inside_min_handoff_leg(self) -> None:
        ctx = _mock_context()
        ctx.field_profile.attack_run.exit_distance_m = 100.0
        ctx.field_profile.attack_run.approach_distance_m = 100.0
        ctx.field_profile.landing.runway_length_m = 98.0
        geometry = MagicMock()
        geometry.landing_approach = (30.30041700564638, 120.0720231438355, 21.4)
        target_lat = 30.3005
        target_lon = 120.0720
        approach_heading = 164.5

        exit_lat, exit_lon = _calculate_exit_waypoint(
            context=ctx,
            geometry=geometry,
            target_lat=target_lat,
            target_lon=target_lon,
            approach_heading=approach_heading,
        )

        assert exit_lat == pytest.approx(target_lat)
        assert exit_lon == pytest.approx(target_lon)

    def test_keeps_configured_exit_leg_with_wind_alignment(self) -> None:
        ctx = _mock_context()
        ctx.field_profile.attack_run.exit_distance_m = 200.0
        wind = MagicMock()
        wind.speed_mps = 5.0
        wind.direction_deg = 270.0
        ctx.current_wind = wind
        geometry = MagicMock()
        geometry.landing_approach = (30.266148, 120.095, 30.0)

        exit_lat, exit_lon = _calculate_exit_waypoint(
            context=ctx,
            geometry=geometry,
            target_lat=30.265,
            target_lon=120.095,
            approach_heading=90.0,
        )

        assert exit_lat == pytest.approx(30.265, abs=1e-3)
        assert exit_lon > 120.095

    def test_selects_buffered_attack_altitude_below_scan_altitude(self) -> None:
        ctx = _mock_context()
        ctx.field_profile.scan.altitude_m = 30.0
        geometry = MagicMock()
        geometry.landing_approach = (30.266148, 120.095, 21.4)

        attack_alt = _select_attack_altitude(ctx, geometry)

        assert attack_alt == pytest.approx(21.4 + ATTACK_HANDOFF_ALT_BUFFER_M)

    def test_caps_attack_altitude_at_scan_altitude(self) -> None:
        ctx = _mock_context()
        ctx.field_profile.scan.altitude_m = 24.0
        geometry = MagicMock()
        geometry.landing_approach = (30.266148, 120.095, 21.4)

        attack_alt = _select_attack_altitude(ctx, geometry)

        assert attack_alt == pytest.approx(24.0)

    @pytest.mark.asyncio
    async def test_heads_to_drop_point(self) -> None:
        state = EnrouteState()
        ctx = _mock_context()
        ctx.active_drop_point = (30.5, 120.5)
        with patch("striker.core.states.enroute.generate_mission_geometry") as gen_geom:
            geometry = MagicMock()
            geometry.landing_approach = (30.266148, 120.095, 30.0)
            gen_geom.return_value = geometry
            with patch(
                "striker.core.states.enroute.upload_attack_mission",
                new=AsyncMock(return_value=(2, 5)),
            ) as upload:
                await state.on_enter(ctx)
        assert state._attack_active is True  # set in on_enter after upload
        assert state._awaiting_attack_seq_sync is True
        assert upload.await_args.kwargs["attack_alt_m"] == pytest.approx(35.0)  # type: ignore

    @pytest.mark.asyncio
    async def test_transitions_at_drop_point(self) -> None:
        state = EnrouteState()
        ctx = _mock_context()
        ctx.active_drop_point = (30.25, 120.10)
        with patch("striker.core.states.enroute.generate_mission_geometry") as gen_geom:
            geometry = MagicMock()
            geometry.landing_approach = (30.266148, 120.095, 30.0)
            gen_geom.return_value = geometry
            with patch("striker.core.states.enroute.upload_attack_mission", new=AsyncMock(return_value=(2, 5))):
                await state.on_enter(ctx)

        ctx.mission_current_seq = 1
        result = await state.execute(ctx)
        assert result is None
        assert state._awaiting_attack_seq_sync is False

        ctx.mission_current_seq = 3  # > target_seq (2)
        result = await state.execute(ctx)
        assert result is not None
        assert result.target_state == "release"

    @pytest.mark.asyncio
    async def test_ignores_stale_scan_sequence_until_attack_mission_sync(self) -> None:
        state = EnrouteState()
        ctx = _mock_context()
        ctx.active_drop_point = (30.25, 120.10)
        ctx.mission_current_seq = 12
        with patch("striker.core.states.enroute.generate_mission_geometry") as gen_geom:
            geometry = MagicMock()
            geometry.landing_approach = (30.266148, 120.095, 30.0)
            gen_geom.return_value = geometry
            with patch("striker.core.states.enroute.upload_attack_mission", new=AsyncMock(return_value=(2, 5))):
                await state.on_enter(ctx)

        result = await state.execute(ctx)
        assert result is None
        assert state._awaiting_attack_seq_sync is True

    @pytest.mark.asyncio
    async def test_ignores_out_of_range_progress_after_attack_mission_sync(self) -> None:
        state = EnrouteState()
        ctx = _mock_context()
        ctx.active_drop_point = (30.25, 120.10)
        with patch("striker.core.states.enroute.generate_mission_geometry") as gen_geom:
            geometry = MagicMock()
            geometry.landing_approach = (30.266148, 120.095, 30.0)
            gen_geom.return_value = geometry
            with patch("striker.core.states.enroute.upload_attack_mission", new=AsyncMock(return_value=(2, 5))):
                await state.on_enter(ctx)

        ctx.mission_current_seq = 1
        result = await state.execute(ctx)
        assert result is None
        assert state._awaiting_attack_seq_sync is False

        ctx.mission_current_seq = 11
        result = await state.execute(ctx)
        assert result is None


class TestReleaseState:
    @pytest.mark.asyncio
    async def test_uploads_landing_only_mission_after_native_release(self) -> None:
        state = ReleaseState()
        ctx = _mock_context()
        ctx.attack_geometry = MagicMock()
        await state.on_enter(ctx)

        with patch(
            "striker.core.states.release.upload_landing_mission",
            new=AsyncMock(return_value=1),
        ) as upload_landing:
            result = await state.execute(ctx)

        upload_landing.assert_awaited_once_with(
            conn=ctx.connection,
            geometry=ctx.attack_geometry,
            context=ctx,
        )
        assert result is not None
        assert result.target_state == "landing"

    @pytest.mark.asyncio
    async def test_uploads_landing_only_mission_after_dry_run_release(self) -> None:
        state = ReleaseState()
        ctx = _mock_context()
        ctx.settings.dry_run = True
        ctx.attack_geometry = MagicMock()
        ctx.release_controller.release = AsyncMock(return_value=True)
        await state.on_enter(ctx)

        with patch(
            "striker.core.states.release.upload_landing_mission",
            new=AsyncMock(return_value=1),
        ) as upload_landing:
            result = await state.execute(ctx)

        ctx.release_controller.release.assert_awaited_once()
        upload_landing.assert_awaited_once_with(
            conn=ctx.connection,
            geometry=ctx.attack_geometry,
            context=ctx,
        )
        assert result is not None
        assert result.target_state == "landing"


class TestLandingState:
    @pytest.mark.asyncio
    async def test_sets_landing_mission_current_on_entry(self) -> None:
        state = LandingState()
        ctx = _mock_context()
        ctx.landing_sequence_start_index = 1
        ctx.connection = MagicMock()
        ctx.connection.flightmode = "AUTO"
        geometry = MagicMock()
        geometry.landing_approach = (30.0, 120.0, 30.0)
        ctx.attack_geometry = geometry
        pos = MagicMock()
        pos.lat = 30.0003
        pos.lon = 120.0003
        pos.relative_alt_m = 20.0
        ctx.current_position = pos
        await state.on_enter(ctx)

        await state.execute(ctx)

        ctx.flight_controller.set_mode.assert_awaited_once()
        ctx.flight_controller.send_command.assert_awaited_once_with(
            MAV_CMD_MISSION_SET_CURRENT,
            param1=1.0,
        )

    @pytest.mark.asyncio
    async def test_transitions_to_completed_on_landing(self) -> None:
        state = LandingState()
        ctx = _mock_context()
        ctx.landing_sequence_start_index = 3
        ctx.connection = MagicMock()
        ctx.connection.flightmode = "AUTO"
        geometry = MagicMock()
        geometry.landing_approach = (30.0, 120.0, 30.0)
        ctx.attack_geometry = geometry
        pos = MagicMock()
        pos.lat = 30.0003
        pos.lon = 120.0003
        pos.relative_alt_m = 20.0
        ctx.current_position = pos
        await state.on_enter(ctx)

        # First execute enters landing monitoring
        await state.execute(ctx)
        assert state._landing_triggered
        ctx.flight_controller.set_mode.assert_awaited_once()
        ctx.flight_controller.send_command.assert_awaited_once_with(
            MAV_CMD_MISSION_SET_CURRENT,
            param1=3.0,
        )

        # Simulate landing detection
        pos.relative_alt_m = 0.5
        result = await state.execute(ctx)
        assert result is not None
        assert result.target_state == "completed"

    @pytest.mark.asyncio
    async def test_transitions_to_override_when_stuck_in_manual_near_ground(self) -> None:
        state = LandingState()
        ctx = _mock_context()
        ctx.landing_sequence_start_index = 3
        ctx.connection = MagicMock()
        ctx.connection.flightmode = "AUTO"
        geometry = MagicMock()
        geometry.landing_approach = (30.0, 120.0, 30.0)
        ctx.attack_geometry = geometry
        pos = MagicMock()
        pos.lat = 30.0003
        pos.lon = 120.0003
        pos.relative_alt_m = 57.0
        ctx.current_position = pos
        await state.on_enter(ctx)
        await state.execute(ctx)

        pos.relative_alt_m = 57.0
        ctx.connection.flightmode = "MANUAL"

        result = None
        for _ in range(20):
            result = await state.execute(ctx)

        assert result is not None
        assert result.target_state == "override"


    @pytest.mark.asyncio
    async def test_transitions_to_completed_on_landing_statustext(self) -> None:
        state = LandingState()
        ctx = _mock_context()
        ctx.landing_sequence_start_index = 3
        ctx.connection = MagicMock()
        ctx.connection.flightmode = "AUTO"
        ctx.last_status_text = ""
        geometry = MagicMock()
        geometry.landing_approach = (30.0, 120.0, 30.0)
        ctx.attack_geometry = geometry
        pos = MagicMock()
        pos.lat = 30.0003
        pos.lon = 120.0003
        pos.relative_alt_m = 0.5
        ctx.current_position = pos
        await state.on_enter(ctx)
        await state.execute(ctx)

        pos.relative_alt_m = 0.5
        ctx.last_status_text = "SIM Hit ground at 4.7 m/s"

        result = await state.execute(ctx)
        assert result is not None
        assert result.target_state == "completed"

    @pytest.mark.asyncio
    async def test_ignores_hit_ground_statustext_while_still_airborne(self) -> None:
        state = LandingState()
        ctx = _mock_context()
        ctx.landing_sequence_start_index = 3
        ctx.connection = MagicMock()
        ctx.connection.flightmode = "AUTO"
        ctx.last_status_text = ""
        geometry = MagicMock()
        geometry.landing_approach = (30.0, 120.0, 30.0)
        ctx.attack_geometry = geometry
        pos = MagicMock()
        pos.lat = 30.0003
        pos.lon = 120.0003
        pos.relative_alt_m = 36.0
        ctx.current_position = pos
        await state.on_enter(ctx)
        await state.execute(ctx)

        pos.relative_alt_m = 36.0
        ctx.last_status_text = "SIM Hit ground at 6.0 m/s"

        result = await state.execute(ctx)
        assert result is None

    @pytest.mark.asyncio
    async def test_defers_landing_activation_until_near_landing_approach(self) -> None:
        state = LandingState()
        ctx = _mock_context()
        ctx.landing_sequence_start_index = 3
        ctx.connection = MagicMock()
        ctx.connection.flightmode = "AUTO"
        ctx.field_profile.landing.runway_length_m = 90.0
        geometry = MagicMock()
        geometry.landing_approach = (30.0, 120.0, 30.0)
        ctx.attack_geometry = geometry
        pos = MagicMock()
        pos.lat = 30.0015
        pos.lon = 120.0015
        pos.relative_alt_m = 25.0
        ctx.current_position = pos
        await state.on_enter(ctx)

        result = await state.execute(ctx)

        assert result is None
        ctx.flight_controller.set_mode.assert_not_awaited()
        ctx.flight_controller.send_command.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_is_terminal(self) -> None:
        state = CompletedState()
        ctx = _mock_context()
        await state.on_enter(ctx)
        result = await state.execute(ctx)  # type: ignore
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
