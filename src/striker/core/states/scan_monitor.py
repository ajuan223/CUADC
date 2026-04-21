"""Scan monitor state — passively observe scan progress."""

from __future__ import annotations

from typing import TYPE_CHECKING

import structlog

from striker.core.events import Transition
from striker.core.states import register_state
from striker.core.states.base import BaseState

if TYPE_CHECKING:
    from striker.core.context import MissionContext

logger = structlog.get_logger(__name__)


class ScanMonitorState(BaseState):
    """Passively monitor preburned scan execution."""

    async def on_enter(self, context: MissionContext) -> None:
        context.current_state_name = "scan_monitor"
        logger.info("Monitoring scan progress")

    async def execute(self, context: MissionContext) -> Transition | None:
        if not context.preburned_info:
            return None

        if context.mission_current_seq >= context.preburned_info.loiter_seq:
            return Transition("loiter_hold", "Reached loiter seq")
        return None

register_state("scan_monitor", ScanMonitorState)
