"""Release state — trigger payload release mechanism."""

from __future__ import annotations

from typing import TYPE_CHECKING

import structlog

from striker.core.events import Transition
from striker.core.states import register_state
from striker.core.states.base import BaseState

if TYPE_CHECKING:
    from striker.core.context import MissionContext

logger = structlog.get_logger(__name__)


class ReleaseState(BaseState):
    """Release state — trigger the release mechanism and verify."""

    _triggered: bool = False

    async def on_enter(self, context: MissionContext) -> None:
        await super().on_enter(context)
        self._triggered = False

    async def execute(self, context: MissionContext) -> Transition | None:
        if not self._triggered:
            try:
                success = await context.release_controller.release()
                if success:
                    self._triggered = True
                    logger.info("Payload released successfully")
                    return Transition(target_state="landing", reason="Release complete")
                else:
                    logger.error("Release failed")
            except Exception:
                logger.exception("Release error")

        return None


register_state("release", ReleaseState)
