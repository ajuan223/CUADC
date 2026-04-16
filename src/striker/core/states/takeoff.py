"""Takeoff state — arm vehicle and climb to target altitude."""

from __future__ import annotations

from typing import TYPE_CHECKING

import structlog

from striker.core.events import Transition
from striker.core.states import register_state
from striker.core.states.base import BaseState

if TYPE_CHECKING:
    from striker.core.context import MissionContext

logger = structlog.get_logger(__name__)


class TakeoffState(BaseState):
    """Takeoff state — arm and climb to target altitude.

    Monitors altitude and transitions to SCAN when target reached.
    """

    _target_alt_m: float = 0.0
    _armed: bool = False
    _takeoff_sent: bool = False

    async def on_enter(self, context: MissionContext) -> None:
        await super().on_enter(context)
        self._target_alt_m = context.field_profile.scan_waypoints.altitude_m
        self._armed = False
        self._takeoff_sent = False

    async def execute(self, context: MissionContext) -> Transition | None:
        if not self._armed:
            try:
                await context.flight_controller.arm(force=context.settings.arm_force_bypass)
                self._armed = True
            except Exception:
                logger.exception("Arm failed")
                return None

        if not self._takeoff_sent:
            try:
                await context.flight_controller.takeoff(self._target_alt_m)
                self._takeoff_sent = True
            except Exception:
                logger.exception("Takeoff command failed")
                return None

        # Check altitude
        if context.current_position and context.current_position.alt_m >= self._target_alt_m * 0.9:
            logger.info("Target altitude reached", alt=context.current_position.alt_m)
            return Transition(target_state="scan", reason="Takeoff complete")

        return None


register_state("takeoff", TakeoffState)
