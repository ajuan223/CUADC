"""Loiter state — orbit and wait for target or timeout."""

from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING

import structlog

from striker.core.events import Transition
from striker.core.states import register_state
from striker.core.states.base import BaseState

if TYPE_CHECKING:
    from striker.core.context import MissionContext

logger = structlog.get_logger(__name__)


class LoiterState(BaseState):
    """Loiter state — orbit with configurable timeout.

    Waits for:
    - TARGET_ACQUIRED → ENROUTE
    - Timeout with cycle < max → SCAN (rescan)
    - Timeout with cycle >= max → FORCED_STRIKE
    """

    _elapsed_s: float = 0.0
    _timeout_s: float = 60.0
    _max_cycles: int = 3
    _cycle_start: float = 0.0

    async def on_enter(self, context: MissionContext) -> None:
        await super().on_enter(context)
        self._timeout_s = context.settings.loiter_timeout_s
        self._max_cycles = context.settings.max_scan_cycles
        self._elapsed_s = 0.0
        self._cycle_start = asyncio.get_event_loop().time()
        logger.info("Loiter started", timeout_s=self._timeout_s, cycle=context.scan_cycle_count)

    async def execute(self, context: MissionContext) -> Transition | None:
        now = asyncio.get_event_loop().time()
        self._elapsed_s = now - self._cycle_start

        # Check for target from tracker
        target = context.target_tracker.get_smoothed_target() if context.target_tracker else None
        if target is not None:
            logger.info("Target acquired in loiter", target=str(target))
            context.update_target(target)
            return Transition(target_state="enroute", reason="Target acquired")

        # Check timeout
        if self._elapsed_s >= self._timeout_s:
            if context.scan_cycle_count < self._max_cycles:
                logger.info("Loiter timeout — rescanning", cycle=context.scan_cycle_count)
                return Transition(target_state="scan", reason="Loiter timeout, rescan")
            else:
                logger.warning(
                    "Max scan cycles reached — forced strike",
                    cycle=context.scan_cycle_count,
                    max=self._max_cycles,
                )
                return Transition(target_state="forced_strike", reason="Max scan cycles reached")

        return None


register_state("loiter", LoiterState)
