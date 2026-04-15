"""Unit tests for geofence ray-casting algorithm."""

from __future__ import annotations

import pytest

from striker.config.field_profile import GeoPoint
from striker.safety.geofence import Geofence


# ── Test polygon (rough rectangle around ZJU Yuquan campus) ──────

_POLYGON = [
    GeoPoint(lat=30.260, lon=120.100),
    GeoPoint(lat=30.260, lon=120.120),
    GeoPoint(lat=30.280, lon=120.120),
    GeoPoint(lat=30.280, lon=120.100),
    GeoPoint(lat=30.260, lon=120.100),  # close polygon
]


class TestGeofence:
    def test_inside_known_interior_point(self) -> None:
        fence = Geofence(_POLYGON)
        assert fence.is_inside(30.270, 120.110) is True

    def test_outside_known_exterior_point(self) -> None:
        fence = Geofence(_POLYGON)
        assert fence.is_inside(30.250, 120.090) is False

    def test_point_on_boundary(self) -> None:
        """Points on the boundary edge should be considered inside."""
        fence = Geofence(_POLYGON)
        # On the bottom edge (lat=30.260, lon between 120.100 and 120.120)
        assert fence.is_inside(30.260, 120.110) is True

    def test_distance_to_boundary_interior(self) -> None:
        fence = Geofence(_POLYGON)
        dist = fence.distance_to_boundary(30.270, 120.110)
        # Center of rectangle, should be ~1.1 km from edges
        assert dist > 0

    def test_distance_to_boundary_outside(self) -> None:
        fence = Geofence(_POLYGON)
        dist = fence.distance_to_boundary(30.250, 120.090)
        assert dist > 0

    def test_triangle_polygon(self) -> None:
        tri = [
            GeoPoint(lat=0.0, lon=0.0),
            GeoPoint(lat=1.0, lon=0.0),
            GeoPoint(lat=0.5, lon=1.0),
        ]
        fence = Geofence(tri)
        assert fence.is_inside(0.5, 0.3) is True
        assert fence.is_inside(0.5, 0.8) is True
        assert fence.is_inside(2.0, 2.0) is False

    def test_less_than_3_vertices(self) -> None:
        fence = Geofence([GeoPoint(lat=0.0, lon=0.0), GeoPoint(lat=1.0, lon=1.0)])
        assert fence.is_inside(0.5, 0.5) is False
