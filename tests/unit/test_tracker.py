"""Unit tests for target tracker."""

from __future__ import annotations

import time

import pytest

from striker.vision.tracker import TargetTracker


class TestTargetTracker:
    def test_single_push_returns_target(self) -> None:
        tracker = TargetTracker()
        tracker.push(30.0, 120.0)
        result = tracker.get_smoothed_target()
        assert result is not None
        assert result == (30.0, 120.0)

    def test_high_frequency_median_smoothing(self) -> None:
        tracker = TargetTracker(window_size=5, stale_timeout_s=10.0)
        tracker.push(30.0, 120.0)
        tracker.push(30.1, 120.1)
        tracker.push(30.2, 120.2)
        tracker.push(29.9, 119.9)
        tracker.push(30.05, 120.05)
        result = tracker.get_smoothed_target()
        assert result is not None
        # Median of [29.9, 30.0, 30.05, 30.1, 30.2] = 30.05
        assert abs(result[0] - 30.05) < 0.01

    def test_low_frequency_adopted_directly(self) -> None:
        tracker = TargetTracker(window_size=5)
        tracker.push(30.0, 120.0)
        # Only one value — should be adopted directly
        result = tracker.get_smoothed_target()
        assert result == (30.0, 120.0)

    def test_no_data_returns_none(self) -> None:
        tracker = TargetTracker()
        assert tracker.get_smoothed_target() is None

    def test_stale_detection(self) -> None:
        tracker = TargetTracker(stale_timeout_s=0.01)
        tracker.push(30.0, 120.0)
        # Force stale by manipulating time
        tracker._last_update_time = time.monotonic() - 1.0
        assert tracker.get_smoothed_target() is None

    def test_update_count(self) -> None:
        tracker = TargetTracker()
        tracker.push(30.0, 120.0)
        tracker.push(30.1, 120.1)
        assert tracker.update_count == 2
