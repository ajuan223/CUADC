"""Landing monitor state — observe landing sequence to touchdown."""

from __future__ import annotations

from typing import TYPE_CHECKING

import structlog

from striker.core.events import Transition
from striker.core.states import register_state
from striker.core.states.base import BaseState

if TYPE_CHECKING:
    from striker.core.context import MissionContext

logger = structlog.get_logger(__name__)


class LandingMonitorState(BaseState):
    """Monitor landing sequence without uploading new missions."""

    async def on_enter(self, context: MissionContext) -> None:
        context.current_state_name = "landing_monitor"
        logger.info("Entering landing monitor")

    async def execute(self, context: MissionContext) -> Transition | None:
        if not context.preburned_info:
            return None

        # Check for landing success via telemetry
        alt = context.current_position.relative_alt_m if context.current_position else 0.0
        status = context.last_status_text.lower()

        # We consider landing done if altitude is low AND status indicates touchdown/disarm
        if alt < 5.0 and ("hit ground" in status or "land complete" in status or "throttle disarmed" in status):
            logger.info("Landing detected", alt=alt, status=status)
            return Transition("completed", "Landing detected")

        return None

register_state("landing_monitor", LandingMonitorState)
