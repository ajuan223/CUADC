"""Forced strike point — generate random point inside geofence polygon."""

from __future__ import annotations

import random
from collections.abc import Sequence

from striker.utils.geo import nearest_boundary_distance
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
    rng = random.Random(seed) if seed is not None else random.Random()

    # Bounding box
    lats = [p.lat if hasattr(p, "lat") else p[0] for p in polygon]
    lons = [p.lon if hasattr(p, "lon") else p[1] for p in polygon]
    min_lat, max_lat = min(lats), max(lats)
    min_lon, max_lon = min(lons), max(lons)

    # Buffer in degrees (approximate)
    buffer_deg = buffer_m / 111_320.0

    max_attempts = 10_000
    for _ in range(max_attempts):
        lat = rng.uniform(min_lat + buffer_deg, max_lat - buffer_deg)
        lon = rng.uniform(min_lon + buffer_deg, max_lon - buffer_deg)

        if point_in_polygon(lat, lon, polygon):
            # Verify safety buffer: point must be at least buffer_m from boundary
            boundary_dist = nearest_boundary_distance(lat, lon, list(polygon))
            if boundary_dist >= buffer_m:
                return (lat, lon)

    msg = f"Failed to generate point inside polygon after {max_attempts} attempts"
    raise ValueError(msg)
