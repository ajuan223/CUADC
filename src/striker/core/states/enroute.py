"""Enroute state — attack run via temporary AUTO mission."""

from __future__ import annotations

from typing import TYPE_CHECKING

import structlog

from striker.comms.messages import MAV_CMD_MISSION_SET_CURRENT
from striker.core.events import Transition
from striker.core.states import register_state
from striker.core.states.base import BaseState
from striker.flight.mission_geometry import generate_mission_geometry
from striker.flight.mission_upload import upload_attack_mission
from striker.flight.modes import ArduPlaneMode
from striker.utils.geo import calculate_bearing, destination_point, haversine_distance

if TYPE_CHECKING:
    from striker.core.context import MissionContext
    from striker.flight.mission_geometry import MissionGeometryResult

logger = structlog.get_logger(__name__)
LANDING_APPROACH_BUFFER_M = 30.0
MIN_NEAR_APPROACH_LEG_M = 30.0
ATTACK_HANDOFF_ALT_BUFFER_M = 5.0


class EnrouteState(BaseState):
    """Enroute state — attack run via temporary AUTO mission.

    Computes attack run geometry (approach → target → exit), uploads a
    temporary AUTO mission with optional native DO_SET_SERVO release,
    and monitors mission progress for state transition.
    """

    _attack_active: bool = False
    _target_seq: int = 0
    _landing_start_seq: int = 0
    _awaiting_attack_seq_sync: bool = False
    _debug_counter: int = 0

    async def on_enter(self, context: MissionContext) -> None:
        await super().on_enter(context)
        self._attack_active = False
        self._landing_start_seq = 0
        self._awaiting_attack_seq_sync = False
        self._debug_counter = 0

        if context.active_drop_point is None:
            logger.error("No drop point set — cannot enter enroute")
            return

        target_lat, target_lon = context.active_drop_point

        geometry = generate_mission_geometry(
            context.field_profile,
        )
        context.attack_geometry = geometry

        # Calculate approach heading
        approach_heading = _calculate_approach_heading(
            context=context,
            geometry=geometry,
            target_lat=target_lat,
            target_lon=target_lon,
        )

        # Calculate approach and exit points
        attack_cfg = context.field_profile.attack_run
        approach_lat, approach_lon = destination_point(
            target_lat, target_lon,
            (approach_heading + 180) % 360,  # behind target
            attack_cfg.approach_distance_m,
        )
        exit_lat, exit_lon = _calculate_exit_waypoint(
            context=context,
            geometry=geometry,
            target_lat=target_lat,
            target_lon=target_lon,
            approach_heading=approach_heading,
        )

        logger.info(
            "Attack run geometry computed",
            heading=round(approach_heading, 1),
            approach=(round(approach_lat, 6), round(approach_lon, 6)),
            target=(target_lat, target_lon),
            exit=(round(exit_lat, 6), round(exit_lon, 6)),
        )

        # Upload attack + landing mission
        attack_alt = _select_attack_altitude(context, geometry)
        try:
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
                attack_alt_m=attack_alt,
                dry_run=context.settings.dry_run,
                release_channel=context.settings.release_channel,
                release_pwm=context.settings.release_pwm_open,
            )
            self._target_seq = target_seq
            self._landing_start_seq = landing_start_seq
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
            self._awaiting_attack_seq_sync = True
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

        if self._awaiting_attack_seq_sync:
            if current_seq >= self._landing_start_seq:
                logger.info(
                    "Ignoring stale mission progress after attack mission upload",
                    mission_seq=current_seq,
                    landing_start_seq=self._landing_start_seq,
                    target_seq=self._target_seq,
                )
                return None
            if current_seq <= 1:
                self._awaiting_attack_seq_sync = False
                logger.info("Attack mission sequence synchronized", mission_seq=current_seq)
            else:
                return None

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
        if self._target_seq < current_seq < self._landing_start_seq:
            logger.info(
                "Target waypoint passed — triggering release transition",
                current_seq=current_seq,
                target_seq=self._target_seq,
                landing_start_seq=self._landing_start_seq,
            )
            return Transition(target_state="release", reason="Attack run target reached")

        if current_seq >= self._landing_start_seq:
            logger.info(
                "Ignoring out-of-range mission progress during attack run",
                current_seq=current_seq,
                target_seq=self._target_seq,
                landing_start_seq=self._landing_start_seq,
            )

        return None


