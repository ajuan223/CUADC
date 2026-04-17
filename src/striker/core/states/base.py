"""Base state — abstract base class for all mission states."""

from __future__ import annotations

from abc import ABC
from typing import TYPE_CHECKING, Any

import structlog

from striker.core.events import Transition

if TYPE_CHECKING:
    from striker.core.context import MissionContext

logger = structlog.get_logger(__name__)


class BaseState(ABC):  # noqa: B024
    """Abstract base class for mission states.

    Each state implements a lifecycle:
    - ``on_enter(context)`` — setup when state becomes active
    - ``execute(context)`` — main state logic (called in loop)
    - ``on_exit(context)`` — cleanup when leaving state
    - ``handle(event)`` — event handler returning optional transition
    """

    @property
    def name(self) -> str:
        """Human-readable state name."""
        return self.__class__.__name__

    async def on_enter(self, context: MissionContext) -> None:
        """Called when this state becomes the active state."""
        context.current_state_name = self.name
        logger.info("State entered", state=self.name)

    async def execute(self, context: MissionContext) -> Transition | None:
        """Main state logic — called repeatedly while this state is active.

        Returns a :class:`Transition` to trigger a state change,
        or ``None`` to stay in the current state.
        """
        return None

    async def on_exit(self, context: MissionContext) -> None:
        """Called when leaving this state."""
        logger.info("State exited", state=self.name)

    def handle(self, event: Any) -> Transition | None:
        """Handle an event, returning an optional transition.

        Override in subclasses for event-driven transitions.
        Global interceptors (OverrideEvent, EmergencyEvent) are handled
        by the FSM engine, not individual states.
        """
        return None
