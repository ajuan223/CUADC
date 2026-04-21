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
        if context.release_triggered:
            return Transition("landing_monitor", "Release confirmed by flag")
        return None

register_state("release_monitor", ReleaseMonitorState)
