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
    load_field_profile,
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
    safety_buffer_m: float = 50.0,
    heading_deg: float = 270.0,
    scan_altitude_m: float = 80.0,
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
        },
        "scan": {
            "description": "Test scan config",
            "altitude_m": scan_altitude_m,
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

    def test_jsonc_loading(self, tmp_path: Path) -> None:
        field_dir = tmp_path / "jsonc_field"
        field_dir.mkdir(parents=True)
        jsonc_str = """
        {
            "name": "jsonc_field", // shared
            // Full line comment
            "coordinate_system": "WGS84",
            "boundary": {
                "polygon": [
                    {"lat": -35.3620, "lon": 149.1640},
                    {"lat": -35.3620, "lon": 149.1700},
                    {"lat": -35.3680, "lon": 149.1700},
                    {"lat": -35.3680, "lon": 149.1640}
                ]
            },
            "landing": {
                "touchdown_point": {"lat": -35.3632, "lon": 149.1652, "alt_m": 0.0},
                "heading_deg": 270.0 // shared
            },
            "scan": {
                "altitude_m": 80.0
            },
            "attack_run": {},
            "safety_buffer_m": 50.0 // runtime
        }
        """
        (field_dir / "field.json").write_text(jsonc_str, encoding="utf-8")
        profile = load_field_profile("jsonc_field", base_dir=tmp_path)
        assert profile.name == "jsonc_field"
        assert profile.safety_buffer_m == 50.0

    def test_zjg_runtime_field_loads_with_valid_derived_landing_approach(self) -> None:
        repo_root = Path(__file__).resolve().parents[2]
        profile = load_field_profile("zjg", base_dir=repo_root / "data" / "fields")
        assert profile.name == "zjg"
        assert profile.landing.heading_deg == pytest.approx(335.18309494177925)

    def test_missing_file_raises_config_error(self, tmp_path: Path) -> None:
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
