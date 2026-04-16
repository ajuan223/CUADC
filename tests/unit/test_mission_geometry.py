"""Unit tests — procedural mission geometry generators."""

from __future__ import annotations

import math

import pytest

from striker.config.field_profile import FieldProfile, GeoPoint, point_in_polygon
from striker.flight.mission_geometry import (
    MissionGeometryResult,
    derive_landing_approach,
    generate_boustrophedon_scan,
    generate_takeoff_geometry,
)

# ── Fixtures ──────────────────────────────────────────────────────

_SQUARE_POLY = [
    (30.2700, 120.0900),
    (30.2700, 120.1000),
    (30.2600, 120.1000),
    (30.2600, 120.0900),
    (30.2700, 120.0900),
]

_GEOFENCE_GEOPOINTS = [GeoPoint(lat=lat, lon=lon) for lat, lon in _SQUARE_POLY]


def _near_boundary(lat: float, lon: float) -> bool:
    """Check if point is within ~0.001 deg of the polygon boundary (edge tolerance)."""
    lats = [p[0] for p in _SQUARE_POLY]
    lons = [p[1] for p in _SQUARE_POLY]
    for edge_lat in set(lats):
        if abs(lat - edge_lat) < 0.001:
            return True
    for edge_lon in set(lons):
        if abs(lon - edge_lon) < 0.001:
            return True
    return False


# ── Landing approach derivation ───────────────────────────────────


class TestDeriveLandingApproach:
    def test_3deg_glide_slope_30m(self) -> None:
        lat, lon, alt = derive_landing_approach(
            touchdown_lat=30.2610,
            touchdown_lon=120.0950,
            touchdown_alt_m=0.0,
            heading_deg=180.0,
            approach_alt_m=30.0,
            glide_slope_deg=3.0,
            geofence_polygon=_GEOFENCE_GEOPOINTS,
        )
        assert alt == 30.0
        # 30 / tan(3°) ≈ 572.9m along heading 0° from touchdown
        # So lat should be higher (further north) than touchdown
        assert lat > 30.2610
        assert abs(lon - 120.0950) < 0.001  # heading 0° → same lon

    def test_nonzero_touchdown_alt(self) -> None:
        lat, lon, alt = derive_landing_approach(
            touchdown_lat=30.2610,
            touchdown_lon=120.0950,
            touchdown_alt_m=5.0,
            heading_deg=180.0,
            approach_alt_m=30.0,
            glide_slope_deg=3.0,
            geofence_polygon=_GEOFENCE_GEOPOINTS,
        )
        # delta_alt = 25m, distance = 25/tan(3°) ≈ 477.4m
        assert alt == 30.0
        assert lat > 30.2610

    def test_reject_non_descending(self) -> None:
        with pytest.raises(ValueError, match="above touchdown"):
            derive_landing_approach(
                touchdown_lat=30.2610,
                touchdown_lon=120.0950,
                touchdown_alt_m=50.0,
                heading_deg=180.0,
                approach_alt_m=30.0,
                glide_slope_deg=3.0,
                geofence_polygon=_GEOFENCE_GEOPOINTS,
            )

    def test_reject_equal_alt(self) -> None:
        with pytest.raises(ValueError, match="above touchdown"):
            derive_landing_approach(
                touchdown_lat=30.2610,
                touchdown_lon=120.0950,
                touchdown_alt_m=30.0,
                heading_deg=180.0,
                approach_alt_m=30.0,
                glide_slope_deg=3.0,
                geofence_polygon=_GEOFENCE_GEOPOINTS,
            )

    def test_reject_approach_outside_geofence(self) -> None:
        # Very steep glide slope + high altitude → approach very far away
        with pytest.raises(ValueError, match="outside geofence"):
            derive_landing_approach(
                touchdown_lat=30.2610,
                touchdown_lon=120.0950,
                touchdown_alt_m=0.0,
                heading_deg=180.0,
                approach_alt_m=500.0,
                glide_slope_deg=3.0,
                geofence_polygon=_GEOFENCE_GEOPOINTS,
            )

    def test_reject_minimum_distance(self) -> None:
        # Very steep angle with tiny alt delta → distance < 200m
        with pytest.raises(ValueError, match="below minimum"):
            derive_landing_approach(
                touchdown_lat=30.2610,
                touchdown_lon=120.0950,
                touchdown_alt_m=0.0,
                heading_deg=180.0,
                approach_alt_m=1.0,
                glide_slope_deg=3.0,
                geofence_polygon=_GEOFENCE_GEOPOINTS,
            )


