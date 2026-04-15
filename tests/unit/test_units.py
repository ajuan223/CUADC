"""Unit tests for unit conversions."""

from __future__ import annotations

import math

import pytest

from striker.utils.units import (
    deg_to_rad,
    feet_to_meters,
    kmh_to_mps,
    meters_to_feet,
    mps_to_kmh,
    rad_to_deg,
)


class TestUnitConversions:
    def test_deg_rad_roundtrip(self) -> None:
        assert deg_to_rad(180) == pytest.approx(math.pi)
        assert rad_to_deg(math.pi) == pytest.approx(180.0)

    def test_mps_kmh_roundtrip(self) -> None:
        assert mps_to_kmh(10) == pytest.approx(36.0)
        assert kmh_to_mps(36) == pytest.approx(10.0)

    def test_meters_feet_roundtrip(self) -> None:
        assert meters_to_feet(100) == pytest.approx(328.084)
        assert feet_to_meters(328.084) == pytest.approx(100.0, abs=0.01)
