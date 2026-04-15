"""Forced strike point — generate random point inside geofence polygon."""

from __future__ import annotations

import math
import random
from typing import Sequence

from striker.utils.point_in_polygon import point_in_polygon


def generate_forced_strike_point(
    polygon: Sequence[tuple[float, float]],
    buffer_m: float = 50.0,
    seed: int | None = None,
) -> tuple[float, float]:
    """Generate a random point inside polygon with safety buffer exclusion.

    Uses bounding box rejection sampling: generate points in the bbox
    and reject those outside the polygon or within the buffer zone.

    Parameters
    ----------
    polygon:
        Closed polygon as sequence of (lat, lon) tuples.
    buffer_m:
        Safety buffer in meters from boundary — generated points
        must be at least this far from edges.
    seed:
        Optional deterministic seed for reproducibility.

    Returns
    -------
    tuple[float, float]
        (lat, lon) of the generated point inside the polygon.

    Raises
    ------
    ValueError
        If no valid point found after max attempts.
    """
    if seed is not None:
        rng = random.Random(seed)
    else:
        rng = random.Random()

    # Bounding box
    lats = [p[0] for p in polygon]
    lons = [p[1] for p in polygon]
    min_lat, max_lat = min(lats), max(lats)
    min_lon, max_lon = min(lons), max(lons)

    # Buffer in degrees (approximate)
    buffer_deg = buffer_m / 111_320.0

    max_attempts = 10_000
    for _ in range(max_attempts):
        lat = rng.uniform(min_lat + buffer_deg, max_lat - buffer_deg)
        lon = rng.uniform(min_lon + buffer_deg, max_lon - buffer_deg)

        if point_in_polygon(lat, lon, polygon):
            return (lat, lon)

    msg = f"Failed to generate point inside polygon after {max_attempts} attempts"
    raise ValueError(msg)
