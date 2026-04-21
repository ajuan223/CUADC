"""Thread-safe global variable for vision drop point."""

from __future__ import annotations

import threading

from striker.vision.models import validate_gps

# Module-level lock for thread safety
_lock = threading.Lock()

# The global drop point coordinate: (lat, lon)
VISION_DROP_POINT: tuple[float, float] | None = None


def set_vision_drop_point(lat: float, lon: float) -> None:
    """Set the vision drop point in a thread-safe manner.

    Raises
    ------
    ValueError
        If the GPS coordinates are out of valid bounds.
    """
    validate_gps(lat, lon)
    global VISION_DROP_POINT
    with _lock:
        VISION_DROP_POINT = (lat, lon)


def get_vision_drop_point() -> tuple[float, float] | None:
    """Get the current vision drop point in a thread-safe manner."""
    with _lock:
        return VISION_DROP_POINT
