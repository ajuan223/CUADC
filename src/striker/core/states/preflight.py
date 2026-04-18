"""Preflight state — upload geofence, landing sequence, prepare for flight."""

from __future__ import annotations

from typing import TYPE_CHECKING

import structlog

from striker.core.events import Transition
from striker.core.states import register_state
from striker.core.states.base import BaseState
from striker.flight.mission_geometry import generate_mission_geometry
from striker.flight.mission_upload import upload_full_mission

if TYPE_CHECKING:
    from striker.core.context import MissionContext

logger = structlog.get_logger(__name__)


class PreflightState(BaseState):
    """Preflight checks and uploads.

    - Upload full mission (takeoff + scan waypoints + landing sequence) to FC
    - Reset mission progress tracking
    """

    _uploads_complete: bool = False

    async def on_enter(self, context: MissionContext) -> None:
        await super().on_enter(context)
        context.landing_sequence_start_index = None
        context.scan_start_seq = None
        context.scan_end_seq = None
        context.mission_current_seq = 0
        context.mission_item_reached_seq = -1
        context.last_status_text = ""
        self._uploads_complete = False

    async def execute(self, context: MissionContext) -> Transition | None:
        if self._uploads_complete:
            return Transition(target_state="takeoff", reason="Preflight complete")

        try:
            geometry = generate_mission_geometry(
                context.field_profile,
            )
            context.landing_sequence_start_index = await upload_full_mission(
                context.connection,
                geometry,
            )
            context.scan_start_seq = geometry.scan_start_seq
            context.scan_end_seq = geometry.scan_end_seq
        except Exception:
            logger.exception("Preflight mission upload failed")
            return None

        self._uploads_complete = True
        logger.info(
            "Preflight: mission uploaded",
            landing_start_index=context.landing_sequence_start_index,
        )
        return None


register_state("preflight", PreflightState)
