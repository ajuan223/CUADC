"""Unit tests — Field profile loading and geographic validation."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest
from pydantic import ValidationError

from striker.config.field_profile import (
    FieldProfile,
    GeoPoint,
    point_in_polygon,
)
from striker.exceptions import ConfigError, FieldValidationError

# ── Fixtures ──────────────────────────────────────────────────────

# A valid square geofence around (-35.36, 149.16) area
_SQUARE_FENCE: list[dict[str, float]] = [
    {"lat": -35.3620, "lon": 149.1640},
    {"lat": -35.3620, "lon": 149.1700},
    {"lat": -35.3680, "lon": 149.1700},
    {"lat": -35.3680, "lon": 149.1640},
]

_POINT_INSIDE = {"lat": -35.3650, "lon": 149.1670}
_POINT_OUTSIDE = {"lat": -35.3600, "lon": 149.1600}


def _make_field_json(
    *,
    polygon: list[dict[str, float]] | None = None,
    touchdown_point: dict[str, float] | None = None,
    loiter_point: dict[str, float] | None = None,
    loiter_alt_m: float = 80.0,
    safety_buffer_m: float = 50.0,
    approach_alt_m: float = 60.0,
    glide_slope_deg: float = 8.0,
    heading_deg: float = 135.0,
    runway_length_m: float = 200.0,
    scan_altitude_m: float = 80.0,
    scan_spacing_m: float = 100.0,
    scan_heading_deg: float = 0.0,
) -> dict[str, Any]:
    """Build a valid field JSON dict with sensible defaults."""
    return {
        "name": "test_field",
        "description": "Test field",
        "coordinate_system": "WGS84",
        "boundary": {
            "description": "Test boundary",
            "polygon": polygon or _SQUARE_FENCE,
        },
        "landing": {
            "description": "Test landing",
            "touchdown_point": touchdown_point
            or {"lat": -35.3632, "lon": 149.1652, "alt_m": 0.0},
            "heading_deg": heading_deg,
            "glide_slope_deg": glide_slope_deg,
            "approach_alt_m": approach_alt_m,
            "runway_length_m": runway_length_m,
        },
        "scan": {
            "description": "Test scan config",
            "altitude_m": scan_altitude_m,
            "spacing_m": scan_spacing_m,
            "heading_deg": scan_heading_deg,
        },
        "loiter_point": {
            "description": "Test loiter point",
            **(loiter_point or _POINT_INSIDE),
            "alt_m": loiter_alt_m,
            "radius_m": 80.0,
        },
        "safety_buffer_m": safety_buffer_m,
    }


def _write_field(tmp_path: Path, data: dict[str, Any], name: str = "test_field") -> Path:
    field_dir = tmp_path / name
    field_dir.mkdir(parents=True, exist_ok=True)
    field_file = field_dir / "field.json"
    field_file.write_text(json.dumps(data), encoding="utf-8")
    return field_file


# ── Valid field loading ───────────────────────────────────────────


class TestLoadFieldProfile:
    def test_valid_field_loads(self, tmp_path: Path) -> None:
        data = _make_field_json()
        _write_field(tmp_path, data)
        profile = FieldProfile.model_validate(data)
        assert profile.name == "test_field"
        assert profile.scan.altitude_m == 80.0
        assert profile.scan.spacing_m == 100.0
        assert profile.landing.approach_alt_m == 60.0
        assert profile.landing.runway_length_m == 200.0

    def test_missing_file_raises_config_error(self, tmp_path: Path) -> None:
        from striker.config.field_profile import load_field_profile

        with pytest.raises(ConfigError, match="not found"):
            load_field_profile("nonexistent", base_dir=tmp_path)

    def test_invalid_json_structure(self, tmp_path: Path) -> None:
        data = _make_field_json()
        data["boundary"]["polygon"] = "not an array"
        with pytest.raises(ValidationError):
            FieldProfile.model_validate(data)


# ── Polygon auto-close ───────────────────────────────────────────


class TestPolygonAutoClose:
    def test_open_polygon_auto_closed(self) -> None:
        data = _make_field_json(polygon=_SQUARE_FENCE)  # 4 vertices, open
        profile = FieldProfile.model_validate(data)
        # Should auto-close to 5 vertices
        assert len(profile.boundary.polygon) == 5
        assert profile.boundary.polygon[0] == profile.boundary.polygon[-1]

    def test_already_closed_polygon_unchanged(self) -> None:
        closed = [*_SQUARE_FENCE, _SQUARE_FENCE[0]]  # 5 vertices, closed
        data = _make_field_json(polygon=closed)
        profile = FieldProfile.model_validate(data)
        assert len(profile.boundary.polygon) == 5


# ── Point-in-polygon (ray casting) ───────────────────────────────


class TestPointInPolygon:
    @pytest.fixture()
    def square_polygon(self) -> list[GeoPoint]:
        return [GeoPoint(**p) for p in _SQUARE_FENCE] + [GeoPoint(**_SQUARE_FENCE[0])]

    def test_point_inside(self, square_polygon: list[GeoPoint]) -> None:
        assert point_in_polygon(-35.3650, 149.1670, square_polygon) is True

    def test_point_outside(self, square_polygon: list[GeoPoint]) -> None:
        assert point_in_polygon(-35.3600, 149.1600, square_polygon) is False

    def test_point_on_vertex(self, square_polygon: list[GeoPoint]) -> None:
        # Vertex of the polygon
        assert point_in_polygon(-35.3620, 149.1640, square_polygon) is True


# ── Waypoint geofence validation ─────────────────────────────────


class TestWaypointGeofence:
    def test_touchdown_outside_rejected(self) -> None:
        data = _make_field_json(touchdown_point={**_POINT_OUTSIDE, "alt_m": 0.0})
        with pytest.raises(FieldValidationError, match="touchdown_point"):
            FieldProfile.model_validate(data)

    def test_loiter_outside_rejected(self) -> None:
        data = _make_field_json(loiter_point=_POINT_OUTSIDE)
        with pytest.raises(FieldValidationError, match="loiter_point"):
            FieldProfile.model_validate(data)


# ── Landing constraint validation ────────────────────────────────


class TestLandingConstraints:
    def test_negative_runway_length_rejected(self) -> None:
        data = _make_field_json(runway_length_m=-10.0)
        with pytest.raises(ValidationError):
            FieldProfile.model_validate(data)

    def test_zero_runway_length_rejected(self) -> None:
        data = _make_field_json(runway_length_m=0.0)
        with pytest.raises(ValidationError):
            FieldProfile.model_validate(data)


# ── Safety buffer validation ─────────────────────────────────────


class TestSafetyBuffer:
    def test_negative_safety_buffer_rejected(self) -> None:
        data = _make_field_json(safety_buffer_m=-10.0)
        with pytest.raises(ValidationError):
            FieldProfile.model_validate(data)

    def test_zero_safety_buffer_rejected(self) -> None:
        data = _make_field_json(safety_buffer_m=0.0)
        with pytest.raises(ValidationError):
            FieldProfile.model_validate(data)
