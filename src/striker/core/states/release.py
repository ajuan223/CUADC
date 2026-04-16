"""Release state — confirm payload release and transition to landing."""

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
    """Release state — confirm payload release.

    When dry_run=False: ArduPlane already triggered DO_SET_SERVO via the
    attack run mission. This state just logs confirmation.

    When dry_run=True: No DO_SET_SERVO was embedded in the mission.
    Trigger release via the companion computer's release controller
    (which logs without physical servo activation in dry_run mode).
    """

    _released: bool = False

    async def on_enter(self, context: MissionContext) -> None:
        await super().on_enter(context)
        self._released = False

    async def execute(self, context: MissionContext) -> Transition | None:
        if self._released:
            return None

        try:
            if context.settings.dry_run:
                # Companion-triggered release (dry_run: logs only)
                success = await context.release_controller.release()
                if success:
                    self._released = True
                    logger.info("Payload released (dry-run via companion)")
                    return Transition(target_state="landing", reason="Release complete (dry-run)")
                else:
                    logger.error("Release failed (dry-run)")
            else:
                # Native DO_SET_SERVO already executed by ArduPlane
                self._released = True
                logger.info("Payload released (native DO_SET_SERVO)")
                return Transition(target_state="landing", reason="Release complete")
        except Exception:
            logger.exception("Release error")

        return None


register_state("release", ReleaseState)
