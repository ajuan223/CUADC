"""OVERRIDE state — human has taken manual control (terminal)."""

from __future__ import annotations

from typing import TYPE_CHECKING

import structlog

from striker.core.states import register_state
from striker.core.states.base import BaseState

if TYPE_CHECKING:
    from striker.core.context import MissionContext

logger = structlog.get_logger(__name__)


class OverrideState(BaseState):
    """Terminal state — human operator has taken manual control (RL-03).

    No automatic recovery possible. System loiters until manual intervention.
    """

    async def on_enter(self, context: MissionContext) -> None:
        await super().on_enter(context)
        logger.warning("Human override detected — autonomous control relinquished")

    async def execute(self, context: MissionContext) -> None:
        # Terminal state — no automatic transitions
        return None


register_state("override", OverrideState)
