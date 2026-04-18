"""Field profile —场地配置数据模型 + 地理校验.

Loads field configurations from ``data/fields/{name}/field.json``, validates
geographic constraints (waypoints inside geofence, closed polygon, etc.)
using pydantic + ray-casting point-in-polygon algorithm.
"""

import json
import math
from pathlib import Path

from pydantic import BaseModel, field_validator, model_validator

from striker.exceptions import ConfigError, FieldValidationError
from striker.utils.geo import destination_point

# ── Nested data models (mapping field.json structure) ─────────────


class GeoPoint(BaseModel):
    """WGS84 geographic coordinate."""

    lat: float
    lon: float


class BoundaryConfig(BaseModel):
    """Geofence boundary — a closed polygon."""

    description: str = ""
    polygon: list[GeoPoint]


class TouchdownPoint(BaseModel):
    """Landing touchdown point on the runway."""

    lat: float
    lon: float
    alt_m: float


class LandingConfig(BaseModel):
    """Fixed-wing landing sequence parameters.

    The approach waypoint is derived from touchdown, heading, glide slope,
    and approach altitude — not hand-authored.
    """

    description: str = ""
    touchdown_point: TouchdownPoint
    heading_deg: float
    glide_slope_deg: float
    approach_alt_m: float
    runway_length_m: float = 200.0
    use_do_land_start: bool = True


class ScanConfig(BaseModel):
    """Scan pattern constraints for procedural generation."""

    description: str = ""
    altitude_m: float
    spacing_m: float = 100.0
    heading_deg: float = 0.0
    boundary_margin_m: float = 100.0


class AttackRunConfig(BaseModel):
    """Attack run geometry parameters."""

    approach_distance_m: float = 200.0
    exit_distance_m: float = 200.0
    release_acceptance_radius_m: float = 0.0  # 0 = use ArduPlane WP_RADIUS default
    fallback_drop_point: GeoPoint | None = None


# ── Top-level model ───────────────────────────────────────────────


class FieldProfile(BaseModel):
    """Complete field configuration with geographic validation."""

    name: str
    description: str = ""
    coordinate_system: str = "WGS84"
    boundary: BoundaryConfig
    landing: LandingConfig
    scan: ScanConfig
    attack_run: AttackRunConfig = AttackRunConfig()
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

        # Landing runway length
        if self.landing.runway_length_m <= 0:
            raise ValueError(
                f"runway_length_m must be positive, got {self.landing.runway_length_m}"
            )

        # Landing touchdown
        td = self.landing.touchdown_point
        if not point_in_polygon(td.lat, td.lon, polygon):
            raise FieldValidationError(
                "landing.touchdown_point",
                f"({td.lat}, {td.lon}) is outside the geofence boundary",
            )
        _validate_landing_approach_inside_geofence(self.landing, polygon)

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


def _validate_landing_approach_inside_geofence(
    landing: LandingConfig,
    polygon: list[GeoPoint],
) -> None:
    delta_alt = landing.approach_alt_m - landing.touchdown_point.alt_m
    if delta_alt <= 0:
        raise FieldValidationError(
            "landing.approach_alt_m",
            (
                "approach_alt_m "
                f"({landing.approach_alt_m}) must be above touchdown altitude ({landing.touchdown_point.alt_m})"
            ),
        )

    tangent = math.tan(math.radians(landing.glide_slope_deg))
    if not math.isfinite(tangent) or tangent <= 0:
        raise FieldValidationError(
            "landing.glide_slope_deg",
            f"invalid glide slope: {landing.glide_slope_deg}",
        )

    distance_m = delta_alt / tangent

    approach_lat, approach_lon = destination_point(
        landing.touchdown_point.lat,
        landing.touchdown_point.lon,
        (landing.heading_deg + 180.0) % 360.0,
        distance_m,
    )
    if not point_in_polygon(approach_lat, approach_lon, polygon):
        raise FieldValidationError(
            "landing.heading_deg",
            (
                "derived approach "
                f"({approach_lat:.6f}, {approach_lon:.6f}) is outside the geofence boundary"
            ),
        )


# ── Loader ────────────────────────────────────────────────────────

_DEFAULT_FIELDS_DIR = Path("data/fields")
_DEFAULT_SITL_PARAMS_NAME = "sitl_merged.param"


def field_profile_dir(name: str, base_dir: Path = _DEFAULT_FIELDS_DIR) -> Path:
    return base_dir / name


def field_profile_path(name: str, base_dir: Path = _DEFAULT_FIELDS_DIR) -> Path:
    return field_profile_dir(name, base_dir) / "field.json"


def sitl_params_path(name: str, base_dir: Path = _DEFAULT_FIELDS_DIR) -> Path:
    return field_profile_dir(name, base_dir) / _DEFAULT_SITL_PARAMS_NAME


def sitl_home_string(profile: FieldProfile) -> str:
    touchdown = profile.landing.touchdown_point
    return (
        f"{touchdown.lat:.6f},"
        f"{touchdown.lon:.6f},"
        f"{touchdown.alt_m:.6f},"
        f"{profile.landing.heading_deg:.6f}"
    )


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
    field_file = field_profile_path(name, base_dir)
    if not field_file.exists():
        raise ConfigError(f"Field configuration not found: {field_file}")

    raw = json.loads(field_file.read_text(encoding="utf-8"))
    return FieldProfile.model_validate(raw)
