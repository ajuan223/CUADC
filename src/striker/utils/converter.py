"""Coordinate converter — NED ↔ WGS-84 with reference point."""

from __future__ import annotations

import math


class CoordConverter:
    """Convert between NED (North-East-Down) meters and WGS-84 GPS.

    Uses a reference point for flat-earth approximation suitable
    for small areas (< 10 km).

    Parameters
    ----------
    ref_lat, ref_lon:
        Reference point in WGS-84 degrees.
    """

    def __init__(self, ref_lat: float, ref_lon: float) -> None:
        self._ref_lat = ref_lat
        self._ref_lon = ref_lon
        # Meters per degree at reference latitude
        self._m_per_deg_lat = 111_320.0
        self._m_per_deg_lon = 111_320.0 * math.cos(math.radians(ref_lat))

    def ned_to_gps(self, north_m: float, east_m: float) -> tuple[float, float]:
        """Convert NED offsets to GPS coordinates."""
        lat = self._ref_lat + north_m / self._m_per_deg_lat
        lon = self._ref_lon + east_m / self._m_per_deg_lon
        return (lat, lon)

    def gps_to_ned(self, lat: float, lon: float) -> tuple[float, float]:
        """Convert GPS coordinates to NED offsets from reference."""
        north_m = (lat - self._ref_lat) * self._m_per_deg_lat
        east_m = (lon - self._ref_lon) * self._m_per_deg_lon
        return (north_m, east_m)

    def map_pixel_to_gps(
        self, pixel_x: int, pixel_y: int, camera_params: dict[str, float],
    ) -> tuple[float, float]:
        """Map pixel coordinates to GPS (reserved — requires camera model)."""
        # Stub — would need camera intrinsic/extrinsic parameters
        return (self._ref_lat, self._ref_lon)
