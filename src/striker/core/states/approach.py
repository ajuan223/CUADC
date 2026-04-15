"""Approach state — fly to release point computed by ballistic solver."""

from __future__ import annotations

from typing import TYPE_CHECKING

import structlog

from striker.core.events import Transition
from striker.core.states import register_state
from striker.core.states.base import BaseState

if TYPE_CHECKING:
    from striker.core.context import MissionContext

logger = structlog.get_logger(__name__)


class ApproachState(BaseState):
    """Approach state — GUIDED flight to computed release point.

    Calculates release point via ballistic solver, then flies to it.
    Transitions to RELEASE on arrival.
    """

    _release_lat: float = 0.0
    _release_lon: float = 0.0
    _heading_to_release: bool = False

    async def on_enter(self, context: MissionContext) -> None:
        await super().on_enter(context)

        # Calculate release point
        if context.current_position and context.last_target:
            target = context.last_target
            pos = context.current_position
            # Decompose ground speed + heading to NED velocity
            # Simplified: assume velocity from speed data
            self._release_lat, self._release_lon = (
                context.ballistic_calculator.calculate_release_point(
                    target_lat=getattr(target, "lat", 0.0),
                    target_lon=getattr(target, "lon", 0.0),
                    altitude_m=pos.alt_m,
                )
            )
            logger.info("Release point calculated", lat=self._release_lat, lon=self._release_lon)
        else:
            logger.error("Cannot calculate release point — no position/target")
            self._release_lat = 0.0
            self._release_lon = 0.0

    async def execute(self, context: MissionContext) -> Transition | None:
        if not self._heading_to_release and self._release_lat != 0.0:
            try:
                await context.flight_controller.goto(
                    self._release_lat, self._release_lon,
                    context.field_profile.scan_waypoints.altitude_m,
                )
                self._heading_to_release = True
            except Exception:
                logger.exception("Failed to goto release point")
                return None

        # Check arrival at release point (simplified)
        if context.current_position and self._heading_to_release:
            dlat = context.current_position.lat - self._release_lat
            dlon = context.current_position.lon - self._release_lon
            dist = ((dlat ** 2 + dlon ** 2) ** 0.5) * 111_000
            if dist < 10.0:
                return Transition(target_state="release", reason="At release point")

        return None


register_state("approach", ApproachState)
