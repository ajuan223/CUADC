"""Landing state — monitor the active landing-only sequence."""

from __future__ import annotations

from typing import TYPE_CHECKING

import structlog

from striker.comms.messages import MAV_CMD_MISSION_SET_CURRENT
from striker.core.events import OverrideEvent, Transition
from striker.core.states import register_state
from striker.core.states.base import BaseState
from striker.flight.modes import ArduPlaneMode

if TYPE_CHECKING:
    from striker.core.context import MissionContext

logger = structlog.get_logger(__name__)
LANDING_STATUSTEXT_MARKERS = (
    "hit ground",
    "land complete",
    "throttle disarmed",
)
LANDING_STATUSTEXT_MAX_REL_ALT_M = 5.0


class LandingState(BaseState):
    """Landing state — monitor the active landing-only sequence."""

    _landing_triggered: bool = False
    _low_altitude_samples: int = 0
    _stalled_ground_samples: int = 0

    async def on_enter(self, context: MissionContext) -> None:
        await super().on_enter(context)
        self._landing_triggered = False
        self._low_altitude_samples = 0
        self._stalled_ground_samples = 0

    async def execute(self, context: MissionContext) -> Transition | None:
        if not self._landing_triggered:
            try:
                await context.flight_controller.set_mode(ArduPlaneMode.AUTO)

                landing_start_index = context.landing_sequence_start_index
                if landing_start_index is None:
                    logger.error("Landing sequence start index unavailable")
                    return None
                await context.flight_controller.send_command(
                    MAV_CMD_MISSION_SET_CURRENT,
                    param1=float(landing_start_index),
                )
                self._landing_triggered = True
                logger.info("Landing sequence monitoring", start_index=landing_start_index)
            except Exception:
                logger.exception("Failed to enter landing monitoring")
                return None

        pos = context.current_position
        if pos is None:
            return None

        status_text = context.last_status_text.lower()
        if any(marker in status_text for marker in LANDING_STATUSTEXT_MARKERS):
            if pos.relative_alt_m <= LANDING_STATUSTEXT_MAX_REL_ALT_M:
                logger.info(
                    "Landing detected",
                    alt=pos.relative_alt_m,
                    reason="status_text",
                    status_text=context.last_status_text,
                )
                return Transition(target_state="completed", reason="Landing complete")
            logger.warning(
                "Ignoring landing status text while still airborne",
                alt=pos.relative_alt_m,
                status_text=context.last_status_text,
                max_rel_alt_m=LANDING_STATUSTEXT_MAX_REL_ALT_M,
            )

        if pos.relative_alt_m < 1.0:
            self._low_altitude_samples += 1
        else:
            self._low_altitude_samples = 0

        if pos.relative_alt_m < 60.0 and context.connection.flightmode.upper() == "MANUAL":
            self._stalled_ground_samples += 1
        else:
            self._stalled_ground_samples = 0

        if self._low_altitude_samples >= 1:
            logger.info("Landing detected", alt=pos.relative_alt_m, reason="relative_altitude")
            return Transition(target_state="completed", reason="Landing complete")

        if self._stalled_ground_samples >= 20:
            logger.warning(
                "Landing ended in manual near-ground state — relinquishing autonomy",
                alt=pos.relative_alt_m,
                samples=self._stalled_ground_samples,
            )
            return Transition(target_state="override", reason="Landing ended in manual near ground")

        return None

    def handle(self, event: object) -> Transition | None:
        if isinstance(event, OverrideEvent):
            return Transition(target_state="override", reason=event.reason)
        return None


register_state("landing", LandingState)
