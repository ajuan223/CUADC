"""Field profile —场地配置数据模型 + 地理校验.

Loads field configurations from ``data/fields/{name}/field.json``, validates
geographic constraints (waypoints inside geofence, closed polygon, etc.)
using pydantic + ray-casting point-in-polygon algorithm.
"""

import json
from pathlib import Path

from pydantic import BaseModel, field_validator, model_validator

from striker.exceptions import ConfigError, FieldValidationError

# ── Nested data models (mapping field.json structure) ─────────────


class GeoPoint(BaseModel):
    """WGS84 geographic coordinate."""

    lat: float
    lon: float


class BoundaryConfig(BaseModel):
    """Geofence boundary — a closed polygon."""

    description: str = ""
    polygon: list[GeoPoint]


class ApproachWaypoint(BaseModel):
    """Landing approach waypoint."""

    lat: float
    lon: float
    alt_m: float


class TouchdownPoint(BaseModel):
    """Landing touchdown point."""

    lat: float
    lon: float
    alt_m: float


class LandingConfig(BaseModel):
    """Fixed-wing landing sequence parameters."""

    description: str = ""
    approach_waypoint: ApproachWaypoint
    touchdown_point: TouchdownPoint
    glide_slope_deg: float
    heading_deg: float


class ScanWaypointsConfig(BaseModel):
    """Scan pattern waypoints."""

    description: str = ""
    altitude_m: float
    waypoints: list[GeoPoint]


class LoiterPointConfig(BaseModel):
    """Default loiter / orbit point."""

    description: str = ""
    lat: float
    lon: float
    alt_m: float
    radius_m: float


# ── Top-level model ───────────────────────────────────────────────


class FieldProfile(BaseModel):
    """Complete field configuration with geographic validation."""

    name: str
    description: str = ""
    coordinate_system: str = "WGS84"
    boundary: BoundaryConfig
    landing: LandingConfig
    scan_waypoints: ScanWaypointsConfig
    loiter_point: LoiterPointConfig
    safety_buffer_m: float

    @field_validator("safety_buffer_m")
    @classmethod
    def _safety_buffer_positive(cls, v: float) -> float:
        if v <= 0:
            msg = f"safety_buffer_m must be positive, got {v}"
            raise ValueError(msg)
        return v

    @model_validator(mode="after")
    def _auto_close_polygon(self) -> "FieldProfile":
        """Ensure the boundary polygon is closed (first == last vertex)."""
        poly = self.boundary.polygon
        if poly and poly[0] != poly[-1]:
            self.boundary.polygon.append(poly[0].model_copy())
        return self

    @model_validator(mode="after")
    def _validate_points_in_geofence(self) -> "FieldProfile":
        """Validate all waypoints and landing points are inside the geofence."""
        polygon = self.boundary.polygon
        if len(polygon) < 3:
            msg = "Geofence polygon must have at least 3 vertices"
            raise ValueError(msg)

        # Scan waypoints
        for i, wp in enumerate(self.scan_waypoints.waypoints):
            if not point_in_polygon(wp.lat, wp.lon, polygon):
                raise FieldValidationError(
                    f"scan_waypoints[{i}]",
                    f"({wp.lat}, {wp.lon}) is outside the geofence boundary",
                )

        # Landing approach
        aw = self.landing.approach_waypoint
        if not point_in_polygon(aw.lat, aw.lon, polygon):
            raise FieldValidationError(
                "landing.approach_waypoint",
                f"({aw.lat}, {aw.lon}) is outside the geofence boundary",
            )

        # Landing touchdown
        td = self.landing.touchdown_point
        if not point_in_polygon(td.lat, td.lon, polygon):
            raise FieldValidationError(
                "landing.touchdown_point",
                f"({td.lat}, {td.lon}) is outside the geofence boundary",
            )

        # Loiter point
        lp = self.loiter_point
        if not point_in_polygon(lp.lat, lp.lon, polygon):
            raise FieldValidationError(
                "loiter_point",
                f"({lp.lat}, {lp.lon}) is outside the geofence boundary",
            )

        return self


# ── Point-in-polygon (ray casting) ───────────────────────────────


def point_in_polygon(lat: float, lon: float, polygon: list[GeoPoint]) -> bool:
    """Return ``True`` if (lat, lon) is inside *polygon* (ray-casting algorithm).

    The polygon is assumed to be closed (first == last vertex).
    Points exactly on an edge are considered inside.
    """
    n = len(polygon)
    inside = False
    j = n - 1  # start with last vertex

    for i in range(n):
        yi, xi = polygon[i].lat, polygon[i].lon
        yj, xj = polygon[j].lat, polygon[j].lon

        # Check if point is on the horizontal ray crossing test
        if ((yi > lat) != (yj > lat)) and (
            lon < (xj - xi) * (lat - yi) / (yj - yi) + xi if (yj - yi) != 0 else lon <= xi
        ):
            inside = not inside
        elif yi == lat and xi == lon:
            # Point coincides with vertex
            return True

        j = i

    return inside


# ── Loader ────────────────────────────────────────────────────────

_DEFAULT_FIELDS_DIR = Path("data/fields")


def load_field_profile(name: str, base_dir: Path = _DEFAULT_FIELDS_DIR) -> FieldProfile:
    """Load and validate a field profile from ``data/fields/{name}/field.json``.

    Raises
    ------
    ConfigError
        If the field file does not exist.
    pydantic.ValidationError
        If the JSON data fails model validation.
    FieldValidationError
        If geographic constraints are violated.
    """
    field_file = base_dir / name / "field.json"
    if not field_file.exists():
        raise ConfigError(f"Field configuration not found: {field_file}")

    raw = json.loads(field_file.read_text(encoding="utf-8"))
    return FieldProfile.model_validate(raw)
