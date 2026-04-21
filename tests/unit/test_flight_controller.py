"""Unit tests for flight controller."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest

from striker.comms.messages import MAV_CMD_MISSION_SET_CURRENT
from striker.exceptions import FlightError
from striker.flight.controller import FlightController
from striker.flight.modes import ArduPlaneMode


class TestFlightModes:
    def test_mode_values(self) -> None:
        assert ArduPlaneMode.MANUAL.mode_id == 0
        assert ArduPlaneMode.AUTO.mode_id == 10
        assert ArduPlaneMode.GUIDED.mode_id == 15
        assert ArduPlaneMode.LOITER.mode_id == 12

    def test_from_name(self) -> None:
        assert ArduPlaneMode.from_name("auto") == ArduPlaneMode.AUTO
        assert ArduPlaneMode.from_name("GUIDED") == ArduPlaneMode.GUIDED


class TestFlightController:
    def _make_fc(self) -> FlightController:
        conn = MagicMock()
        return FlightController(conn)

    @pytest.mark.asyncio
    async def test_takeoff_starts_uploaded_mission(self) -> None:
        fc = self._make_fc()
        fc.send_command = AsyncMock()  # type: ignore
        fc.set_mode = AsyncMock()  # type: ignore

        await fc.takeoff(100.0)

        fc.send_command.assert_awaited_once_with(MAV_CMD_MISSION_SET_CURRENT, param1=0.0)
        fc.set_mode.assert_awaited_once_with(ArduPlaneMode.AUTO)

    @pytest.mark.asyncio
    async def test_set_mode_blocked_after_autonomy_relinquished(self) -> None:
        fc = self._make_fc()
        fc._conn.ensure_autonomy_allowed.side_effect = FlightError("Autonomy relinquished")  # type: ignore

        with pytest.raises(FlightError, match="Autonomy relinquished"):
            await fc.set_mode(ArduPlaneMode.AUTO)

    def test_manual_mode_blocks_command_and_relinquishes_autonomy(self) -> None:
        fc = self._make_fc()
        fc._conn.ensure_autonomy_allowed.return_value = None  # type: ignore
        fc._conn.flightmode = "AUTO"  # type: ignore
        fc._assert_command_allowed()
        fc._conn.flightmode = "MANUAL"  # type: ignore

        with pytest.raises(FlightError, match="vehicle in MANUAL"):
            fc._assert_command_allowed()

        fc._conn.relinquish_autonomy.assert_called_once_with("vehicle already in MANUAL")  # type: ignore

    def test_initial_manual_mode_does_not_block_takeover_guard(self) -> None:
        fc = self._make_fc()
        fc._conn.ensure_autonomy_allowed.return_value = None  # type: ignore
        fc._conn.flightmode = "MANUAL"  # type: ignore

        fc._assert_command_allowed()

        fc._conn.relinquish_autonomy.assert_not_called()  # type: ignore

    def test_gps_validation_accepts_valid(self) -> None:
        FlightController._validate_gps(30.0, 120.0)
        FlightController._validate_gps(-90.0, -180.0)
        FlightController._validate_gps(90.0, 180.0)

    def test_gps_validation_rejects_invalid_lat(self) -> None:
        with pytest.raises(FlightError, match="Invalid latitude"):
            FlightController._validate_gps(91.0, 120.0)

    def test_gps_validation_rejects_invalid_lon(self) -> None:
        with pytest.raises(FlightError, match="Invalid longitude"):
            FlightController._validate_gps(30.0, 181.0)

    def test_gps_validation_rejects_negative_lat(self) -> None:
        with pytest.raises(FlightError, match="Invalid latitude"):
            FlightController._validate_gps(-91.0, 0.0)
