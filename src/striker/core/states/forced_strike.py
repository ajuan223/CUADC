"""Forced strike state — random point drop after max scan cycles."""

from __future__ import annotations

from typing import TYPE_CHECKING

import structlog

from striker.core.events import Transition
from striker.core.states import register_state
from striker.core.states.base import BaseState
from striker.utils.forced_strike_point import generate_forced_strike_point
from striker.utils.point_in_polygon import point_in_polygon

if TYPE_CHECKING:
    from striker.core.context import MissionContext

logger = structlog.get_logger(__name__)


class ForcedStrikeState(BaseState):
    """Forced strike degradation state after max scan cycles.

    Generates a random point inside the geofence and flies to it
    for payload release.
    """

    _strike_lat: float = 0.0
    _strike_lon: float = 0.0
    _heading_to_strike: bool = False
    _released: bool = False

    async def on_enter(self, context: MissionContext) -> None:
        await super().on_enter(context)

        # Generate random strike point inside geofence
        polygon = [(p.lat, p.lon) for p in context.field_profile.boundary.polygon]
        self._strike_lat, self._strike_lon = generate_forced_strike_point(
            polygon, buffer_m=context.field_profile.safety_buffer_m,
        )

        # Validate with point_in_polygon (RL-10)
        if not point_in_polygon(self._strike_lat, self._strike_lon, polygon):
            logger.error("Forced strike point outside geofence!")
            return

        logger.info(
            "Forced strike point generated",
            lat=self._strike_lat,
            lon=self._strike_lon,
        )

        if context.settings.dry_run:
            logger.info("DRY_RUN: Would fly to forced strike point")

    async def execute(self, context: MissionContext) -> Transition | None:
        if not self._heading_to_strike:
            try:
                await context.flight_controller.goto(
                    self._strike_lat, self._strike_lon,
                    context.field_profile.scan_waypoints.altitude_m,
                )
                self._heading_to_strike = True
            except Exception:
                logger.exception("Failed to goto forced strike point")
                return None

        # Check arrival
        if context.current_position and self._heading_to_strike:
            dlat = context.current_position.lat - self._strike_lat
            dlon = context.current_position.lon - self._strike_lon
            dist = ((dlat ** 2 + dlon ** 2) ** 0.5) * 111_000
            if dist < 10.0 and not self._released:
                if context.settings.dry_run:
                    logger.info("DRY_RUN: Would release at forced strike point")
                    self._released = True
                    return Transition(target_state="landing", reason="Forced strike complete (dry run)")
                try:
                    success = await context.release_controller.release()
                    if success:
                        self._released = True
                        return Transition(target_state="landing", reason="Forced strike complete")
                except Exception:
                    logger.exception("Forced strike release error")

        return None


register_state("forced_strike", ForcedStrikeState)
