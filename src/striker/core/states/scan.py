"""Scan state — execute scan waypoint pattern."""

from __future__ import annotations

from typing import TYPE_CHECKING

import structlog

from striker.core.events import Transition
from striker.core.states import register_state
from striker.core.states.base import BaseState

if TYPE_CHECKING:
    from striker.core.context import MissionContext

logger = structlog.get_logger(__name__)


class ScanState(BaseState):
    """Scan state — follow scan waypoints in AUTO mode.

    Increments scan_cycle_count and monitors waypoint progress.
    Transitions to LOITER on scan completion.
    """

    _waypoints_remaining: int = 0

    async def on_enter(self, context: MissionContext) -> None:
        await super().on_enter(context)
        context.scan_cycle_count += 1
        logger.info("Scan started", cycle=context.scan_cycle_count)

        self._waypoints_remaining = len(context.field_profile.scan_waypoints.waypoints)

    async def execute(self, context: MissionContext) -> Transition | None:
        # In production, would monitor MISSION_ITEM_REACHED messages
        # For now, simple waypoint count down
        if self._waypoints_remaining <= 0:
            logger.info("Scan complete", cycle=context.scan_cycle_count)
            return Transition(target_state="loiter", reason="Scan waypoints complete")

        self._waypoints_remaining -= 1
        return None


register_state("scan", ScanState)
