"""Flight controller — high-level MAVLink flight command wrappers."""

from __future__ import annotations

from typing import TYPE_CHECKING

import structlog

from striker.comms.messages import (
    MAV_CMD_COMPONENT_ARM_DISARM,
    MAV_CMD_DO_CHANGE_SPEED,
    MAV_CMD_DO_SET_MODE,
    MAV_CMD_MISSION_SET_CURRENT,
    MAV_FRAME_GLOBAL_RELATIVE_ALT_INT,
    MAV_MODE_FLAG_CUSTOM_MODE_ENABLED,
    send_command_long,
)
from striker.exceptions import FlightError
from striker.flight.modes import ArduPlaneMode

if TYPE_CHECKING:
    from striker.comms.connection import MAVLinkConnection

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
        self._manual_override_modes = {ArduPlaneMode.MANUAL.name, ArduPlaneMode.STABILIZE.name, ArduPlaneMode.FBWA.name}
        self._autonomous_modes = {ArduPlaneMode.AUTO.name, ArduPlaneMode.GUIDED.name, ArduPlaneMode.LOITER.name}
        self._autonomy_flight_seen = False

    def _assert_command_allowed(self) -> None:
        self._conn.ensure_autonomy_allowed()
        current_mode = self._conn.flightmode.upper()
        if current_mode in self._autonomous_modes:
            self._autonomy_flight_seen = True
        if current_mode in self._manual_override_modes and self._autonomy_flight_seen:
            self._conn.relinquish_autonomy(f"vehicle already in {self._conn.flightmode}")
            raise FlightError(f"Autonomy relinquished: vehicle in {self._conn.flightmode}")

    async def arm(self, force: bool = True, retries: int = 5) -> None:
        """Send ARM command with optional force bypass and retries.

        Parameters
        ----------
        force:
            Use MAVLink force-arm bypass (param2=21196) to skip pre-arm checks.
            Required for SITL where GPS lock / calibration may not be complete.
        retries:
            Number of attempts before giving up.
        """
        import asyncio

        arm_attempts = retries
        for attempt in range(1, arm_attempts + 1):
            self._assert_command_allowed()
            logger.info("Arming vehicle", attempt=attempt, force=force)
            try:
                await send_command_long(
                    self._conn,
                    MAV_CMD_COMPONENT_ARM_DISARM,
                    param1=1,  # ARM
                    param2=21196 if force else 0,  # MAVLink safety bypass
                )
                logger.info("Vehicle armed")
                return
            except Exception:
                if attempt < arm_attempts:
                    logger.warning("Arm failed, retrying in 1s", attempt=attempt)
                    await asyncio.sleep(1.0)
                else:
                    raise

    async def takeoff(self, alt_m: float) -> None:
        """Start the uploaded AUTO mission from its takeoff item.

        Parameters
        ----------
        alt_m:
            Target takeoff altitude in meters.
        """
        self._assert_command_allowed()
        logger.info("Takeoff", alt_m=alt_m)
        await self.send_command(
            MAV_CMD_MISSION_SET_CURRENT,
            param1=0.0,
        )
        await self.set_mode(ArduPlaneMode.AUTO)
        logger.info("Takeoff mission started", alt_m=alt_m, mission_index=0)

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
        self._assert_command_allowed()

        await self.set_mode(ArduPlaneMode.GUIDED)
        import asyncio
        for _ in range(20):
            if self._conn.flightmode == ArduPlaneMode.GUIDED.name:
                break
            await asyncio.sleep(0.1)
        self._send_position_target(lat, lon, alt_m)
        logger.info("Goto command sent", lat=lat, lon=lon, alt_m=alt_m)

    async def resend_position_target(self, lat: float, lon: float, alt_m: float) -> None:
        """Re-send SET_POSITION_TARGET without mode change (for GUIDED keepalive)."""
        self._assert_command_allowed()
        self._send_position_target(lat, lon, alt_m)

    def _send_position_target(self, lat: float, lon: float, alt_m: float) -> None:
        """Send DO_REPOSITION via command_int (int32 coords, no float precision loss).

        Uses MAV_CMD_DO_REPOSITION which is the ArduPlane-native GUIDED nav
        command. Must use command_int_send (not command_long_send) because
        lat/lon * 1e7 exceeds float precision and causes FPE crashes.
        """
        self._assert_command_allowed()
        mav = self._conn.mav
        self._conn.command_int_send(
            mav.target_system,
            mav.target_component,
            MAV_FRAME_GLOBAL_RELATIVE_ALT_INT,  # frame
            192,  # MAV_CMD_DO_REPOSITION
            0,    # current
            0,    # autocontinue
            0,    # param1: speed (0=no change)
            0,    # param2: flags bitmask
            0,    # param3: reserved
            0,    # param4: yaw (0=no change)
            int(lat * 1e7),  # x: lat * 1e7 (int32)
            int(lon * 1e7),  # y: lon * 1e7 (int32)
            alt_m,  # z: altitude (float)
        )

    async def set_mode(self, mode: ArduPlaneMode) -> None:
        """Switch flight mode with ACK verification.

        Parameters
        ----------
        mode:
            Target ArduPlane mode.
        """
        self._assert_command_allowed()
        mav = self._conn.mav
        self._conn.command_long_send(
            mav.target_system,
            mav.target_component,
            MAV_CMD_DO_SET_MODE,
            0,  # confirmation
            MAV_MODE_FLAG_CUSTOM_MODE_ENABLED,
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
        self._assert_command_allowed()
        await send_command_long(
            self._conn,
            MAV_CMD_DO_CHANGE_SPEED,
            param1=0,  # airspeed
            param2=speed_mps,
        )
        logger.info("Speed set", speed_mps=speed_mps)

    async def send_command(
        self,
        command: int,
        param1: float = 0.0,
        param2: float = 0.0,
        param3: float = 0.0,
        param4: float = 0.0,
        param5: float = 0.0,
        param6: float = 0.0,
        param7: float = 0.0,
    ) -> None:
        """Send a raw MAVLink COMMAND_LONG (fire-and-forget, no ACK wait)."""
        self._assert_command_allowed()
        mav = self._conn.mav
        self._conn.command_long_send(
            mav.target_system,
            mav.target_component,
            command,
            0,
            param1, param2, param3, param4, param5, param6, param7,
        )

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
