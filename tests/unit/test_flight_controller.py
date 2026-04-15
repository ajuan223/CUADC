"""Unit tests for flight controller."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

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

    def test_gps_validation_accepts_valid(self) -> None:
        FlightController._validate_gps(30.0, 120.0)  # should not raise
        FlightController._validate_gps(-90.0, -180.0)  # boundary
        FlightController._validate_gps(90.0, 180.0)  # boundary

    def test_gps_validation_rejects_invalid_lat(self) -> None:
        with pytest.raises(FlightError, match="Invalid latitude"):
            FlightController._validate_gps(91.0, 120.0)

    def test_gps_validation_rejects_invalid_lon(self) -> None:
        with pytest.raises(FlightError, match="Invalid longitude"):
            FlightController._validate_gps(30.0, 181.0)

    def test_gps_validation_rejects_negative_lat(self) -> None:
        with pytest.raises(FlightError, match="Invalid latitude"):
            FlightController._validate_gps(-91.0, 0.0)
