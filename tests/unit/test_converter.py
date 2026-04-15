"""Unit tests for coordinate converter."""

from __future__ import annotations

import pytest

from striker.utils.converter import CoordConverter


class TestCoordConverter:
    def test_ned_to_gps_known_offset(self) -> None:
        """NED(100m N, 50m E) should produce correct GPS offset."""
        conv = CoordConverter(ref_lat=30.0, ref_lon=120.0)
        lat, lon = conv.ned_to_gps(100.0, 50.0)
        # ~100m north → lat increases by ~0.0009 deg
        assert abs(lat - 30.0) < 0.002
        assert lat > 30.0
        assert lon > 120.0

    def test_round_trip_ned_gps(self) -> None:
        """NED → GPS → NED should be within tolerance."""
        conv = CoordConverter(ref_lat=30.0, ref_lon=120.0)
        n, e = 150.0, -75.0
        lat, lon = conv.ned_to_gps(n, e)
        n2, e2 = conv.gps_to_ned(lat, lon)
        assert n == pytest.approx(n2, abs=0.01)
        assert e == pytest.approx(e2, abs=0.01)

    def test_different_latitudes(self) -> None:
        """Converter at higher latitudes should compress longitude."""
        conv_eq = CoordConverter(ref_lat=0, ref_lon=0)
        conv_60 = CoordConverter(ref_lat=60, ref_lon=0)
        # Same NED offset → different GPS delta at different latitudes
        lat_eq, lon_eq = conv_eq.ned_to_gps(0, 1000)
        lat_60, lon_60 = conv_60.ned_to_gps(0, 1000)
        # Longitude offset should be larger at 60° (less m per deg)
        assert abs(lon_60) > abs(lon_eq)
