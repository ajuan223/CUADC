"""Geo utilities — haversine distance, bearing, destination point."""

from __future__ import annotations

import math


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
