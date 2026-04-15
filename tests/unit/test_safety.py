"""Unit tests for safety checks and monitor."""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from striker.core.events import EmergencyEvent, OverrideEvent
from striker.safety.checks import (
    AirspeedCheck,
    BatteryCheck,
    CheckResult,
    GeofenceCheck,
    GPSCheck,
    HeartbeatCheck,
)
from striker.safety.override_detector import OverrideDetector


# ── BatteryCheck ──────────────────────────────────────────────────


class TestBatteryCheck:
    def test_triggers_emergency_on_low_voltage(self) -> None:
        check = BatteryCheck(min_voltage_v=11.1)
        battery = MagicMock()
        battery.voltage_v = 10.5
        result = check.check(battery)
        assert not result.passed
        assert "10.5" in result.message

    def test_passes_on_normal_voltage(self) -> None:
        check = BatteryCheck(min_voltage_v=11.1)
        battery = MagicMock()
        battery.voltage_v = 12.6
        result = check.check(battery)
        assert result.passed


# ── GPSCheck ──────────────────────────────────────────────────────


class TestGPSCheck:
    def test_fails_on_no_fix(self) -> None:
        check = GPSCheck(min_fix_type=3)
        result = check.check(fix_type=1, satellites=12)
        assert not result.passed

    def test_passes_on_3d_fix(self) -> None:
        check = GPSCheck(min_fix_type=3)
        result = check.check(fix_type=3, satellites=10)
        assert result.passed


# ── HeartbeatCheck ────────────────────────────────────────────────


class TestHeartbeatCheck:
    def test_healthy(self) -> None:
        check = HeartbeatCheck(is_healthy_fn=lambda: True)
        result = check.check()
        assert result.passed

    def test_unhealthy(self) -> None:
        check = HeartbeatCheck(is_healthy_fn=lambda: False)
        result = check.check()
        assert not result.passed


# ── AirspeedCheck ─────────────────────────────────────────────────


class TestAirspeedCheck:
    def test_below_stall_speed(self) -> None:
        check = AirspeedCheck(stall_speed_mps=10.0)
        speed = MagicMock()
        speed.airspeed_mps = 8.0
        result = check.check(speed)
        assert not result.passed

    def test_above_stall_speed(self) -> None:
        check = AirspeedCheck(stall_speed_mps=10.0)
        speed = MagicMock()
        speed.airspeed_mps = 15.0
        result = check.check(speed)
        assert result.passed


# ── OverrideDetector ──────────────────────────────────────────────


class TestOverrideDetector:
    def test_emits_event_on_manual_mode(self) -> None:
        events: list[OverrideEvent] = []
        detector = OverrideDetector(
            override_modes={"MANUAL"},
            on_override=events.append,
        )
        # First call just sets baseline
        assert detector.check_mode("AUTO") is None
        # Mode change to MANUAL triggers override
        event = detector.check_mode("MANUAL")
        assert event is not None
        assert isinstance(event, OverrideEvent)
        assert events  # callback was called

    def test_no_event_on_auto_mode(self) -> None:
        detector = OverrideDetector(override_modes={"MANUAL"})
        detector.check_mode("AUTO")
        result = detector.check_mode("GUIDED")
        assert result is None

    def test_no_event_same_mode(self) -> None:
        detector = OverrideDetector(override_modes={"MANUAL"})
        detector.check_mode("AUTO")
        result = detector.check_mode("AUTO")
        assert result is None
