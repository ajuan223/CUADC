"""Completed state — terminal state after successful mission."""

from __future__ import annotations

from typing import TYPE_CHECKING

import structlog

from striker.core.states import register_state
from striker.core.states.base import BaseState

if TYPE_CHECKING:
    from striker.core.context import MissionContext

logger = structlog.get_logger(__name__)


class CompletedState(BaseState):
    """Terminal state — mission completed successfully.

    Logs success and stops the flight recorder.
    No transitions out — this is a final state.
    """

    async def on_enter(self, context: MissionContext) -> None:
        await super().on_enter(context)
        logger.info("Mission completed successfully!")
        try:
            context.flight_recorder.stop()
        except Exception:
            logger.exception("Error stopping flight recorder")

    async def execute(self, context: MissionContext) -> None:
        # Terminal state — no transitions
        return None


register_state("completed", CompletedState)
