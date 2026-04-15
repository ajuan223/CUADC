"""Point-in-polygon test using ray-casting algorithm."""

from __future__ import annotations

from collections.abc import Sequence


def point_in_polygon(lat: float, lon: float, polygon: Sequence[tuple[float, float]]) -> bool:
    """Return True if (lat, lon) is inside polygon using ray-casting.

    Parameters
    ----------
    lat, lon:
        Test point coordinates.
    polygon:
        Sequence of (lat, lon) vertex tuples. Assumed closed.

    Handles edge cases: point on boundary considered inside.
    """
    n = len(polygon)
    if n < 3:
        return False

    inside = False
    j = n - 1

    for i in range(n):
        p_i, p_j = polygon[i], polygon[j]
        yi, xi = (p_i.lat, p_i.lon) if hasattr(p_i, "lat") else p_i
        yj, xj = (p_j.lat, p_j.lon) if hasattr(p_j, "lat") else p_j

        # Check if ray from point crosses this edge
        if ((yi > lat) != (yj > lat)) and (
            lon < (xj - xi) * (lat - yi) / (yj - yi) + xi if (yj - yi) != 0 else lon <= xi
        ):
            inside = not inside

        j = i

    return inside
