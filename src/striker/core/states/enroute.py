"""Enroute state — fly to the resolved drop point."""

from __future__ import annotations

from typing import TYPE_CHECKING

import structlog

from striker.core.events import Transition
from striker.core.states import register_state
from striker.core.states.base import BaseState
from striker.utils.geo import haversine_distance

if TYPE_CHECKING:
    from striker.core.context import MissionContext

logger = structlog.get_logger(__name__)

# Distance threshold for release transition (meters).
# ArduPlane GUIDED mode orbits the target (loiter radius ~50-80m), so the
# aircraft never reaches the exact point. This threshold must be larger than
# the typical loiter radius.
_RELEASE_DISTANCE_M = 100.0


class EnrouteState(BaseState):
    """Enroute state — GUIDED mode to the active drop point.

    Uses the drop point resolved by ScanState (either vision or fallback
    midpoint). Monitors distance and transitions to RELEASE when close enough.
    """

    _heading_to_drop: bool = False
    _debug_counter: int = 0

    async def on_enter(self, context: MissionContext) -> None:
        await super().on_enter(context)
        self._heading_to_drop = False

        if context.active_drop_point is None:
            logger.error("No drop point set — cannot enter enroute")
            return

        lat, lon = context.active_drop_point
        alt_m = context.field_profile.scan_waypoints.altitude_m
        try:
            await context.flight_controller.goto(lat, lon, alt_m)
            self._heading_to_drop = True
            logger.info("Enroute: heading to drop point", lat=lat, lon=lon, source=context.drop_point_source)
        except Exception:
            logger.exception("Failed to goto drop point")

    async def execute(self, context: MissionContext) -> Transition | None:
        if not self._heading_to_drop or context.active_drop_point is None:
            return None

        dp_lat, dp_lon = context.active_drop_point

        # Re-send position target periodically (~1Hz) to keep GUIDED mode active.
        # ArduPlane GUIDED mode times out without continuous position targets.
        self._debug_counter += 1
        if self._debug_counter % 20 == 0:  # every ~1s at 50ms cycle
            try:
                await context.flight_controller.resend_position_target(dp_lat, dp_lon, context.field_profile.scan_waypoints.altitude_m)
            except Exception:
                logger.debug("Position target re-send failed (non-fatal)")

        if context.current_position:
            dist_m = haversine_distance(
                context.current_position.lat, context.current_position.lon,
                dp_lat, dp_lon,
            )
            if self._debug_counter % 100 == 0:  # ~every 5s
                logger.info("Enroute distance", dist_m=round(dist_m, 1), lat=context.current_position.lat, lon=context.current_position.lon)
            if dist_m <= _RELEASE_DISTANCE_M:
                logger.info("Drop point reached", dist_m=dist_m)
                return Transition(target_state="release", reason="At drop point")
        else:
            if self._debug_counter % 100 == 0:
                logger.warning("Enroute: no position data")

        return None


register_state("enroute", EnrouteState)
