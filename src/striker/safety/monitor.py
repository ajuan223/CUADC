"""Safety monitor — continuous coroutine running all safety checks."""

from __future__ import annotations

import asyncio
from collections.abc import Callable
from typing import TYPE_CHECKING, Any

import structlog

from striker.core.events import EmergencyEvent
from striker.safety.checks import (
    AirspeedCheck,
    BatteryCheck,
    CheckResult,
    GeofenceCheck,
    GPSCheck,
    HeartbeatCheck,
)
from striker.safety.geofence import Geofence
from striker.safety.override_detector import OverrideDetector

if TYPE_CHECKING:
    from striker.core.context import MissionContext

logger = structlog.get_logger(__name__)
MIN_AIRSPEED_CHECK_REL_ALT_M = 5.0
_AIRSPEED_CHECK_STATES = {
    "scan_monitor",
    "loiter_hold",
    "attack_run",
    "release_monitor",
}
_FLIGHT_STATES = _AIRSPEED_CHECK_STATES | {"landing_monitor"}
_GEOFENCE_EXEMPT_STATES = {"landing_monitor"}


class SafetyMonitor:
    """Continuous safety monitor coroutine.

    Runs all safety checks at a configurable interval and emits events
    (EmergencyEvent, OverrideEvent) when violations are detected.

    Parameters
    ----------
    geofence:
        Geofence instance for boundary checking.
    check_interval_s:
        Seconds between check cycles (default 1.0).
    battery_min_v:
        Minimum battery voltage (default 11.1V).
    stall_speed_mps:
        Minimum airspeed (default 10.0 m/s).
    override_modes:
        FC modes that trigger override (default: MANUAL, STABILIZE).
    """

    def __init__(
        self,
        geofence: Geofence,
        check_interval_s: float = 1.0,
        battery_min_v: float = 11.1,
        stall_speed_mps: float = 10.0,
        override_modes: set[str] | None = None,
        buffer_m: float = 0.0,
    ) -> None:
        self._check_interval_s = check_interval_s
        self._running = False
        self._stop_event = asyncio.Event()

        # Checks
        self._battery_check = BatteryCheck(min_voltage_v=battery_min_v)
        self._gps_check = GPSCheck()
        self._airspeed_check = AirspeedCheck(stall_speed_mps=stall_speed_mps)
        self._geofence_check = GeofenceCheck(geofence, buffer_m=buffer_m)
        self._heartbeat_check: HeartbeatCheck | None = None
        self._override_detector = OverrideDetector(
            override_modes=override_modes,
        )

        # Event callback
        self._event_callback: Callable[[Any], None] | None = None

    def set_heartbeat_check(self, is_healthy_fn: Callable[[], bool]) -> None:
        """Set the heartbeat health check function."""
        self._heartbeat_check = HeartbeatCheck(is_healthy_fn)

    def set_event_callback(self, callback: Callable[[Any], None]) -> None:
        """Set callback for safety events (EmergencyEvent, OverrideEvent)."""
        self._event_callback = callback

    async def run(self, context: MissionContext) -> None:
        """Run periodic safety check loop."""
        self._running = True
        self._stop_event.clear()
        logger.info("Safety monitor started", interval_s=self._check_interval_s)

        while self._running:
            results = await self._run_checks(context)
            if not self._running:
                return
            self._process_results(results)
            try:
                await asyncio.wait_for(self._stop_event.wait(), timeout=self._check_interval_s)
            except TimeoutError:
                continue

    async def _run_checks(self, context: MissionContext) -> list[CheckResult]:
        """Run all safety checks and collect results."""
        results: list[CheckResult] = []
        in_flight = context.current_state_name in _FLIGHT_STATES
        reached_scan = (
            context.preburned_info is not None
            and context.mission_item_reached_seq >= context.preburned_info.loiter_seq
        )

        if in_flight and context.current_battery is not None:
            results.append(self._battery_check.check(context.current_battery))

        if (
            in_flight
            and reached_scan
            and context.current_position is not None
            and context.current_state_name not in _GEOFENCE_EXEMPT_STATES
        ):
            results.append(self._geofence_check.check(context.current_position))

        if self._should_run_airspeed_check(context):
            assert context.current_speed is not None
            results.append(self._airspeed_check.check(context.current_speed))

        if self._heartbeat_check:
            results.append(self._heartbeat_check.check())

        # Override check using pymavlink flightmode property
        current_mode = context.connection.flightmode
        override_event = self._override_detector.check_mode(current_mode)
        if override_event:
            context.connection.relinquish_autonomy(override_event.reason)
            if self._event_callback:
                self._event_callback(override_event)

        return results

    def _should_run_airspeed_check(self, context: MissionContext) -> bool:
        """Enable airspeed safety only after the aircraft is actually airborne."""
        if context.current_speed is None or context.current_position is None:
            return False
        if context.current_state_name not in _AIRSPEED_CHECK_STATES:
            return False
        return context.current_position.relative_alt_m >= MIN_AIRSPEED_CHECK_REL_ALT_M

    def _process_results(self, results: list[CheckResult]) -> None:
        """Process check results and emit events for failures."""
        if not self._running:
            return
        for result in results:
            if not result.passed:
                logger.warning("Safety check failed", check=result.name, message=result.message)
                if self._event_callback:
                    self._event_callback(EmergencyEvent(reason=result.message))
            else:
                logger.debug("Safety check passed", check=result.name)

    def stop(self) -> None:
        """Stop the safety monitor."""
        self._running = False
        self._stop_event.set()
