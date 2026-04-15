"""INIT state — system startup, subsystem initialization."""

from __future__ import annotations

from typing import TYPE_CHECKING

from striker.core.events import SystemEvent, Transition
from striker.core.states import register_state
from striker.core.states.base import BaseState

if TYPE_CHECKING:
    from striker.core.context import MissionContext


class InitState(BaseState):
    """Initial state — waits for all subsystems to report ready."""

    async def on_enter(self, context: MissionContext) -> None:
        await super().on_enter(context)
        self._ready = False

    async def execute(self, context: MissionContext) -> Transition | None:
        if self._ready:
            return Transition(target_state="preflight", reason="Initialization complete")
        return None

    def handle(self, event: object) -> Transition | None:
        if isinstance(event, SystemEvent) and event == SystemEvent.INIT_COMPLETE:
            self._ready = True
            return Transition(target_state="preflight", reason="INIT_COMPLETE received")
        return None


register_state("init", InitState)
