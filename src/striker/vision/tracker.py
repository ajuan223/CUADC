"""Drop point tracker — adaptive smoothing with sliding window median filter."""

from __future__ import annotations

import time
from collections import deque
from statistics import median

import structlog

logger = structlog.get_logger(__name__)


class DropPointTracker:
    """Sliding window median filter with adaptive frequency handling.

    Modes:
    - 0 Hz: no data, maintain last state, no drop point
    - Single: immediately adopt
    - Low freq (<1Hz): each update adopted directly
    - High freq (>1Hz): N-frame median smoothing

    Parameters
    ----------
    window_size:
        Size of the sliding window for median smoothing (default 5).
    stale_timeout_s:
        Seconds before drop point is considered expired (default 2.0).
    """

    def __init__(self, window_size: int = 5, stale_timeout_s: float = 2.0) -> None:
        self._window_size = window_size
        self._stale_timeout_s = stale_timeout_s
        self._lat_window: deque[float] = deque(maxlen=window_size)
        self._lon_window: deque[float] = deque(maxlen=window_size)
        self._last_update_time: float = 0.0
        self._last_lat: float = 0.0
        self._last_lon: float = 0.0
        self._has_data = False
        self._update_count = 0

    def push(self, lat: float, lon: float) -> None:
        """Push a new drop point observation."""
        now = time.monotonic()
        self._lat_window.append(lat)
        self._lon_window.append(lon)
        self._last_update_time = now
        self._last_lat = lat
        self._last_lon = lon
        self._has_data = True
        self._update_count += 1

    def get_smoothed_drop_point(self) -> tuple[float, float] | None:
        """Return the smoothed drop point coordinates, or None if stale/empty."""
        if not self._has_data:
            return None

        # Stale detection
        if time.monotonic() - self._last_update_time > self._stale_timeout_s:
            logger.debug("Drop point stale")
            return None

        # Single or low-frequency: adopt directly
        if len(self._lat_window) <= 1:
            return (self._last_lat, self._last_lon)

        # High frequency: median smoothing
        smoothed_lat = median(self._lat_window)
        smoothed_lon = median(self._lon_window)
        return (smoothed_lat, smoothed_lon)

    @property
    def last_update_time(self) -> float:
        """Monotonic timestamp of last update."""
        return self._last_update_time

    @property
    def update_count(self) -> int:
        """Total number of pushes."""
        return self._update_count
