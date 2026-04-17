"""Geo utilities — haversine distance, bearing, destination point."""

from __future__ import annotations

import math
from typing import TYPE_CHECKING, Protocol

if TYPE_CHECKING:
    from striker.config.field_profile import GeoPoint


class _LatLonPoint(Protocol):
    lat: float
    lon: float


def _coords(point: GeoPoint | tuple[float, float] | _LatLonPoint) -> tuple[float, float]:
    if isinstance(point, tuple):
        return (point[0], point[1])
    return (point.lat, point.lon)


def haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculate haversine distance between two GPS points in meters."""
    R = 6_371_000  # Earth radius in meters
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = (
        math.sin(dlat / 2) ** 2
        + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon / 2) ** 2
    )
    c = 2 * math.asin(math.sqrt(a))
    return R * c


def calculate_bearing(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculate bearing from point 1 to point 2 in degrees [0, 360)."""
    dlon = math.radians(lon2 - lon1)
    lat1_r = math.radians(lat1)
    lat2_r = math.radians(lat2)
    x = math.sin(dlon) * math.cos(lat2_r)
    y = math.cos(lat1_r) * math.sin(lat2_r) - math.sin(lat1_r) * math.cos(lat2_r) * math.cos(dlon)
    bearing = math.degrees(math.atan2(x, y))
    return (bearing + 360) % 360


def destination_point(lat: float, lon: float, bearing: float, distance: float) -> tuple[float, float]:
    """Calculate destination point given start, bearing (deg), and distance (m).

    Returns (lat, lon) of the destination.
    """
    R = 6_371_000
    lat_r = math.radians(lat)
    lon_r = math.radians(lon)
    bearing_r = math.radians(bearing)
    d = distance / R

    dest_lat = math.asin(
        math.sin(lat_r) * math.cos(d) + math.cos(lat_r) * math.sin(d) * math.cos(bearing_r)
    )
    dest_lon = lon_r + math.atan2(
        math.sin(bearing_r) * math.sin(d) * math.cos(lat_r),
        math.cos(d) - math.sin(lat_r) * math.sin(dest_lat),
    )
    return (math.degrees(dest_lat), math.degrees(dest_lon))


def validate_gps(lat: float, lon: float) -> bool:
    """Return True if GPS coordinates are in valid range (RL-05)."""
    return -90 <= lat <= 90 and -180 <= lon <= 180


def point_to_segment_distance(
    lat: float, lon: float,
    lat1: float, lon1: float,
    lat2: float, lon2: float,
) -> float:
    """Distance in meters from point to line segment (equirectangular approx).

    Used for geofence boundary distance calculations.
    """
    # Convert to approximate meters
    lat_m = lat * 111_320
    lon_m = lon * 111_320 * math.cos(math.radians(lat))
    lat1_m = lat1 * 111_320
    lon1_m = lon1 * 111_320 * math.cos(math.radians(lat1))
    lat2_m = lat2 * 111_320
    lon2_m = lon2 * 111_320 * math.cos(math.radians(lat2))

    dx = lon2_m - lon1_m
    dy = lat2_m - lat1_m

    if dx == 0 and dy == 0:
        return math.sqrt((lon_m - lon1_m) ** 2 + (lat_m - lat1_m) ** 2)

    t = max(0, min(1, ((lon_m - lon1_m) * dx + (lat_m - lat1_m) * dy) / (dx * dx + dy * dy)))
    proj_x = lon1_m + t * dx
    proj_y = lat1_m + t * dy

    return math.sqrt((lon_m - proj_x) ** 2 + (lat_m - proj_y) ** 2)


def nearest_boundary_distance(
    lat: float, lon: float,
    polygon: list[GeoPoint] | list[tuple[float, float]],
) -> float:
    """Return distance in meters to the nearest edge of a polygon."""
    min_dist = float("inf")
    n = len(polygon)
    for i in range(n):
        j = (i + 1) % n
        p_i, p_j = polygon[i], polygon[j]
        yi, xi = _coords(p_i)
        yj, xj = _coords(p_j)
        dist = point_to_segment_distance(lat, lon, yi, xi, yj, xj)
        min_dist = min(min_dist, dist)
    return min_dist
