"""Telemetry parser — typed dataclasses for all MAVLink telemetry.

Converts raw pymavlink messages to strong-typed dataclasses immediately
at the comms boundary (REQ-COMMS-007, RL-04).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

# ── Typed dataclasses ─────────────────────────────────────────────


@dataclass(frozen=True)
class GeoPosition:
    """WGS-84 position from GLOBAL_POSITION_INT."""

    lat: float
    lon: float
    alt_m: float
    relative_alt_m: float


@dataclass(frozen=True)
class AttitudeData:
    """Attitude from ATTITUDE message."""

    roll_rad: float
    pitch_rad: float
    yaw_rad: float


@dataclass(frozen=True)
class SpeedData:
    """Speed from VFR_HUD message."""

    airspeed_mps: float
    groundspeed_mps: float


@dataclass(frozen=True)
class WindData:
    """Wind from WIND message."""

    direction_deg: float
    speed_mps: float


@dataclass(frozen=True)
class BatteryData:
    """Battery from SYS_STATUS message."""

    voltage_v: float
    current_a: float
    remaining_pct: int


@dataclass(frozen=True)
class SystemStatus:
    """System status from HEARTBEAT message."""

    mode: str
    armed: bool
    system_status: int


# ── Parser ────────────────────────────────────────────────────────

# Message types we parse into typed dataclasses
_PARSED_TYPES = frozenset({
    "GLOBAL_POSITION_INT",
    "ATTITUDE",
    "VFR_HUD",
    "WIND",
    "SYS_STATUS",
    "HEARTBEAT",
})


class TelemetryParser:
    """Dispatch-table telemetry parser.

    Converts raw pymavlink messages into frozen dataclasses.
    Returns ``None`` for unhandled message types.
    """

    def __init__(self) -> None:
        self._dispatch: dict[str, Any] = {
            "GLOBAL_POSITION_INT": self._parse_global_position_int,
            "ATTITUDE": self._parse_attitude,
            "VFR_HUD": self._parse_vfr_hud,
            "WIND": self._parse_wind,
            "SYS_STATUS": self._parse_sys_status,
            "HEARTBEAT": self._parse_heartbeat,
        }

    def parse(self, msg: Any) -> Any:
        """Parse a raw pymavlink message into a typed dataclass.

        Returns ``None`` if the message type is not handled.
        """
        msg_type = msg.get_type()
        handler = self._dispatch.get(msg_type)
        if handler is None:
            return None
        try:
            return handler(msg)
        except Exception:
            # Gracefully handle malformed messages
            return None

    # ── Conversion helpers ────────────────────────────────────────

    @staticmethod
    def _parse_global_position_int(msg: Any) -> GeoPosition:
        return GeoPosition(
            lat=msg.lat / 1e7,
            lon=msg.lon / 1e7,
            alt_m=msg.alt / 1e3,
            relative_alt_m=msg.relative_alt / 1e3,
        )

    @staticmethod
    def _parse_attitude(msg: Any) -> AttitudeData:
        return AttitudeData(
            roll_rad=msg.roll,
            pitch_rad=msg.pitch,
            yaw_rad=msg.yaw,
        )

    @staticmethod
    def _parse_vfr_hud(msg: Any) -> SpeedData:
        return SpeedData(
            airspeed_mps=msg.airspeed,
            groundspeed_mps=msg.groundspeed,
        )

    @staticmethod
    def _parse_wind(msg: Any) -> WindData:
        return WindData(
            direction_deg=msg.direction,
            speed_mps=msg.speed,
        )

    @staticmethod
    def _parse_sys_status(msg: Any) -> BatteryData:
        return BatteryData(
            voltage_v=msg.voltage_battery / 1e3,
            current_a=msg.current_battery / 1e2 if msg.current_battery != -1 else 0.0,
            remaining_pct=msg.battery_remaining,
        )

    @staticmethod
    def _parse_heartbeat(msg: Any) -> SystemStatus:
        # pymavlink mavutil sets .flightmode and .motors_armed() on the connection
        # object, not on the message itself. For mode detection use
        # connection.flightmode which returns ArduPlane mode names directly.
        # Here we store custom_mode as a numeric string for raw telemetry logging.
        # RL-04: confine pymavlink imports to the comms package.
        from pymavlink import mavutil

        armed = bool(msg.base_mode & mavutil.mavlink.MAV_MODE_FLAG_SAFETY_ARMED)
        return SystemStatus(
            mode=str(msg.custom_mode),
            armed=armed,
            system_status=msg.system_status,
        )
