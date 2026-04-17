"""Unit tests for ballistic solver with known-answer tests."""

from __future__ import annotations

import math

from striker.payload.ballistics import BallisticCalculator


class TestBallisticCalculator:
    def setup_method(self) -> None:
        self.calc = BallisticCalculator(gravity=9.81)

    def test_kat1_50m_20mps_north_no_wind(self) -> None:
        """KAT #1: 50m alt, 20 m/s north, 0 wind → ~63.9m lead."""
        lat, lon = self.calc.calculate_release_point(
            target_lat=30.0, target_lon=120.0,
            altitude_m=50.0,
            velocity_n_mps=20.0, velocity_e_mps=0.0,
            wind_n_mps=0.0, wind_e_mps=0.0,
        )
        # Release point should be upstream (south of target)
        assert lat < 30.0
        # Displacement ~63.9m → lat offset ~0.000575 deg
        assert abs(lat - 30.0) < 0.001
        assert abs(lon - 120.0) < 0.001

    def test_kat2_100m_25mps_east_5mps_w_wind(self) -> None:
        """KAT #2: 100m alt, 25 m/s east, 5 m/s west wind → ~142.5m lead."""
        _lat, lon = self.calc.calculate_release_point(
            target_lat=30.0, target_lon=120.0,
            altitude_m=100.0,
            velocity_n_mps=0.0, velocity_e_mps=25.0,
            wind_n_mps=0.0, wind_e_mps=-5.0,
        )
        # Net east velocity: 25 + (-5) = 20 m/s
        # Release point should be upstream (west of target)
        assert lon < 120.0

    def test_kat3_30m_15mps_ne_no_wind(self) -> None:
        """KAT #3: 30m alt, 15 m/s NE, 0 wind → ~37.1m lead."""
        lat, lon = self.calc.calculate_release_point(
            target_lat=30.0, target_lon=120.0,
            altitude_m=30.0,
            velocity_n_mps=15.0 * math.cos(math.pi / 4),
            velocity_e_mps=15.0 * math.sin(math.pi / 4),
        )
        assert lat < 30.0  # upstream is south-west
        assert lon < 120.0

    def test_altitude_zero_returns_target(self) -> None:
        lat, lon = self.calc.calculate_release_point(30.0, 120.0, 0.0)
        assert lat == 30.0
        assert lon == 120.0

    def test_altitude_negative_returns_target(self) -> None:
        lat, lon = self.calc.calculate_release_point(30.0, 120.0, -10.0)
        assert lat == 30.0
        assert lon == 120.0

    def test_pure_north_displacement(self) -> None:
        lat, lon = self.calc.calculate_release_point(
            30.0, 120.0, 50.0, velocity_n_mps=10.0,
        )
        assert lat < 30.0
        assert abs(lon - 120.0) < 0.0001

    def test_pure_east_displacement(self) -> None:
        lat, lon = self.calc.calculate_release_point(
            30.0, 120.0, 50.0, velocity_e_mps=10.0,
        )
        assert abs(lat - 30.0) < 0.0001
        assert lon < 120.0

    def test_wind_compensation_direction(self) -> None:
        """Wind from north should push impact north → release south."""
        no_wind = self.calc.calculate_release_point(
            30.0, 120.0, 50.0, velocity_n_mps=10.0,
        )
        with_wind = self.calc.calculate_release_point(
            30.0, 120.0, 50.0, velocity_n_mps=10.0, wind_n_mps=5.0,
        )
        # With wind, more upstream needed → release further south
        assert with_wind[0] < no_wind[0]
