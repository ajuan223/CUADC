"""Unit tests for timing utilities."""

from __future__ import annotations

import time

import pytest

from striker.utils.timing import RateLimiter, precise_timestamp


class TestPreciseTimestamp:
    def test_monotonically_increasing(self) -> None:
        t1 = precise_timestamp()
        t2 = precise_timestamp()
        assert t2 >= t1


class TestRateLimiter:
    def test_enforces_interval(self) -> None:
        limiter = RateLimiter(interval_s=0.5)
        assert limiter.ready() is True  # first call always ready
        assert limiter.ready() is False  # too soon

    def test_ready_after_interval(self) -> None:
        limiter = RateLimiter(interval_s=0.01)
        limiter.ready()
        time.sleep(0.02)
        assert limiter.ready() is True
