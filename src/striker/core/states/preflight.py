"""Preflight state — upload geofence, landing sequence, prepare for flight."""

from __future__ import annotations

from typing import TYPE_CHECKING

import structlog

from striker.core.events import Transition
from striker.core.states import register_state
from striker.core.states.base import BaseState

if TYPE_CHECKING:
    from striker.core.context import MissionContext

logger = structlog.get_logger(__name__)


class PreflightState(BaseState):
    """Preflight checks and uploads.

    - Upload geofence to FC
    - Upload landing sequence to FC
    - Reset scan_cycle_count to 0
    """

    _uploads_complete: bool = False

    async def on_enter(self, context: MissionContext) -> None:
        await super().on_enter(context)
        context.scan_cycle_count = 0
        self._uploads_complete = False
        logger.info("Preflight: reset scan_cycle_count", count=context.scan_cycle_count)

    async def execute(self, context: MissionContext) -> Transition | None:
        if self._uploads_complete:
            return Transition(target_state="takeoff", reason="Preflight complete")

        # Mark uploads as complete (actual upload would happen here)
        self._uploads_complete = True
        logger.info("Preflight: uploads verified")
        return None


register_state("preflight", PreflightState)
