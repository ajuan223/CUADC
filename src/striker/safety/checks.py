"""Safety checks — battery, GPS, heartbeat, airspeed, geofence."""

from __future__ import annotations

from typing import TYPE_CHECKING

import structlog

if TYPE_CHECKING:
    from striker.comms.telemetry import BatteryData, GeoPosition, SpeedData
    from striker.safety.geofence import Geofence

logger = structlog.get_logger(__name__)


# ── Check result ──────────────────────────────────────────────────


class CheckResult:
    """Result of a single safety check."""

    def __init__(self, name: str, passed: bool, message: str = "") -> None:
        self.name = name
        self.passed = passed
        self.message = message

    def __repr__(self) -> str:
        status = "PASS" if self.passed else "FAIL"
        return f"CheckResult({self.name}={status}: {self.message})"


# ── Individual checks ────────────────────────────────────────────


class BatteryCheck:
    """Battery voltage check — triggers EmergencyEvent if below threshold."""

    def __init__(self, min_voltage_v: float = 11.1) -> None:
        self._min_voltage_v = min_voltage_v

    def check(self, battery: BatteryData) -> CheckResult:
        if battery.voltage_v < self._min_voltage_v:
            return CheckResult(
                "battery",
                False,
                f"Voltage {battery.voltage_v:.1f}V below threshold {self._min_voltage_v}V",
            )
        return CheckResult("battery", True, f"Voltage {battery.voltage_v:.1f}V OK")


class GPSCheck:
    """GPS fix quality check."""

    def __init__(self, min_fix_type: int = 3, min_satellites: int = 6) -> None:
        self._min_fix_type = min_fix_type
        self._min_satellites = min_satellites

    def check(self, fix_type: int, satellites: int) -> CheckResult:
        if fix_type < self._min_fix_type:
            return CheckResult(
                "gps",
                False,
                f"Fix type {fix_type} below minimum {self._min_fix_type}",
            )
        return CheckResult("gps", True, f"GPS fix type {fix_type}, {satellites} satellites")


class HeartbeatCheck:
    """Heartbeat health check — delegates to HeartbeatMonitor."""

    def __init__(self, is_healthy_fn: callable) -> None:  # type: ignore[type-arg]
        self._is_healthy_fn = is_healthy_fn

    def check(self) -> CheckResult:
        healthy = self._is_healthy_fn()
        if not healthy:
            return CheckResult("heartbeat", False, "Heartbeat timeout — connection unhealthy")
        return CheckResult("heartbeat", True, "Heartbeat OK")


class AirspeedCheck:
    """Airspeed check — warns if below stall speed."""

    def __init__(self, stall_speed_mps: float = 10.0) -> None:
        self._stall_speed_mps = stall_speed_mps

    def check(self, speed: SpeedData) -> CheckResult:
        if speed.airspeed_mps < self._stall_speed_mps:
            return CheckResult(
                "airspeed",
                False,
                f"Airspeed {speed.airspeed_mps:.1f} m/s below stall speed {self._stall_speed_mps} m/s",
            )
        return CheckResult("airspeed", True, f"Airspeed {speed.airspeed_mps:.1f} m/s OK")


class GeofenceCheck:
    """Geofence boundary check — triggers EmergencyEvent if outside."""

    def __init__(self, geofence: Geofence) -> None:
        self._geofence = geofence

    def check(self, position: GeoPosition) -> CheckResult:
        if not self._geofence.is_inside(position.lat, position.lon):
            return CheckResult(
                "geofence",
                False,
                f"Position ({position.lat:.6f}, {position.lon:.6f}) outside geofence",
            )
        return CheckResult("geofence", True, "Position inside geofence")
