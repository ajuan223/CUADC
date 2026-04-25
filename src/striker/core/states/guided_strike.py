"""Guided strike state — programmatically controlled attack run in GUIDED mode."""

from __future__ import annotations

import math
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
        self.wp_radius = 150.0  # fallback wp_radius (must be > min turn radius of ~90m)
        self.release_radius = 50.0  # fallback release radius
        self.cross_track_limit = 100.0  # max lateral offset at gate crossing to trigger release
        self.attack_alt_m = 100.0
        self._prev_progress: float | None = None  # progress along approach→exit axis for crossing detection

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

        # Cross-track limit: wider than proximity radius to handle wind drift
        self.cross_track_limit = self.release_radius * 2.0  # gate fires if on-axis enough
        self._gate_deferred = False
        self._gate_cross_track: float | None = None

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
            dist = haversine_distance(
                current_lat, current_lon, self.approach_point[0], self.approach_point[1]
            )
            if dist <= self.wp_radius:
                self.phase = StrikePhase.STRIKE
                self._prev_progress = 0.0  # entering STRIKE from approach (progress=0)
                assert self.target_point is not None
                assert self.exit_point is not None
                # Command it to go to the EXIT point so it flies THROUGH the target point!
                # If we command it to go to target_point, ArduPlane GUIDED mode will try to ORBIT the target point.
                await context.flight_controller.goto(
                    self.exit_point[0], self.exit_point[1], self.attack_alt_m
                )
                logger.info(
                    "Phase: STRIKE (navigating to EXIT point to pass through target)",
                    target_lat=self.target_point[0], target_lon=self.target_point[1],
                )

        elif self.phase == StrikePhase.STRIKE:
            assert self.target_point is not None
            assert self.approach_point is not None
            assert self.exit_point is not None

            # Compute progress along approach→exit axis (0 at approach, 1 at exit)
            progress, cross_track = self._project_onto_axis(
                current_lat, current_lon,
                self.approach_point, self.exit_point,
            )

            # Target is at a known fraction along the axis
            target_frac, _ = self._project_onto_axis(
                self.target_point[0], self.target_point[1],
                self.approach_point, self.exit_point,
            )

            # Trigger when aircraft crosses the target's perpendicular plane
            released = False
            if self._prev_progress is not None and self._prev_progress < target_frac and progress >= target_frac:
                if cross_track <= self.cross_track_limit:
                    await self._trigger_release(context, current_lat, current_lon)
                    self.phase = StrikePhase.EXIT
                    released = True
                    assert self.exit_point is not None
                    logger.info(
                        "Phase: EXIT (crossing exact target gate)",
                        target_lat=self.exit_point[0], target_lon=self.exit_point[1],
                        cross_track=cross_track
                    )
                else:
                    logger.warning(
                        "Crossed target gate but cross-track too large",
                        cross_track=cross_track,
                        limit=self.cross_track_limit,
                    )
                    self._gate_deferred = True
                    self._gate_cross_track = cross_track

            # Fallback: proximity trigger for cases where crossing detection misses
            # We must NOT trigger prematurely before crossing the gate. So we only allow proximity
            # fallback if we've already passed the gate (progress >= target_frac) but deferred it
            # because of cross-track, OR if the distance is extremely small (< 2 meters).
            if not released:
                dist = haversine_distance(
                    current_lat, current_lon, self.target_point[0], self.target_point[1]
                )

                # If we are literally on top of it (< 2m), release immediately.
                # If we passed the gate but cross_track was too large, we still drop if we
                # ever get within effective_radius.
                if self._gate_deferred and self._gate_cross_track is not None:
                    effective_radius = max(self.release_radius, self._gate_cross_track)
                else:
                    effective_radius = 2.0
                if dist <= effective_radius and (progress >= target_frac or dist <= 2.0):
                    await self._trigger_release(context, current_lat, current_lon)
                    self.phase = StrikePhase.EXIT
                    assert self.exit_point is not None
                    logger.info(
                        "Phase: EXIT (proximity fallback to exact target)",
                        target_lat=self.exit_point[0], target_lon=self.exit_point[1],
                    )

            self._prev_progress = progress

        elif self.phase == StrikePhase.EXIT:
            assert self.exit_point is not None
            dist = haversine_distance(
                current_lat, current_lon, self.exit_point[0], self.exit_point[1]
            )
            if dist <= self.wp_radius:
                logger.info("Guided strike completed")
                return Transition(target_state="release_monitor", reason="Strike sequence complete")

        return None

    def _project_onto_axis(
        self,
        lat: float, lon: float,
        p_start: tuple[float, float],
        p_end: tuple[float, float],
    ) -> tuple[float, float]:
        """Project a point onto the approach→exit axis.

        Returns (progress, cross_track) where progress is 0..1 along the axis
        and cross_track is the perpendicular distance in meters.
        """
        cos_lat = math.cos(math.radians(lat))
        ax = (p_end[1] - p_start[1]) * 111_320 * cos_lat
        ay = (p_end[0] - p_start[0]) * 111_320
        px = (lon - p_start[1]) * 111_320 * cos_lat
        py = (lat - p_start[0]) * 111_320

        axis_len_sq = ax * ax + ay * ay
        if axis_len_sq < 1e-6:
            return 0.0, 0.0

        progress = (px * ax + py * ay) / axis_len_sq
        proj_x = progress * ax
        proj_y = progress * ay
        cross_track = math.sqrt((px - proj_x) ** 2 + (py - proj_y) ** 2)
        return progress, cross_track

    async def _trigger_release(self, context: MissionContext, lat: float, lon: float) -> None:
        """Fire DO_SET_SERVO and record the drop point."""
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
        context.set_actual_drop_point(lat, lon, "guided_strike")
