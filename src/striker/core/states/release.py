"""Release state — confirm payload release and transition to landing."""

from __future__ import annotations

from typing import TYPE_CHECKING

import time

import structlog

from striker.core.events import Transition
from striker.core.states import register_state
from striker.core.states.base import BaseState
from striker.flight.mission_upload import upload_landing_mission

if TYPE_CHECKING:
    from striker.core.context import MissionContext

logger = structlog.get_logger(__name__)


class ReleaseState(BaseState):
    """Release state — confirm payload release.

    When dry_run=False: ArduPlane already triggered DO_SET_SERVO via the
    attack run mission. This state uploads a landing-only mission and then
    transitions to landing so the landing sequence is no longer appended to
    the temporary attack mission.

    When dry_run=True: No DO_SET_SERVO was embedded in the mission.
    Trigger release via the companion computer's release controller
    (which logs without physical servo activation in dry_run mode), then
    upload the same landing-only mission.
    """

    _released: bool = False

    async def on_enter(self, context: MissionContext) -> None:
        await super().on_enter(context)
        self._released = False

    async def _handoff_to_landing(self, context: MissionContext) -> Transition | None:
        geometry = context.attack_geometry
        if geometry is None:
            logger.error("Attack geometry unavailable for landing handoff")
            return None

        try:
            landing_start_seq = await upload_landing_mission(
                conn=context.connection,
                geometry=geometry,
                context=context,
            )
        except Exception:
            logger.exception("Failed to upload landing-only mission after release")
            return None

        logger.info(
            "Landing handoff prepared",
            landing_start_seq=landing_start_seq,
        )
        return Transition(target_state="landing", reason="Release complete")

    async def execute(self, context: MissionContext) -> Transition | None:
        try:
            if not self._released:
                if context.settings.dry_run:
                    success = await context.release_controller.release()
                    if success:
                        self._released = True
                        context.mark_release_triggered(time.monotonic())
                        logger.info("Payload released (dry-run via companion)")
                    else:
                        logger.error("Release failed (dry-run)")
                        return None
                else:
                    self._released = True
                    context.mark_release_triggered(time.monotonic())
                    logger.info("Payload released (native DO_SET_SERVO)")

            return await self._handoff_to_landing(context)
        except Exception:
            logger.exception("Release error")

        return None


register_state("release", ReleaseState)
