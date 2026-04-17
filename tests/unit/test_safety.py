"""Unit tests for safety checks and monitor."""

from __future__ import annotations

import asyncio
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
from striker.safety.monitor import SafetyMonitor
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


class TestSafetyMonitor:
    @pytest.mark.asyncio
    async def test_stop_prevents_emergency_event_after_checks(self) -> None:
        monitor = SafetyMonitor(geofence=MagicMock(), check_interval_s=10.0)
        events: list[object] = []
        monitor.set_event_callback(events.append)
        monitor._running = True

        monitor.stop()
        monitor._process_results([CheckResult(name="heartbeat", passed=False, message="timeout")])

        assert events == []

    @pytest.mark.asyncio
    async def test_override_relinquishes_autonomy(self) -> None:
        monitor = SafetyMonitor(geofence=MagicMock())
        context = MagicMock()
        context.connection.flightmode = "AUTO"
        context.connection.relinquish_autonomy = MagicMock()
        events: list[object] = []
        monitor.set_event_callback(events.append)

        await monitor._run_checks(context)
        context.connection.flightmode = "MANUAL"
        await monitor._run_checks(context)

        context.connection.relinquish_autonomy.assert_called_once_with("Mode switched to MANUAL")
        assert isinstance(events[0], OverrideEvent)

    @pytest.mark.asyncio
    async def test_initial_manual_mode_does_not_trigger_override(self) -> None:
        monitor = SafetyMonitor(geofence=MagicMock())
        context = MagicMock()
        context.connection.flightmode = "MANUAL"
        context.connection.relinquish_autonomy = MagicMock()
        events: list[object] = []
        monitor.set_event_callback(events.append)

        await monitor._run_checks(context)

        context.connection.relinquish_autonomy.assert_not_called()
        assert events == []


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

    def test_initial_manual_mode_is_not_immediate_override(self) -> None:
        detector = OverrideDetector(override_modes={"MANUAL"})
        assert detector.check_mode("MANUAL") is None

    def test_manual_from_non_autonomous_mode_is_not_override(self) -> None:
        detector = OverrideDetector(override_modes={"MANUAL"})
        detector.check_mode("INITIALISING")
        assert detector.check_mode("MANUAL") is None
