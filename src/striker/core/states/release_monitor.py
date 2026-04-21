"""Release monitor state — confirm payload release."""

from __future__ import annotations

from typing import TYPE_CHECKING

import structlog

from striker.core.events import Transition
from striker.core.states import register_state
from striker.core.states.base import BaseState

if TYPE_CHECKING:
    from striker.core.context import MissionContext

logger = structlog.get_logger(__name__)


class ReleaseMonitorState(BaseState):
    """Confirm payload release via servo action or companion API."""

    async def on_enter(self, context: MissionContext) -> None:
        context.current_state_name = "release_monitor"
        logger.info("Entering release monitor")

    async def execute(self, context: MissionContext) -> Transition | None:
        if not context.preburned_info:
            return None

        servo_seq = context.preburned_info.slot_start_seq + 2

        # Flight controller should automatically execute DO_SET_SERVO at servo_seq
        if context.mission_current_seq > servo_seq:
            # We assume it has been triggered
            if not context.release_triggered:
                # Mark as triggered now using system time
                import time
                context.mark_release_triggered(time.monotonic())

            return Transition("landing_monitor", "Release confirmed by seq progression")
        return None

register_state("release_monitor", ReleaseMonitorState)
