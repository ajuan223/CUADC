"""Enroute state — attack run via temporary AUTO mission."""

from __future__ import annotations

from typing import TYPE_CHECKING

import structlog

from striker.comms.messages import MAV_CMD_MISSION_SET_CURRENT
from striker.core.events import Transition
from striker.core.states import register_state
from striker.core.states.base import BaseState
from striker.flight.modes import ArduPlaneMode
from striker.flight.mission_geometry import generate_mission_geometry
from striker.flight.mission_upload import upload_attack_mission
from striker.utils.geo import calculate_bearing, destination_point, haversine_distance

if TYPE_CHECKING:
    from striker.core.context import MissionContext

logger = structlog.get_logger(__name__)


class EnrouteState(BaseState):
    """Enroute state — attack run via temporary AUTO mission.

    Computes attack run geometry (approach → target → exit), uploads a
    temporary AUTO mission with optional native DO_SET_SERVO release,
    and monitors mission progress for state transition.
    """

    _attack_active: bool = False
    _target_seq: int = 0
    _debug_counter: int = 0

    async def on_enter(self, context: MissionContext) -> None:
        await super().on_enter(context)
        self._attack_active = False
        self._debug_counter = 0

        if context.active_drop_point is None:
            logger.error("No drop point set — cannot enter enroute")
            return

        target_lat, target_lon = context.active_drop_point

        # Calculate approach heading
        approach_heading = _calculate_approach_heading(context, target_lat, target_lon)

        # Calculate approach and exit points
        attack_cfg = context.field_profile.attack_run
        approach_lat, approach_lon = destination_point(
            target_lat, target_lon,
            (approach_heading + 180) % 360,  # behind target
            attack_cfg.approach_distance_m,
        )
        exit_lat, exit_lon = destination_point(
            target_lat, target_lon,
            approach_heading,  # beyond target
            attack_cfg.exit_distance_m,
        )

        logger.info(
            "Attack run geometry computed",
            heading=round(approach_heading, 1),
            approach=(round(approach_lat, 6), round(approach_lon, 6)),
            target=(target_lat, target_lon),
            exit=(round(exit_lat, 6), round(exit_lon, 6)),
        )

        # Upload attack + landing mission
        try:
            geometry = generate_mission_geometry(context.field_profile)
            target_seq, landing_start_seq = await upload_attack_mission(
                conn=context.connection,
                field_profile=context.field_profile,
                geometry=geometry,
                context=context,
                target_lat=target_lat,
                target_lon=target_lon,
                approach_lat=approach_lat,
                approach_lon=approach_lon,
                exit_lat=exit_lat,
                exit_lon=exit_lon,
                dry_run=context.settings.dry_run,
                release_channel=context.settings.release_channel,
                release_pwm=context.settings.release_pwm_open,
            )
            self._target_seq = target_seq
        except Exception:
            logger.exception("Failed to upload attack mission")
            return

        # Switch to AUTO mode and start at approach waypoint
        try:
            await context.flight_controller.set_mode(ArduPlaneMode.AUTO)

            import asyncio
            await asyncio.sleep(0.5)  # wait for mode switch to take effect

            # Approach waypoint is seq=1 (seq=0 is dummy HOME)
            await context.flight_controller.send_command(
                MAV_CMD_MISSION_SET_CURRENT,
                param1=1.0,
            )
            self._attack_active = True
            logger.info(
                "Attack run initiated",
                target_seq=target_seq,
                landing_start=landing_start_seq,
            )
        except Exception:
            logger.exception("Failed to initiate attack run")

    async def execute(self, context: MissionContext) -> Transition | None:
        if not self._attack_active:
            return None

        self._debug_counter += 1

        current_seq = context.mission_current_seq

        # Log progress every ~5s (at 50ms cycle, every 100 ticks)
        if self._debug_counter % 100 == 0:
            dist_str = "N/A"
            if context.current_position and context.active_drop_point:
                dp_lat, dp_lon = context.active_drop_point
                dist = haversine_distance(
                    context.current_position.lat, context.current_position.lon,
                    dp_lat, dp_lon,
                )
                dist_str = f"{dist:.1f}m"
            logger.info(
                "Attack run progress",
                mission_seq=current_seq,
                target_seq=self._target_seq,
                dist_to_target=dist_str,
            )

        # Target waypoint completed → transition to release
        if current_seq > self._target_seq:
            logger.info(
                "Target waypoint passed — triggering release transition",
                current_seq=current_seq,
                target_seq=self._target_seq,
            )
            return Transition(target_state="release", reason="Attack run target reached")

        return None


def _calculate_approach_heading(context: MissionContext, target_lat: float, target_lon: float) -> float:
    """Determine approach heading with priority: upwind > direct > landing heading fallback."""
    # Priority 1: upwind approach
    if context.current_wind and context.current_wind.speed_mps > 2.0:
        heading = (context.current_wind.direction_deg + 180) % 360
        logger.debug("Approach heading from wind", heading=heading, wind_dir=context.current_wind.direction_deg)
        return heading

    # Priority 2: direct bearing from current position
    if context.current_position:
        heading = calculate_bearing(
            context.current_position.lat, context.current_position.lon,
            target_lat, target_lon,
        )
        logger.debug("Approach heading from current position", heading=round(heading, 1))
        return heading

    # Fallback: reverse of landing heading
    heading = (context.field_profile.landing.heading_deg + 180) % 360
    logger.debug("Approach heading from landing config", heading=heading)
    return heading


register_state("enroute", EnrouteState)
