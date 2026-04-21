"""Standby state — download and parse preburned mission."""

from __future__ import annotations

from typing import TYPE_CHECKING

import structlog

from striker.core.events import Transition
from striker.core.states import register_state
from striker.core.states.base import BaseState
from striker.exceptions import StrikerError
from striker.flight.mission_upload import download_mission
from striker.flight.preburned_mission import parse_preburned_mission

if TYPE_CHECKING:
    from striker.core.context import MissionContext

logger = structlog.get_logger(__name__)


class StandbyState(BaseState):
    """Wait for connection and download preburned mission."""

    async def on_enter(self, context: MissionContext) -> None:
        context.current_state_name = "standby"
        logger.info("Entering standby — downloading preburned mission")

    async def execute(self, context: MissionContext) -> Transition | None:
        try:
            items = await download_mission(context.connection)
            preburned_info = parse_preburned_mission(items)
            context.preburned_info = preburned_info

            logger.info(
                "Preburned mission validated",
                loiter_seq=preburned_info.loiter_seq,
                slot_start=preburned_info.slot_start_seq,
                landing_seq=preburned_info.landing_start_seq,
            )
            return Transition("scan_monitor", "Preburned mission ready")
        except StrikerError as e:
            logger.error("Preburned mission error", error=str(e))
            # Remain in standby on error
            return None

register_state("standby", StandbyState)