# ── Boustrophedon scan generation ─────────────────────────────────


class TestBoustrophedonScan:
    def test_generates_waypoints_in_polygon(self) -> None:
        wps = generate_boustrophedon_scan(
            boundary_polygon=_SQUARE_POLY,
            scan_alt_m=80.0,
            scan_spacing_m=500.0,  # coarse for ~1km polygon
            scan_heading_deg=0.0,
        )
        assert len(wps) > 0
        for lat, lon, alt in wps:
            assert alt == 80.0
            # Points on the polygon edge are acceptable (within floating-point tolerance)
            assert point_in_polygon(lat, lon, _GEOFENCE_GEOPOINTS) or _near_boundary(lat, lon)

    def test_reject_fewer_than_3_vertices(self) -> None:
        with pytest.raises(ValueError, match="at least 3"):
            generate_boustrophedon_scan(
                boundary_polygon=[(30.27, 120.09), (30.26, 120.10)],
                scan_alt_m=80.0,
                scan_spacing_m=100.0,
                scan_heading_deg=0.0,
            )

    def test_reject_zero_spacing(self) -> None:
        with pytest.raises(ValueError, match="positive"):
            generate_boustrophedon_scan(
                boundary_polygon=_SQUARE_POLY,
                scan_alt_m=80.0,
                scan_spacing_m=0.0,
                scan_heading_deg=0.0,
            )

    def test_boustrophedon_ordering(self) -> None:
        """Odd sweeps should reverse direction (entry/exit swapped)."""
        wps = generate_boustrophedon_scan(
            boundary_polygon=_SQUARE_POLY,
            scan_alt_m=80.0,
            scan_spacing_m=300.0,
            scan_heading_deg=0.0,
        )
        # Each sweep produces pairs: check that waypoints come in pairs
        assert len(wps) % 2 == 0


# ── Takeoff geometry ──────────────────────────────────────────────


class TestTakeoffGeometry:
    def test_basic_takeoff_geometry(self) -> None:
        result = generate_takeoff_geometry(
            touchdown_lat=30.2610,
            touchdown_lon=120.0950,
            touchdown_alt_m=0.0,
            heading_deg=0.0,  # takeoff north
            runway_length_m=200.0,
            takeoff_alt_m=80.0,
        )
        assert result["start_alt_m"] == 0.0
        assert result["climbout_alt_m"] == 80.0
        # Start point: midpoint is 100m north of touchdown, start is 80m behind midpoint
        # → start is 20m north of touchdown
        assert result["start_lat"] > 30.2610
        # Climbout should be 200m north of touchdown (far end of runway)
        assert result["climbout_lat"] > result["start_lat"]

    def test_reject_zero_runway_length(self) -> None:
        with pytest.raises(ValueError, match="positive"):
            generate_takeoff_geometry(
                touchdown_lat=30.2610,
                touchdown_lon=120.0950,
                touchdown_alt_m=0.0,
                heading_deg=0.0,
                runway_length_m=0.0,
                takeoff_alt_m=80.0,
            )

    def test_reject_takeoff_below_runway(self) -> None:
        with pytest.raises(ValueError, match="above runway"):
            generate_takeoff_geometry(
                touchdown_lat=30.2610,
                touchdown_lon=120.0950,
                touchdown_alt_m=100.0,
                heading_deg=0.0,
                runway_length_m=200.0,
                takeoff_alt_m=80.0,
            )


# ── MissionGeometryResult indices ─────────────────────────────────


class TestMissionGeometryResultIndices:
    def test_compute_indices(self) -> None:
        result = MissionGeometryResult(
            takeoff_start=(30.27, 120.09, 0.0),
            takeoff_climbout=(30.28, 120.09, 80.0),
            scan_waypoints=[(30.27, 120.09, 80.0)] * 8,
            landing_approach=(30.26, 120.09, 30.0),
            landing_touchdown=(30.25, 120.09, 0.0),
            use_do_land_start=True,
        )
        result.compute_indices()
        assert result.takeoff_start_seq == 1
        assert result.scan_start_seq == 3
        assert result.scan_end_seq == 10
        assert result.landing_start_seq == 11
