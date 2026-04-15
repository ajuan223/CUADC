"""Timing utilities — precise timestamps and rate limiting."""

from __future__ import annotations

import time


def precise_timestamp() -> float:
    """Return a monotonic timestamp with maximum precision."""
    return time.monotonic()


class RateLimiter:
    """Enforce a minimum interval between operations.

    Parameters
    ----------
    interval_s:
        Minimum seconds between allowed operations.
    """

    def __init__(self, interval_s: float) -> None:
        self._interval_s = interval_s
        self._last_time: float = 0.0

    def ready(self) -> bool:
        """Return True if enough time has elapsed since last operation."""
        now = time.monotonic()
        if now - self._last_time >= self._interval_s:
            self._last_time = now
            return True
        return False
