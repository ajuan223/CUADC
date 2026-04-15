"""Geofence — polygon boundary checking using ray-casting algorithm."""

from __future__ import annotations

from typing import TYPE_CHECKING

import structlog

from striker.utils.geo import nearest_boundary_distance

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
        """Approximate distance in meters from (lat, lon) to nearest boundary edge."""
        polygon_tuples = [(p.lat, p.lon) for p in self._polygon]
        return nearest_boundary_distance(lat, lon, polygon_tuples)
