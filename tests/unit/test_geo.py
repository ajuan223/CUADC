"""Unit tests for geo utilities."""

from __future__ import annotations

import math

import pytest

from striker.utils.geo import (
    calculate_bearing,
    destination_point,
    haversine_distance,
    validate_gps,
)


class TestHaversine:
    def test_known_answer_per_degree(self) -> None:
        """~111 km per degree of latitude at equator."""
        dist = haversine_distance(0, 0, 1, 0)
        assert 110_000 < dist < 112_000

    def test_same_point_zero(self) -> None:
        assert haversine_distance(30, 120, 30, 120) == pytest.approx(0.0)

    def test_known_distance(self) -> None:
        # ZJU Yuquan to West Lake roughly 3km
        dist = haversine_distance(30.2637, 120.1250, 30.2500, 120.1500)
        assert 2000 < dist < 3500


class TestBearing:
    def test_north(self) -> None:
        b = calculate_bearing(0, 0, 1, 0)
        assert abs(b - 0.0) < 1.0

    def test_east(self) -> None:
        b = calculate_bearing(0, 0, 0, 1)
        assert abs(b - 90.0) < 1.0

    def test_south(self) -> None:
        b = calculate_bearing(1, 0, 0, 0)
        assert abs(b - 180.0) < 1.0

    def test_west(self) -> None:
        b = calculate_bearing(0, 1, 0, 0)
        assert abs(b - 270.0) < 1.0


class TestDestinationPoint:
    def test_known_answer(self) -> None:
        # 1 degree north from equator
        lat, lon = destination_point(0, 0, 0, 111_320)
        assert abs(lat - 1.0) < 0.01
        assert abs(lon - 0.0) < 0.01

    def test_east_1_degree(self) -> None:
        lat, lon = destination_point(0, 0, 90, 111_320)
        assert abs(lat - 0.0) < 0.01
        assert abs(lon - 1.0) < 0.01


class TestValidateGps:
    def test_accepts_valid(self) -> None:
        assert validate_gps(30.0, 120.0) is True
        assert validate_gps(-90, -180) is True

    def test_rejects_invalid(self) -> None:
        assert validate_gps(91, 0) is False
        assert validate_gps(0, 181) is False
