"""Ballistic solver — free-fall parabolic trajectory with wind compensation.

Computes release point upstream of target using:
- Fall time: ``t_fall = sqrt(2h/g)``
- Displacement: ``d = (velocity + wind) * t_fall``
- Release point via geopy geodesic reverse projection
"""

from __future__ import annotations

import math

import structlog
from geopy.distance import geodesic

logger = structlog.get_logger(__name__)


class BallisticCalculator:
    """Free-fall parabolic ballistic solver with wind compensation.

    Parameters
    ----------
    gravity:
        Gravitational acceleration (default 9.81 m/s^2).
    """

    def __init__(self, gravity: float = 9.81) -> None:
        self._gravity = gravity

    def calculate_release_point(
        self,
        target_lat: float,
        target_lon: float,
        altitude_m: float,
        velocity_n_mps: float = 0.0,
        velocity_e_mps: float = 0.0,
        wind_n_mps: float = 0.0,
        wind_e_mps: float = 0.0,
    ) -> tuple[float, float]:
        """Calculate the release point upstream of the target.

        Parameters
        ----------
        target_lat, target_lon:
            Target GPS coordinates.
        altitude_m:
            Altitude above target in meters.
        velocity_n_mps, velocity_e_mps:
            Aircraft velocity in NED frame (m/s).
        wind_n_mps, wind_e_mps:
            Wind velocity in NED frame (m/s).

        Returns
        -------
        tuple[float, float]
            (lat, lon) of the release point.
        """
        # Edge case: altitude <= 0
        if altitude_m <= 0:
            logger.warning("Altitude <= 0, returning target unchanged", alt=altitude_m)
            return (target_lat, target_lon)

        # Fall time
        t_fall = math.sqrt(2 * altitude_m / self._gravity)

        # Displacement during fall
        d_north = (velocity_n_mps + wind_n_mps) * t_fall
        d_east = (velocity_e_mps + wind_e_mps) * t_fall

        # Total displacement and bearing from release to target
        displacement_m = math.sqrt(d_north ** 2 + d_east ** 2)

        if displacement_m < 0.01:
            return (target_lat, target_lon)

        # Bearing from release point to target (release is upstream)
        bearing_to_target = math.degrees(math.atan2(d_east, d_north)) % 360

        # Release point is upstream: project from target in opposite direction
        release_bearing = (bearing_to_target + 180) % 360

        result = geodesic(meters=displacement_m).destination(
            (target_lat, target_lon), release_bearing,
        )

        logger.info(
            "Release point calculated",
            t_fall=t_fall,
            displacement_m=displacement_m,
            release_lat=result.latitude,
            release_lon=result.longitude,
        )

        return (result.latitude, result.longitude)
