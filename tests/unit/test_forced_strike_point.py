"""Unit tests for forced strike point generator."""

from __future__ import annotations

import pytest

from striker.utils.forced_strike_point import generate_forced_strike_point
from striker.utils.point_in_polygon import point_in_polygon

_POLYGON = [(30.25, 120.10), (30.25, 120.12), (30.28, 120.12), (30.28, 120.10)]


class TestForcedStrikePoint:
    def test_all_points_inside_polygon(self) -> None:
        for _ in range(100):
            lat, lon = generate_forced_strike_point(_POLYGON, buffer_m=10.0)
            assert point_in_polygon(lat, lon, _POLYGON)

    def test_deterministic_seeding(self) -> None:
        p1 = generate_forced_strike_point(_POLYGON, seed=42)
        p2 = generate_forced_strike_point(_POLYGON, seed=42)
        assert p1 == p2

    def test_different_seeds_different_points(self) -> None:
        p1 = generate_forced_strike_point(_POLYGON, seed=1)
        p2 = generate_forced_strike_point(_POLYGON, seed=2)
        assert p1 != p2

    def test_passes_point_in_polygon_verification(self) -> None:
        for seed in range(50):
            lat, lon = generate_forced_strike_point(_POLYGON, buffer_m=5.0, seed=seed)
            assert point_in_polygon(lat, lon, _POLYGON)
