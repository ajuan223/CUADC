"""Vision models — GpsTarget dataclass and validation."""

from __future__ import annotations

import time
from dataclasses import dataclass


@dataclass(frozen=True)
class GpsTarget:
    """GPS target from external solver."""

    lat: float
    lon: float
    confidence: float
    timestamp: float

    def __post_init__(self) -> None:
        validate_gps(self.lat, self.lon)
        if not (0.0 <= self.confidence <= 1.0):
            msg = f"Confidence must be [0, 1], got {self.confidence}"
            raise ValueError(msg)

    @classmethod
    def from_dict(cls, data: dict[str, float]) -> "GpsTarget":
        """Create from a JSON-decoded dict."""
        return cls(
            lat=data["lat"],
            lon=data["lon"],
            confidence=data.get("confidence", 1.0),
            timestamp=data.get("timestamp", time.monotonic()),
        )


def validate_gps(lat: float, lon: float) -> None:
    """Validate GPS coordinate ranges (RL-05).

    Raises
    ------
    ValueError
        If coordinates are out of valid range.
    """
    if not (-90 <= lat <= 90):
        msg = f"Latitude must be [-90, 90], got {lat}"
        raise ValueError(msg)
    if not (-180 <= lon <= 180):
        msg = f"Longitude must be [-180, 180], got {lon}"
        raise ValueError(msg)
