"""Landing monitor state — engage landing sequence, observe to touchdown."""

from __future__ import annotations

from typing import TYPE_CHECKING

import structlog

from striker.core.events import Transition
from striker.core.states import register_state
from striker.core.states.base import BaseState
from striker.flight.modes import ArduPlaneMode

if TYPE_CHECKING:
    from striker.core.context import MissionContext

logger = structlog.get_logger(__name__)


class LandingMonitorState(BaseState):
    """Engage AUTO landing and monitor for touchdown."""

    async def on_enter(self, context: MissionContext) -> None:
        context.current_state_name = "landing_monitor"
        logger.info("Entering landing monitor")

        if not context.preburned_info:
            return

        from striker.comms.messages import MAV_CMD_MISSION_SET_CURRENT

        logger.info(
            "Setting mission sequence for landing",
            seq=context.preburned_info.landing_start_seq,
        )
        await context.flight_controller.send_command(
            MAV_CMD_MISSION_SET_CURRENT,
            param1=context.preburned_info.landing_start_seq,
        )
        await context.flight_controller.set_mode(ArduPlaneMode.AUTO)

    async def execute(self, context: MissionContext) -> Transition | None:
        if not context.preburned_info:
            return None

        alt = context.current_position.relative_alt_m if context.current_position else 0.0
        status = context.last_status_text.lower()

        if alt < 5.0 and ("hit ground" in status or "land complete" in status or "throttle disarmed" in status):
            logger.info("Landing detected", alt=alt, status=status)
            return Transition("completed", "Landing detected")

        if context.current_system_status and not context.current_system_status.armed:
            logger.info("Landing detected (disarmed)", alt=alt)
            return Transition("completed", "Landing detected (vehicle disarmed)")

        return None


register_state("landing_monitor", LandingMonitorState)
