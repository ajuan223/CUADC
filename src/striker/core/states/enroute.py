"""Enroute state — fly to target coordinates."""

from __future__ import annotations

from typing import TYPE_CHECKING

import structlog

from striker.core.events import Transition
from striker.core.states import register_state
from striker.core.states.base import BaseState

if TYPE_CHECKING:
    from striker.core.context import MissionContext

logger = structlog.get_logger(__name__)

# Distance threshold for approach transition (meters)
_APPROACH_DISTANCE_M = 50.0


class EnrouteState(BaseState):
    """Enroute state — GUIDED mode to target coordinates.

    Monitors distance to target and transitions to APPROACH when close enough.
    Updates target if tracker provides new data.
    """

    async def on_enter(self, context: MissionContext) -> None:
        await super().on_enter(context)
        if context.last_target:
            target = context.last_target
            lat = getattr(target, "lat", 0.0)
            lon = getattr(target, "lon", 0.0)
            await context.flight_controller.goto(lat, lon, context.field_profile.scan_waypoints.altitude_m)
            logger.info("Enroute: heading to target", lat=lat, lon=lon)

    async def execute(self, context: MissionContext) -> Transition | None:
        # Check if tracker has updated target
        target = context.target_tracker.get_smoothed_target() if context.target_tracker else None
        if target is not None:
            context.update_target(target)

        # Check distance to target
        if context.current_position and context.last_target:
            pos = context.current_position
            tgt = context.last_target
            # Simplified distance check (would use haversine in production)
            dlat = pos.lat - getattr(tgt, "lat", 0.0)
            dlon = pos.lon - getattr(tgt, "lon", 0.0)
            # Rough estimate ~111m per 0.001 deg
            dist_m = ((dlat ** 2 + dlon ** 2) ** 0.5) * 111_000

            if dist_m <= _APPROACH_DISTANCE_M:
                logger.info("Approach distance reached", dist_m=dist_m)
                return Transition(target_state="approach", reason="Near target")

        return None


register_state("enroute", EnrouteState)
