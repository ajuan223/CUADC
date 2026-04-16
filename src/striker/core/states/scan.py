"""Scan state — execute scan waypoint pattern and decide drop point."""

from __future__ import annotations

from typing import TYPE_CHECKING

import structlog

from striker.core.events import Transition
from striker.core.states import register_state
from striker.core.states.base import BaseState

if TYPE_CHECKING:
    from striker.core.context import MissionContext

logger = structlog.get_logger(__name__)


class ScanState(BaseState):
    """Scan state — follow scan waypoints in AUTO mode.

    Monitors mission progress (MISSION_ITEM_REACHED / MISSION_CURRENT)
    to detect scan completion. On completion, performs drop-point decision:
    - If vision system provided a drop point → use it directly.
    - If no drop point → compute fallback midpoint and use that.
    Then transitions to ENROUTE to fly to the resolved drop point.
    """

    _scan_complete: bool = False
    _last_mission_seq: int = -1

    async def on_enter(self, context: MissionContext) -> None:
        await super().on_enter(context)
        self._scan_complete = False
        self._last_mission_seq = -1
        scan_wp_count = len(context.field_profile.scan_waypoints.waypoints)
        # Use scan_end_seq from context (set by preflight after mission upload)
        # Accounts for ArduPlane HOME item at seq=0 and TAKEOFF at seq=1.
        self._scan_end_seq = context.scan_end_seq or (1 + scan_wp_count)
        logger.info("Scan started", scan_wp_count=scan_wp_count, scan_end_seq=self._scan_end_seq)

    async def execute(self, context: MissionContext) -> Transition | None:
        if self._scan_complete:
            return None

        # Check mission progress
        current_seq = context.mission_current_seq
        if current_seq == self._last_mission_seq:
            return None  # no change
        self._last_mission_seq = current_seq

        if current_seq >= self._scan_end_seq:
            self._scan_complete = True
            logger.info("Scan complete", final_seq=current_seq)

            # Drop-point decision
            drop_point = context.drop_point_tracker.get_smoothed_drop_point() if context.drop_point_tracker else None

            if drop_point is not None:
                lat, lon = drop_point
                context.set_drop_point(lat, lon, source="vision")
                logger.info("Using vision drop point", lat=lat, lon=lon)
            else:
                # Fallback: midpoint between scan end and landing reference
                from striker.config.field_profile import GeoPoint
                from striker.utils.fallback_drop_point import compute_fallback_drop_point

                scan_end = context.last_scan_waypoint
                landing_ref = context.field_profile.landing.approach_waypoint

                if scan_end is not None:
                    lat, lon = compute_fallback_drop_point(scan_end, landing_ref)
                    context.set_drop_point(lat, lon, source="fallback_midpoint")
                    logger.info("Using fallback midpoint drop point", lat=lat, lon=lon)
                else:
                    logger.error("Cannot compute fallback: no scan waypoints defined")
                    return None

            return Transition(target_state="enroute", reason="Scan complete, drop point resolved")

        return None


register_state("scan", ScanState)
