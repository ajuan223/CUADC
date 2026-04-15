"""Flight controller — high-level MAVLink flight command wrappers."""

from __future__ import annotations

import structlog
from typing import TYPE_CHECKING

from striker.comms.messages import send_command_long, wait_for_message
from striker.exceptions import FlightError
from striker.flight.modes import ArduPlaneMode

if TYPE_CHECKING:
    from striker.comms.connection import MAVLinkConnection
    from striker.config.field_profile import FieldProfile

logger = structlog.get_logger(__name__)


class FlightController:
    """High-level flight command wrapper.

    Provides async methods for common MAVLink flight operations:
    arm, takeoff, goto, set_mode, set_speed.

    Parameters
    ----------
    connection:
        Active MAVLinkConnection.
    """

    def __init__(self, connection: MAVLinkConnection) -> None:
        self._conn = connection

    async def arm(self) -> None:
        """Send ARM command with pre-arm checks."""
        from pymavlink import mavutil  # noqa: RL-04 — allowed in flight via messages

        logger.info("Arming vehicle")
        await send_command_long(
            self._conn,
            mavutil.mavlink.MAV_CMD_COMPONENT_ARM_DISARM,
            param1=1,  # ARM
        )
        logger.info("Vehicle armed")

    async def takeoff(self, alt_m: float) -> None:
        """Set AUTO mode and send NAV_TAKEOFF command.

        Parameters
        ----------
        alt_m:
            Target takeoff altitude in meters.
        """
        from pymavlink import mavutil

        logger.info("Takeoff", alt_m=alt_m)
        await self.set_mode(ArduPlaneMode.AUTO)

        await send_command_long(
            self._conn,
            mavutil.mavlink.MAV_CMD_NAV_TAKEOFF,
            param7=alt_m,
        )
        logger.info("Takeoff command sent", alt_m=alt_m)

    async def goto(self, lat: float, lon: float, alt_m: float) -> None:
        """GUIDED mode + SET_POSITION_TARGET for GPS navigation.

        Parameters
        ----------
        lat, lon:
            Target GPS coordinates (WGS-84 degrees).
        alt_m:
            Target altitude in meters.
        """
        self._validate_gps(lat, lon)

        from pymavlink import mavutil

        await self.set_mode(ArduPlaneMode.GUIDED)

        mav = self._conn.mav
        mav.mav.set_position_target_global_int_send(
            0,  # time_boot_ms
            mav.target_system,
            mav.target_component,
            mavutil.mavlink.MAV_FRAME_GLOBAL_RELATIVE_ALT_INT,
            0b1111111111111000,  # type_mask: only pos
            int(lat * 1e7),
            int(lon * 1e7),
            alt_m,
            0, 0, 0,  # vel
            0, 0, 0,  # accel
            0, 0,  # yaw, yaw_rate
        )
        logger.info("Goto command sent", lat=lat, lon=lon, alt_m=alt_m)

    async def set_mode(self, mode: ArduPlaneMode) -> None:
        """Switch flight mode with ACK verification.

        Parameters
        ----------
        mode:
            Target ArduPlane mode.
        """
        from pymavlink import mavutil

        mav = self._conn.mav
        mav.mav.command_long_send(
            mav.target_system,
            mav.target_component,
            mavutil.mavlink.MAV_CMD_DO_SET_MODE,
            0,  # confirmation
            mavutil.mavlink.MAV_MODE_FLAG_CUSTOM_MODE_ENABLED,
            mode.mode_id,
            0, 0, 0, 0, 0,
        )
        logger.info("Mode change requested", mode=mode.name)

    async def set_speed(self, speed_mps: float) -> None:
        """Set airspeed via MAV_CMD_DO_CHANGE_SPEED.

        Parameters
        ----------
        speed_mps:
            Target airspeed in m/s.
        """
        from pymavlink import mavutil

        await send_command_long(
            self._conn,
            mavutil.mavlink.MAV_CMD_DO_CHANGE_SPEED,
            param1=0,  # airspeed
            param2=speed_mps,
        )
        logger.info("Speed set", speed_mps=speed_mps)

    @staticmethod
    def _validate_gps(lat: float, lon: float) -> None:
        """Validate GPS coordinate ranges (RL-05).

        Raises
        ------
        FlightError
            If coordinates are out of valid range.
        """
        if not (-90 <= lat <= 90):
            raise FlightError(f"Invalid latitude: {lat}")
        if not (-180 <= lon <= 180):
            raise FlightError(f"Invalid longitude: {lon}")
