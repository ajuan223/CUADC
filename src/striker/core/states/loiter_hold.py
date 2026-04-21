"""Loiter hold state — intercept drop point and overwrite mission slots."""

from __future__ import annotations

from typing import TYPE_CHECKING

import structlog

from striker.comms.messages import MAV_CMD_MISSION_SET_CURRENT
from striker.core.events import Transition
from striker.core.states import register_state
from striker.core.states.base import BaseState
from striker.exceptions import StrikerError
from striker.flight.attack_geometry import compute_attack_slots
from striker.flight.mission_upload import partial_write_mission
from striker.vision.global_var import get_vision_drop_point

if TYPE_CHECKING:
    from striker.core.context import MissionContext

logger = structlog.get_logger(__name__)


class LoiterHoldState(BaseState):
    """Wait in loiter, inject drop point, and unblock."""

    async def on_enter(self, context: MissionContext) -> None:
        context.current_state_name = "loiter_hold"
        logger.info("Entering loiter hold")

    async def execute(self, context: MissionContext) -> Transition | None:
        if not context.preburned_info:
            return None

        # 1. Resolve Drop Point
        drop_point = get_vision_drop_point()
        source = "vision"
        if not drop_point:
            fallback = context.field_profile.attack_run.fallback_drop_point
            if fallback:
                drop_point = (fallback.lat, fallback.lon)
                source = "fallback_field"

        if not drop_point:
            logger.error("No drop point available (no vision, no fallback)")
            return None

        context.set_drop_point(drop_point[0], drop_point[1], source)

        # 2. Compute attack slots
        runway_heading = context.field_profile.landing.heading_deg
        items = compute_attack_slots(
            drop_lat=drop_point[0],
            drop_lon=drop_point[1],
            approach_heading_deg=runway_heading,
            approach_distance_m=context.field_profile.attack_run.approach_distance_m,
            exit_distance_m=context.field_profile.attack_run.exit_distance_m,
            attack_alt_m=context.field_profile.scan.altitude_m,
            release_channel=context.settings.release_channel,
            release_pwm=context.settings.release_pwm_open,
            mav=context.connection.mav,
        )

        # 3. Overwrite reserved slots
        start_seq = context.preburned_info.slot_start_seq
        end_seq = context.preburned_info.slot_end_seq

        try:
            await partial_write_mission(
                conn=context.connection,
                start_seq=start_seq,
                end_seq=end_seq,
                items=items,
            )
            logger.info("Overwrote mission slots", start=start_seq, end=end_seq)
        except StrikerError as e:
            logger.error("Partial write failed", error=str(e))
            return None

        # 4. Unblock (MISSION_SET_CURRENT to slot_0)
        try:
            await context.flight_controller.send_command(
                MAV_CMD_MISSION_SET_CURRENT,
                param1=start_seq,
            )
            logger.info("Unblocked mission", seq=start_seq)
            return Transition("attack_run", "Injected drop point and unblocked")
        except StrikerError as e:
            logger.error("Unblock failed", error=str(e))
            return None

register_state("loiter_hold", LoiterHoldState)
