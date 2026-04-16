"""Fallback drop point — compute midpoint between scan end and landing reference."""

from __future__ import annotations

import math

from geopy.distance import geodesic

from striker.config.field_profile import GeoPoint


def compute_fallback_drop_point(
    scan_end_point: GeoPoint,
    landing_reference_point: GeoPoint,
) -> tuple[float, float]:
    """Compute the fallback drop point as the geographic midpoint.

    Calculates the geodesic midpoint between the last scan waypoint
    and the landing reference point using geopy.

    Parameters
    ----------
    scan_end_point:
        The last scan waypoint (GeoPoint with lat/lon).
    landing_reference_point:
        The landing reference point (GeoPoint with lat/lon).

    Returns
    -------
    tuple[float, float]
        (lat, lon) of the midpoint.
    """
    p1 = (scan_end_point.lat, scan_end_point.lon)
    p2 = (landing_reference_point.lat, landing_reference_point.lon)

    dist = geodesic(p1, p2)
    bearing = _bearing(p1, p2)
    midpoint = geodesic(kilometers=dist.kilometers / 2).destination(p1, bearing)

    return (midpoint.latitude, midpoint.longitude)


def _bearing(p1: tuple[float, float], p2: tuple[float, float]) -> float:
    """Calculate initial bearing from p1 to p2 in degrees."""
    lat1, lon1 = math.radians(p1[0]), math.radians(p1[1])
    lat2, lon2 = math.radians(p2[0]), math.radians(p2[1])
    dlon = lon2 - lon1
    x = math.sin(dlon) * math.cos(lat2)
    y = math.cos(lat1) * math.sin(lat2) - math.sin(lat1) * math.cos(lat2) * math.cos(dlon)
    return (math.degrees(math.atan2(x, y)) + 360) % 360
