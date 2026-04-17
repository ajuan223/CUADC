"""Procedural mission geometry — derive takeoff, scan, and landing from field facts.

Algorithms:
- Landing approach: Glide Slope Reverse Projection
- Scan path: Boustrophedon Coverage Path Planning (Coombes 2017)
- Takeoff: Runway-Aligned Takeoff Geometry
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import TYPE_CHECKING

import structlog

from striker.config.field_profile import point_in_polygon
from striker.utils.geo import destination_point

if TYPE_CHECKING:
    from striker.config.field_profile import FieldProfile, GeoPoint

logger = structlog.get_logger(__name__)


# ── Result dataclass ──────────────────────────────────────────────


@dataclass
class MissionGeometryResult:
    """Output of procedural mission geometry generation."""

    # Raw waypoint data (lat, lon, alt_m tuples)
    takeoff_start: tuple[float, float, float]
    takeoff_climbout: tuple[float, float, float]
    scan_waypoints: list[tuple[float, float, float]]
    landing_approach: tuple[float, float, float]
    landing_touchdown: tuple[float, float, float]

    # Flags
    use_do_land_start: bool

    # Key sequence indices (populated during mission assembly)
    takeoff_start_seq: int = 0
    scan_start_seq: int = 0
    scan_end_seq: int = 0
    landing_start_seq: int = 0

    def compute_indices(self, include_dummy_home: bool = True) -> None:
        """Compute sequence indices based on mission item count."""
        seq = 1 if include_dummy_home else 0  # seq 0 = dummy HOME
        self.takeoff_start_seq = seq
        seq += 2  # takeoff + climbout
        self.scan_start_seq = seq
        seq += len(self.scan_waypoints)
        self.scan_end_seq = seq - 1
        self.landing_start_seq = seq


# ── Landing approach derivation ───────────────────────────────────


def derive_landing_approach(
    touchdown_lat: float,
    touchdown_lon: float,
    touchdown_alt_m: float,
    heading_deg: float,
    approach_alt_m: float,
    glide_slope_deg: float,
    geofence_polygon: list[GeoPoint],
) -> tuple[float, float, float]:
    """Derive landing approach waypoint from touchdown + glide slope.

    Returns (lat, lon, alt_m) of the approach gate.
    Raises ValueError if geometry is invalid.
    """
    delta_alt = approach_alt_m - touchdown_alt_m
    if delta_alt <= 0:
        raise ValueError(
            f"Approach alt ({approach_alt_m}) must be above touchdown alt ({touchdown_alt_m})"
        )

    tangent = math.tan(math.radians(glide_slope_deg))
    if not math.isfinite(tangent) or tangent <= 0:
        raise ValueError(f"Invalid glide slope ({glide_slope_deg})")

    distance = delta_alt / tangent

    reverse_heading = (heading_deg + 180.0) % 360.0
    approach_lat, approach_lon = destination_point(
        touchdown_lat, touchdown_lon, reverse_heading, distance
    )

    if not point_in_polygon(approach_lat, approach_lon, geofence_polygon):
        raise ValueError(
            f"Derived approach ({approach_lat:.6f}, {approach_lon:.6f}) is outside geofence"
        )

    logger.info(
        "Landing approach derived",
        lat=approach_lat,
        lon=approach_lon,
        alt=approach_alt_m,
        distance_m=distance,
    )
    return approach_lat, approach_lon, approach_alt_m


# ── Boustrophedon scan path generation ────────────────────────────


def _line_polygon_intersections(
    line_y: float, polygon: list[tuple[float, float]]
) -> list[float]:
    """Find x-intersections of a horizontal line y=line_y with polygon edges."""
    xs: list[float] = []
    n = len(polygon)
    for i in range(n):
        x1, y1 = polygon[i]
        x2, y2 = polygon[(i + 1) % n]
        if ((y1 <= line_y < y2) or (y2 <= line_y < y1)) and y2 != y1:
            t = (line_y - y1) / (y2 - y1)
            xs.append(x1 + t * (x2 - x1))
    xs.sort()
    return xs


def _point_in_polygon_xy(x: float, y: float, polygon: list[tuple[float, float]]) -> bool:
    """Return True if a planar point lies inside or on the edge of a polygon."""
    inside = False
    n = len(polygon)

    for i in range(n):
        x1, y1 = polygon[i]
        x2, y2 = polygon[(i + 1) % n]

        cross = (x - x1) * (y2 - y1) - (y - y1) * (x2 - x1)
        if abs(cross) < 1e-9:
            min_x = min(x1, x2) - 1e-9
            max_x = max(x1, x2) + 1e-9
            min_y = min(y1, y2) - 1e-9
            max_y = max(y1, y2) + 1e-9
            if min_x <= x <= max_x and min_y <= y <= max_y:
                return True

        if ((y1 > y) != (y2 > y)) and (
            x < (x2 - x1) * (y - y1) / (y2 - y1) + x1 if (y2 - y1) != 0 else x <= x1
        ):
            inside = not inside

    return inside


def generate_boustrophedon_scan(
    boundary_polygon: list[tuple[float, float]],
    scan_alt_m: float,
    scan_spacing_m: float,
    scan_heading_deg: float,
) -> list[tuple[float, float, float]]:
    """Generate Boustrophedon scan waypoints over a polygon.

    Args:
        boundary_polygon: Closed list of (lat, lon) vertices.
        scan_alt_m: Flight altitude (added to each waypoint).
        scan_spacing_m: Spacing between sweep lines in meters.
        scan_heading_deg: Heading of sweep lines (flight goes perpendicular).

    Returns:
        List of (lat, lon, alt_m) waypoints in flyable order.
    """
    if len(boundary_polygon) < 3:
        raise ValueError("Polygon must have at least 3 vertices")
    if scan_spacing_m <= 0:
        raise ValueError(f"Scan spacing must be positive, got {scan_spacing_m}")

    # Compute centroid for rotation reference
    clat = sum(p[0] for p in boundary_polygon) / len(boundary_polygon)
    clon = sum(p[1] for p in boundary_polygon) / len(boundary_polygon)

    # Rotation angle: rotate so sweep lines go horizontal
    rot_angle = -math.radians(scan_heading_deg - 90.0)

    # Convert polygon to local meters and rotate
    m_per_deg_lat = 110540.0
    m_per_deg_lon = 111320.0 * math.cos(math.radians(clat))

    rot_poly: list[tuple[float, float]] = []
    for lat, lon in boundary_polygon:
        x = (lon - clon) * m_per_deg_lon
        y = (lat - clat) * m_per_deg_lat
        xr = x * math.cos(rot_angle) - y * math.sin(rot_angle)
        yr = x * math.sin(rot_angle) + y * math.cos(rot_angle)
        rot_poly.append((xr, yr))

    # Find vertical extent of rotated polygon
    ys = [p[1] for p in rot_poly]
    y_min, y_max = min(ys), max(ys)

    # Generate sweep lines
    waypoints: list[tuple[float, float, float]] = []
    sweep_idx = 0
    y = y_min + scan_spacing_m / 2  # offset half-spacing from edge

    while y <= y_max - scan_spacing_m / 4:
        intersections = _line_polygon_intersections(y, rot_poly)
        for i in range(0, len(intersections) - 1, 2):
            left_x = intersections[i]
            right_x = intersections[i + 1]
            midpoint_x = (left_x + right_x) / 2.0
            if not _point_in_polygon_xy(midpoint_x, y, rot_poly):
                continue

            segment_width = right_x - left_x
            inset_m = min(0.1, max(segment_width / 10.0, 0.0))
            entry_x = left_x + inset_m
            exit_x = right_x - inset_m
            if entry_x > exit_x:
                entry_x = midpoint_x
                exit_x = midpoint_x

            # Alternate direction for Boustrophedon
            if sweep_idx % 2 == 1:
                entry_x, exit_x = exit_x, entry_x
            for wx in [entry_x, exit_x]:
                # Inverse rotate back to geographic
                ix = wx * math.cos(-rot_angle) - y * math.sin(-rot_angle)
                iy = wx * math.sin(-rot_angle) + y * math.cos(-rot_angle)
                lat = clat + iy / m_per_deg_lat
                lon = clon + ix / m_per_deg_lon
                waypoints.append((lat, lon, scan_alt_m))
        sweep_idx += 1
        y += scan_spacing_m

    logger.info(
        "Boustrophedon scan generated",
        waypoints=len(waypoints),
        sweeps=sweep_idx,
        spacing_m=scan_spacing_m,
    )
    return waypoints


# ── Runway-aligned takeoff geometry ───────────────────────────────


def generate_takeoff_geometry(
    touchdown_lat: float,
    touchdown_lon: float,
    touchdown_alt_m: float,
    heading_deg: float,
    runway_length_m: float,
    takeoff_alt_m: float,
) -> dict[str, float]:
    """Generate fixed-wing takeoff geometry from runway facts.

    Returns dict with takeoff start and climb-out waypoint coordinates.
    """
    if runway_length_m <= 0:
        raise ValueError(f"Runway length must be positive, got {runway_length_m}")
    if takeoff_alt_m <= touchdown_alt_m:
        raise ValueError(
            f"Takeoff alt ({takeoff_alt_m}) must be above runway alt ({touchdown_alt_m})"
        )

    reverse_heading = (heading_deg + 180.0) % 360.0

    # Start point: 40% behind the midpoint along the runway
    mid_lat, mid_lon = destination_point(
        touchdown_lat, touchdown_lon, heading_deg, runway_length_m / 2
    )
    start_lat, start_lon = destination_point(
        mid_lat, mid_lon, reverse_heading, runway_length_m * 0.4
    )

    # Climb-out point: beyond far end of runway
    climbout_lat, climbout_lon = destination_point(
        touchdown_lat, touchdown_lon, heading_deg, runway_length_m
    )

    logger.info(
        "Takeoff geometry generated",
        start_lat=start_lat,
        start_lon=start_lon,
        climbout_lat=climbout_lat,
        climbout_lon=climbout_lon,
        heading=heading_deg,
    )
    return {
        "start_lat": start_lat,
        "start_lon": start_lon,
        "start_alt_m": touchdown_alt_m,
        "climbout_lat": climbout_lat,
        "climbout_lon": climbout_lon,
        "climbout_alt_m": takeoff_alt_m,
        "heading_deg": heading_deg,
    }


# ── Top-level entry point ─────────────────────────────────────────


def generate_mission_geometry(field_profile: FieldProfile) -> MissionGeometryResult:
    """Generate all mission geometry from field profile facts.

    This is the single entry point for procedural mission generation.
    """
    landing = field_profile.landing
    td = landing.touchdown_point
    polygon = field_profile.boundary.polygon
    scan_cfg = field_profile.scan

    # Landing approach
    approach_lat, approach_lon, approach_alt = derive_landing_approach(
        touchdown_lat=td.lat,
        touchdown_lon=td.lon,
        touchdown_alt_m=td.alt_m,
        heading_deg=landing.heading_deg,
        approach_alt_m=landing.approach_alt_m,
        glide_slope_deg=landing.glide_slope_deg,
        geofence_polygon=polygon,
    )

    # Boustrophedon scan
    boundary_tuples = [(p.lat, p.lon) for p in polygon]
    scan_wps = generate_boustrophedon_scan(
        boundary_polygon=boundary_tuples,
        scan_alt_m=scan_cfg.altitude_m,
        scan_spacing_m=scan_cfg.spacing_m,
        scan_heading_deg=scan_cfg.heading_deg,
    )

    # Takeoff geometry
    takeoff_heading = (landing.heading_deg + 180.0) % 360.0
    takeoff = generate_takeoff_geometry(
        touchdown_lat=td.lat,
        touchdown_lon=td.lon,
        touchdown_alt_m=td.alt_m,
        heading_deg=takeoff_heading,
        runway_length_m=landing.runway_length_m,
        takeoff_alt_m=scan_cfg.altitude_m,
    )

    result = MissionGeometryResult(
        takeoff_start=(takeoff["start_lat"], takeoff["start_lon"], takeoff["start_alt_m"]),
        takeoff_climbout=(
            takeoff["climbout_lat"],
            takeoff["climbout_lon"],
            takeoff["climbout_alt_m"],
        ),
        scan_waypoints=scan_wps,
        landing_approach=(approach_lat, approach_lon, approach_alt),
        landing_touchdown=(td.lat, td.lon, td.alt_m),
        use_do_land_start=landing.use_do_land_start,
    )
    result.compute_indices()
    logger.info(
        "Mission geometry generated",
        scan_waypoints=len(scan_wps),
        takeoff_start_seq=result.takeoff_start_seq,
        scan_start_seq=result.scan_start_seq,
        landing_start_seq=result.landing_start_seq,
    )
    return result
