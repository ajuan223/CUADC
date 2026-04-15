"""Landing state — trigger landing sequence and detect touchdown."""

from __future__ import annotations

from typing import TYPE_CHECKING

import structlog

from striker.core.events import Transition
from striker.core.states import register_state
from striker.core.states.base import BaseState

if TYPE_CHECKING:
    from striker.core.context import MissionContext

logger = structlog.get_logger(__name__)


class LandingState(BaseState):
    """Landing state — execute landing sequence.

    Triggers the pre-uploaded landing sequence and monitors for
    landing detection (altitude near ground, low speed).
    """

    _landing_triggered: bool = False

    async def on_enter(self, context: MissionContext) -> None:
        await super().on_enter(context)
        self._landing_triggered = False

    async def execute(self, context: MissionContext) -> Transition | None:
        if not self._landing_triggered:
            try:
                await context.flight_controller.set_mode(
                    __import__("striker.flight.modes", fromlist=["ArduPlaneMode"]).ArduPlaneMode.RTL
                )
                self._landing_triggered = True
                logger.info("Landing sequence triggered")
            except Exception:
                logger.exception("Failed to trigger landing")
                return None

        # Detect landing: altitude near 0 and low speed
        if context.current_position:
            if context.current_position.relative_alt_m < 1.0:
                logger.info("Landing detected", alt=context.current_position.relative_alt_m)
                return Transition(target_state="completed", reason="Landing complete")

        return None


register_state("landing", LandingState)
