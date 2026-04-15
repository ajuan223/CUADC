"""EMERGENCY state — safety violation, trigger emergency landing."""

from __future__ import annotations

from typing import TYPE_CHECKING

import structlog

from striker.core.events import EmergencyEvent
from striker.core.states import register_state
from striker.core.states.base import BaseState

if TYPE_CHECKING:
    from striker.core.context import MissionContext

logger = structlog.get_logger(__name__)


class EmergencyState(BaseState):
    """Emergency state — triggered by safety violation.

    Logs the emergency reason and triggers emergency landing procedure.
    """

    _reason: str = ""

    async def on_enter(self, context: MissionContext) -> None:
        await super().on_enter(context)
        logger.critical("EMERGENCY state entered", reason=self._reason)

    def handle(self, event: object) -> None:
        if isinstance(event, EmergencyEvent):
            self._reason = event.reason
        return None


register_state("emergency", EmergencyState)
