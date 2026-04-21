"""Attack run state — monitor approach to drop point."""

from __future__ import annotations

from typing import TYPE_CHECKING

import structlog

from striker.core.events import Transition
from striker.core.states import register_state
from striker.core.states.base import BaseState

if TYPE_CHECKING:
    from striker.core.context import MissionContext

logger = structlog.get_logger(__name__)


class AttackRunState(BaseState):
    """Monitor progress toward drop point."""

    async def on_enter(self, context: MissionContext) -> None:
        context.current_state_name = "attack_run"
        logger.info("Entering attack run")

    async def execute(self, context: MissionContext) -> Transition | None:
        if not context.preburned_info:
            return None

        target_seq = context.preburned_info.slot_start_seq + 1

        if context.mission_item_reached_seq >= target_seq or context.mission_current_seq > target_seq:
            return Transition("release_monitor", "Target waypoint reached")
        return None

register_state("attack_run", AttackRunState)
