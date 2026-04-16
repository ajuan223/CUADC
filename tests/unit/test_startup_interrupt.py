"""Unit tests for startup interrupt handling."""

from __future__ import annotations

import asyncio
import contextlib
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from striker.app import main


class TestStartupInterrupt:
    @pytest.mark.asyncio
    async def test_ctrl_c_during_connect_returns_cleanly(self) -> None:
        shutdown_event: asyncio.Event | None = None

        def fake_install_signal_handlers(event: asyncio.Event) -> None:
            nonlocal shutdown_event
            shutdown_event = event

        async def slow_connect() -> None:
            await asyncio.sleep(10)

        mock_field_profile = MagicMock()
        mock_field_profile.name = "SITL Default"
        mock_field_profile.boundary.polygon = []
        mock_connection = MagicMock()
        mock_connection.connect = AsyncMock(side_effect=slow_connect)
        mock_connection.disconnect = MagicMock()
        mock_heartbeat = MagicMock()
        mock_heartbeat.seed_healthy = MagicMock()
        mock_heartbeat.stop = MagicMock()
        mock_flight_controller = MagicMock()
        mock_geofence = MagicMock()
        mock_safety = MagicMock()
        mock_safety.set_heartbeat_check = MagicMock()
        mock_safety.set_event_callback = MagicMock()
        mock_safety.stop = MagicMock()
        mock_drop_point_tracker = MagicMock()
        mock_vision = MagicMock()
        mock_vision.stop = AsyncMock()
        mock_release = MagicMock()
        mock_recorder = MagicMock()
        mock_recorder.stop = MagicMock()
        mock_fsm = MagicMock()
        mock_fsm.register_state_instance = MagicMock()
        mock_fsm.stop = MagicMock()

        with patch("striker.app.load_field_profile", return_value=mock_field_profile):
            with patch("striker.app.MAVLinkConnection", return_value=mock_connection):
                with patch("striker.app.HeartbeatMonitor", return_value=mock_heartbeat):
                    with patch("striker.app.FlightController", return_value=mock_flight_controller):
                        with patch("striker.app.Geofence", return_value=mock_geofence):
                            with patch("striker.app.SafetyMonitor", return_value=mock_safety):
                                with patch("striker.app.DropPointTracker", return_value=mock_drop_point_tracker):
                                    with patch("striker.app._create_vision_receiver_stub", return_value=mock_vision):
                                        with patch("striker.app._create_release_controller", return_value=mock_release):
                                            with patch("striker.app.FlightRecorder", return_value=mock_recorder):
                                                with patch("striker.app.MissionStateMachine", return_value=mock_fsm):
                                                    with patch("striker.app._install_signal_handlers", side_effect=fake_install_signal_handlers):
                                                        task = asyncio.create_task(main(["--field", "sitl_default"]))
                                                        while shutdown_event is None:
                                                            await asyncio.sleep(0)
                                                        shutdown_event.set()
                                                        await task

        mock_connection.connect.assert_awaited_once()
        mock_connection.disconnect.assert_called_once()
        mock_heartbeat.seed_healthy.assert_not_called()
        mock_vision.stop.assert_awaited_once()
        mock_fsm.stop.assert_called_once()

