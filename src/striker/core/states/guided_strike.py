"""Guided strike state — programmatically controlled attack run in GUIDED mode."""

from __future__ import annotations

import time
from enum import Enum, auto
from typing import TYPE_CHECKING

import structlog

from striker.comms.messages import MAV_CMD_DO_SET_SERVO
from striker.core.events import Transition
from striker.core.states.base import BaseState
from striker.flight.attack_geometry import compute_attack_geometry
from striker.utils.geo import haversine_distance

if TYPE_CHECKING:
    from striker.core.context import MissionContext

logger = structlog.get_logger(__name__)


class StrikePhase(Enum):
    INIT = auto()
    APPROACH = auto()
    STRIKE = auto()
    EXIT = auto()


class GuidedStrikeState(BaseState):
    """Programmatically controlled attack run in GUIDED mode.

    Replaces preburned slot overwriting. Navigates through approach,
    target, and exit points using DO_REPOSITION, and explicitly
    triggers DO_SET_SERVO for payload release.
    """

    def __init__(self) -> None:
        self.phase = StrikePhase.INIT
        self.approach_point: tuple[float, float] | None = None
        self.target_point: tuple[float, float] | None = None
        self.exit_point: tuple[float, float] | None = None
        self.wp_radius = 30.0  # fallback wp_radius
        self.release_radius = 10.0  # fallback release radius
        self.attack_alt_m = 100.0

    async def on_enter(self, context: MissionContext) -> None:
        await super().on_enter(context)
        self.phase = StrikePhase.INIT

        # Determine drop point: vision > fallback
        drop_point = None
        source = ""

        # Assuming vision drop point is already in context if valid
        if context.active_drop_point:
            drop_point = context.active_drop_point
            source = context.drop_point_source
        elif context.field_profile.attack_run.fallback_drop_point:
            fallback = context.field_profile.attack_run.fallback_drop_point
            drop_point = (fallback.lat, fallback.lon)
            source = "fallback_field"

        if not drop_point:
            logger.error("No valid drop point available for guided strike")
            # We can't transition to release_monitor or safely fly.
            # State will just do nothing, relying on loiter safety anchor.
            return

        context.set_drop_point(drop_point[0], drop_point[1], source)
        logger.info("Starting guided strike", lat=drop_point[0], lon=drop_point[1], source=source)

        # Compute geometry
        heading = 0.0
        if context.current_wind and context.current_wind.speed_mps > 2.0:
            heading = context.current_wind.direction_deg
        elif context.current_position:
            from striker.utils.geo import calculate_bearing
            heading = calculate_bearing(
                context.current_position.lat,
                context.current_position.lon,
                drop_point[0],
                drop_point[1],
            )
        else:
            heading = (context.field_profile.landing.heading_deg + 180) % 360

        approach, target, exit_pt = compute_attack_geometry(
            drop_point[0],
            drop_point[1],
            heading,
            context.field_profile.attack_run.approach_distance_m,
            context.field_profile.attack_run.exit_distance_m,
        )
        self.approach_point = approach
        self.target_point = target
        self.exit_point = exit_pt

        self.attack_alt_m = context.field_profile.scan.altitude_m

        # wp_radius config
        if hasattr(context.field_profile.attack_run, "release_acceptance_radius_m"):
            self.release_radius = context.field_profile.attack_run.release_acceptance_radius_m
        if hasattr(context.field_profile, "wp_radius_m"):
            self.wp_radius = context.field_profile.wp_radius_m

        # Switch to GUIDED and start navigation
        await context.flight_controller.goto(
            self.approach_point[0], self.approach_point[1], self.attack_alt_m
        )
        self.phase = StrikePhase.APPROACH
        logger.info("Phase: APPROACH", target_lat=self.approach_point[0], target_lon=self.approach_point[1])

    async def execute(self, context: MissionContext) -> Transition | None:
        if self.phase == StrikePhase.INIT or not context.current_position:
            return None

        current_lat = context.current_position.lat
        current_lon = context.current_position.lon

        if self.phase == StrikePhase.APPROACH:
            assert self.approach_point is not None
            await context.flight_controller.resend_position_target(
                self.approach_point[0], self.approach_point[1], self.attack_alt_m
            )
            dist = haversine_distance(
                current_lat, current_lon, self.approach_point[0], self.approach_point[1]
            )
            if dist <= self.wp_radius:
                self.phase = StrikePhase.STRIKE
                assert self.target_point is not None
                await context.flight_controller.goto(
                    self.target_point[0], self.target_point[1], self.attack_alt_m
                )
                logger.info("Phase: STRIKE", target_lat=self.target_point[0], target_lon=self.target_point[1])

        elif self.phase == StrikePhase.STRIKE:
            assert self.target_point is not None
            await context.flight_controller.resend_position_target(
                self.target_point[0], self.target_point[1], self.attack_alt_m
            )
            dist = haversine_distance(
                current_lat, current_lon, self.target_point[0], self.target_point[1]
            )
            if dist <= self.release_radius:
                # Trigger release
                if not context.settings.dry_run:
                    await context.flight_controller.send_command(
                        MAV_CMD_DO_SET_SERVO,
                        param1=context.settings.release_channel,
                        param2=context.settings.release_pwm_open,
                    )
                    logger.info("Payload released (native DO_SET_SERVO)")
                else:
                    logger.info("Payload release simulated (dry_run=True)")

                context.mark_release_triggered(time.time())
                context.set_actual_drop_point(current_lat, current_lon, "guided_strike")

                self.phase = StrikePhase.EXIT
                assert self.exit_point is not None
                await context.flight_controller.goto(
                    self.exit_point[0], self.exit_point[1], self.attack_alt_m
                )
                logger.info("Phase: EXIT", target_lat=self.exit_point[0], target_lon=self.exit_point[1])

        elif self.phase == StrikePhase.EXIT:
            assert self.exit_point is not None
            await context.flight_controller.resend_position_target(
                self.exit_point[0], self.exit_point[1], self.attack_alt_m
            )
            dist = haversine_distance(
                current_lat, current_lon, self.exit_point[0], self.exit_point[1]
            )
            if dist <= self.wp_radius:
                logger.info("Guided strike completed")
                return Transition(target_state="release_monitor", reason="Strike sequence complete")

        return None
