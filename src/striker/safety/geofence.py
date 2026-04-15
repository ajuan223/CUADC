"""Geofence — polygon boundary checking using ray-casting algorithm."""

from __future__ import annotations

import math
from typing import TYPE_CHECKING

import structlog

if TYPE_CHECKING:
    from striker.config.field_profile import GeoPoint

logger = structlog.get_logger(__name__)


class Geofence:
    """Polygon-based geofence from field profile boundary.

    Parameters
    ----------
    polygon:
        List of GeoPoint vertices forming a closed polygon.
    """

    def __init__(self, polygon: list[GeoPoint]) -> None:
        self._polygon = polygon

    def is_inside(self, lat: float, lon: float) -> bool:
        """Return ``True`` if (lat, lon) is inside the geofence.

        Uses the ray-casting algorithm.
        """
        n = len(self._polygon)
        if n < 3:
            return False

        inside = False
        j = n - 1

        for i in range(n):
            yi, xi = self._polygon[i].lat, self._polygon[i].lon
            yj, xj = self._polygon[j].lat, self._polygon[j].lon

            if ((yi > lat) != (yj > lat)) and (
                lon < (xj - xi) * (lat - yi) / (yj - yi) + xi if (yj - yi) != 0 else lon <= xi
            ):
                inside = not inside

            j = i

        return inside

    def distance_to_boundary(self, lat: float, lon: float) -> float:
        """Approximate distance in meters from (lat, lon) to nearest boundary edge.

        Uses simplified equirectangular approximation for short distances.
        """
        min_dist = float("inf")
        n = len(self._polygon)

        for i in range(n):
            j = (i + 1) % n
            p1 = self._polygon[i]
            p2 = self._polygon[j]

            dist = _point_to_segment_distance(lat, lon, p1.lat, p1.lon, p2.lat, p2.lon)
            min_dist = min(min_dist, dist)

        return min_dist


def _point_to_segment_distance(
    lat: float, lon: float,
    lat1: float, lon1: float,
    lat2: float, lon2: float,
) -> float:
    """Distance in meters from point to line segment (equirectangular approx)."""
    # Convert to approximate meters
    lat_m = lat * 111_320  # meters per degree latitude
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