def _uses_wind_aligned_approach(context: MissionContext) -> bool:
    return bool(context.current_wind and context.current_wind.speed_mps > 2.0)


def _calculate_approach_heading(
    context: MissionContext,
    geometry: MissionGeometryResult,
    target_lat: float,
    target_lon: float,
) -> float:
    """Determine approach heading with priority: upwind > landing-approach alignment."""
    # Priority 1: upwind approach
    if _uses_wind_aligned_approach(context):
        assert context.current_wind is not None
        heading = (context.current_wind.direction_deg + 180) % 360
        logger.debug("Approach heading from wind", heading=heading, wind_dir=context.current_wind.direction_deg)
        return heading

    # Priority 2: aim from the resolved target toward the derived landing approach.
    # Some fallback targets sit materially off the runway centerline, so reusing only
    # the published landing heading can leave the aircraft orbiting around the target
    # without ever advancing to the release/exit leg. When the resolved target already
    # sits at the landing-approach gate, keep using the published landing corridor so
    # the pre-release and post-release legs remain distinct and forward-moving.
    approach_lat, approach_lon, _ = geometry.landing_approach
    distance_to_landing_approach = haversine_distance(
        target_lat,
        target_lon,
        approach_lat,
        approach_lon,
    )
    if distance_to_landing_approach <= MIN_NEAR_APPROACH_LEG_M:
        heading = (context.field_profile.landing.heading_deg + 180.0) % 360.0
        logger.info(
            "Approach heading from landing corridor fallback",
            heading=heading,
            target=(target_lat, target_lon),
            landing_approach=(approach_lat, approach_lon),
            target_to_landing_approach_m=round(distance_to_landing_approach, 1),
            min_leg_m=MIN_NEAR_APPROACH_LEG_M,
        )
        return heading

    heading = calculate_bearing(target_lat, target_lon, approach_lat, approach_lon)
    logger.debug(
        "Approach heading from landing approach alignment",
        heading=heading,
        landing_approach=(approach_lat, approach_lon),
        target=(target_lat, target_lon),
    )
    return heading


def _select_attack_altitude(
    context: MissionContext,
    geometry: MissionGeometryResult,
) -> float:
    landing_approach_alt_m = geometry.landing_approach[2]
    scan_alt_m = context.field_profile.scan.altitude_m
    buffered_handoff_alt_m = landing_approach_alt_m + ATTACK_HANDOFF_ALT_BUFFER_M
    attack_alt_m = min(scan_alt_m, buffered_handoff_alt_m)
    logger.info(
        "Attack altitude selected",
        attack_alt_m=attack_alt_m,
        landing_approach_alt_m=landing_approach_alt_m,
        scan_alt_m=scan_alt_m,
        handoff_buffer_m=ATTACK_HANDOFF_ALT_BUFFER_M,
    )
    return attack_alt_m


def _calculate_exit_waypoint(
    context: MissionContext,
    geometry: MissionGeometryResult,
    target_lat: float,
    target_lon: float,
    approach_heading: float,
) -> tuple[float, float]:
    """Keep the exit leg ahead of the landing approach instead of beyond it."""
    exit_distance_m = context.field_profile.attack_run.exit_distance_m

    if not _uses_wind_aligned_approach(context):
        approach_lat, approach_lon, _ = geometry.landing_approach
        distance_to_landing_approach = haversine_distance(
            target_lat,
            target_lon,
            approach_lat,
            approach_lon,
        )
        min_handoff_leg_m = max(
            LANDING_APPROACH_BUFFER_M,
            min(
                context.field_profile.attack_run.approach_distance_m,
                context.field_profile.landing.runway_length_m,
            ),
        )
        max_safe_exit_distance = max(0.0, distance_to_landing_approach - min_handoff_leg_m)
        if exit_distance_m > max_safe_exit_distance:
            logger.info(
                "Capping exit leg before landing approach",
                configured_exit_distance_m=exit_distance_m,
                capped_exit_distance_m=round(max_safe_exit_distance, 1),
                landing_approach_distance_m=round(distance_to_landing_approach, 1),
                min_handoff_leg_m=round(min_handoff_leg_m, 1),
            )
            exit_distance_m = max_safe_exit_distance

    return destination_point(target_lat, target_lon, approach_heading, exit_distance_m)


register_state("enroute", EnrouteState)
