"""MAVLink release controller — DO_SET_SERVO with ACK verification."""

from __future__ import annotations

from typing import TYPE_CHECKING

import structlog

from striker.comms.messages import (
    MAV_CMD_DO_SET_SERVO,
    MAV_RESULT_ACCEPTED,
)
from striker.payload import register_release
from striker.payload.models import ReleaseConfig

if TYPE_CHECKING:
    from striker.comms.connection import MAVLinkConnection

logger = structlog.get_logger(__name__)


class MavlinkRelease:
    """MAVLink servo-based release controller.

    Uses DO_SET_SERVO command with COMMAND_ACK verification.

    Parameters
    ----------
    conn:
        Active MAVLinkConnection.
    config:
        Release mechanism configuration.
    """

    def __init__(self, conn: MAVLinkConnection, config: ReleaseConfig) -> None:
        self._conn = conn
        self._config = config
        self._armed = False
        self._released = False

    @property
    def is_armed(self) -> bool:
        return self._armed

    @property
    def is_released(self) -> bool:
        return self._released

    async def arm(self) -> None:
        """Arm the release mechanism (set servo to closed position)."""
        if self._config.dry_run:
            logger.info("DRY_RUN: Would arm release servo")
            self._armed = True
            return

        mav = self._conn.mav
        mav.mav.command_long_send(
            mav.target_system,
            mav.target_component,
            MAV_CMD_DO_SET_SERVO,
            0,
            self._config.channel,
            self._config.pwm_close,
            0, 0, 0, 0, 0,
        )
        self._armed = True
        logger.info("Release servo armed", channel=self._config.channel)

    async def release(self) -> bool:
        """Trigger release via DO_SET_SERVO with ACK verification."""
        if self._config.dry_run:
            logger.info("DRY_RUN: Would trigger release")
            self._released = True
            return True

        mav = self._conn.mav
        mav.mav.command_long_send(
            mav.target_system,
            mav.target_component,
            MAV_CMD_DO_SET_SERVO,
            0,
            self._config.channel,
            self._config.pwm_open,
            0, 0, 0, 0, 0,
        )

        # Wait for ACK
        try:
            ack = await self._conn.recv_match("COMMAND_ACK", timeout=3.0)
            if hasattr(ack, "result") and ack.result == MAV_RESULT_ACCEPTED:
                self._released = True
                logger.info("Release triggered successfully")
                return True
        except TimeoutError:
            logger.error("Release ACK timeout")

        return False


register_release("mavlink", MavlinkRelease)
