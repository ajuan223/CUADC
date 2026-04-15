"""Landing state — trigger landing sequence and detect touchdown."""

from __future__ import annotations

from typing import TYPE_CHECKING

import structlog

from striker.comms.messages import MAV_CMD_MISSION_SET_CURRENT
from striker.core.events import Transition
from striker.core.states import register_state
from striker.core.states.base import BaseState
from striker.flight.modes import ArduPlaneMode

if TYPE_CHECKING:
    from striker.core.context import MissionContext

logger = structlog.get_logger(__name__)


class LandingState(BaseState):
    """Landing state — execute landing sequence.

    Triggers the pre-uploaded landing sequence (uploaded during PREFLIGHT)
    by setting AUTO mode and jumping to the landing sequence start index.
    Monitors for landing detection (altitude near ground).
    """

    _landing_triggered: bool = False

    async def on_enter(self, context: MissionContext) -> None:
        await super().on_enter(context)
        self._landing_triggered = False

    async def execute(self, context: MissionContext) -> Transition | None:
        if not self._landing_triggered:
            try:
                # Set AUTO mode to execute pre-uploaded mission
                await context.flight_controller.set_mode(ArduPlaneMode.AUTO)

                landing_start_index = context.landing_sequence_start_index
                if landing_start_index is None:
                    logger.error("Landing sequence start index unavailable")
                    return None
                await context.flight_controller.send_command(
                    MAV_CMD_MISSION_SET_CURRENT,
                    param1=float(landing_start_index),
                )
                self._landing_triggered = True
                logger.info("Landing sequence triggered", start_index=landing_start_index)
            except Exception:
                logger.exception("Failed to trigger landing")
                return None

        # Detect landing: altitude near 0
        if context.current_position and context.current_position.relative_alt_m < 1.0:
            logger.info("Landing detected", alt=context.current_position.relative_alt_m)
            return Transition(target_state="completed", reason="Landing complete")

        return None


register_state("landing", LandingState)
