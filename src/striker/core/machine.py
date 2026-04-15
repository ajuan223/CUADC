"""Mission state machine engine — async FSM with global interceptors.

Uses ``python-statemachine`` declarative syntax with ``rtc=False`` to prevent
run-to-completion deadlocks in async contexts.
"""

from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING, Any

import structlog
from statemachine import State, StateMachine

from striker.core.events import EmergencyEvent, OverrideEvent, Transition

if TYPE_CHECKING:
    from striker.core.context import MissionContext
    from striker.core.states.base import BaseState

logger = structlog.get_logger(__name__)


# ── Declarative state machine using python-statemachine ───────────


class MissionStateMachine(StateMachine):
    """Declarative mission state machine.

    States
    ------
    INIT → PREFLIGHT → TAKEOFF → SCAN ↔ LOITER → ENROUTE →
    APPROACH → RELEASE → LANDING → COMPLETED
    OVERRIDE (terminal), EMERGENCY (terminal)

    Global interceptors: OverrideEvent → OVERRIDE, EmergencyEvent → EMERGENCY
    """

    # ── States ────────────────────────────────────────────────────
    init = State(initial=True)
    preflight = State()
    takeoff = State()
    scan = State()
    loiter = State()
    enroute = State()
    approach = State()
    release = State()
    landing = State()
    completed = State(final=True)
    override = State(final=True)
    emergency = State()

    # ── Transitions ───────────────────────────────────────────────
    to_preflight = init.to(preflight)
    to_takeoff = preflight.to(takeoff)
    to_scan = takeoff.to(scan) | loiter.to(scan)
    to_loiter = scan.to(loiter)
    to_enroute = loiter.to(enroute)
    to_approach = enroute.to(approach)
    to_release = approach.to(release)
    to_landing = release.to(landing) | emergency.to(landing)
    to_completed = landing.to(completed)
    to_override = (
        init.to(override)
        | preflight.to(override)
        | takeoff.to(override)
        | scan.to(override)
        | loiter.to(override)
        | enroute.to(override)
        | approach.to(override)
        | release.to(override)
        | landing.to(override)
    )
    to_emergency = (
        init.to(emergency)
        | preflight.to(emergency)
        | takeoff.to(emergency)
        | scan.to(emergency)
        | loiter.to(emergency)
        | enroute.to(emergency)
        | approach.to(emergency)
        | release.to(emergency)
        | landing.to(emergency)
    )

    # Force RTC off for async safety
    class Meta:
        rtc = False

    # ── Lifecycle hooks ───────────────────────────────────────────

    def __init__(self, model: Any = None, state_field: str = "state", **kwargs: Any) -> None:
        super().__init__(model=model, state_field=state_field, **kwargs)
        self._context: MissionContext | None = None
        self._state_instances: dict[str, BaseState] = {}
        self._running = False

    @property
    def current_state_name(self) -> str:
        """Current state as a string."""
        return str(self.current_state.id)  # noqa: DEP001

    def bind_context(self, context: MissionContext) -> None:
        """Bind the mission context to this state machine."""
        self._context = context

    def register_state_instance(self, name: str, state: BaseState) -> None:
        """Register a state instance for lifecycle callbacks."""
        self._state_instances[name] = state

    # ── on_enter / on_exit logging ────────────────────────────────

    def on_enter_state(self, state: State, *args: Any, **kwargs: Any) -> None:
        logger.info("FSM transition", to=state.id)

    # ── Run loop ──────────────────────────────────────────────────

    async def run(self, context: MissionContext) -> None:
        """Main async run loop — pump events and execute current state."""
        self._context = context
        self._running = True

        current_state = self._get_current_state_instance()
        if current_state and context:
            await current_state.on_enter(context)

        while self._running:
            current_state = self._get_current_state_instance()
            if current_state is None:
                logger.warning("No state instance for current state", state=self.current_state_name)
                await asyncio.sleep(0.1)
                continue

            # Execute current state logic
            if context:
                transition = await current_state.execute(context)
                if transition is not None:
                    await self._perform_transition(transition, context)

            await asyncio.sleep(0.05)  # 50ms cycle

    async def _perform_transition(self, transition: Transition, context: MissionContext) -> None:
        """Execute a state transition."""
        old_state = self._get_current_state_instance()
        if old_state:
            await old_state.on_exit(context)

        # Trigger the transition on the state machine
        target = transition.target_state.upper()
        transition_method = getattr(self, f"to_{transition.target_state.lower()}", None)
        if transition_method:
            transition_method()
        else:
            logger.error("No transition method", target=transition.target_state)

        new_state = self._get_current_state_instance()
        if new_state:
            await new_state.on_enter(context)

    def _get_current_state_instance(self) -> BaseState | None:
        """Get the state instance for the current FSM state."""
        return self._state_instances.get(self.current_state_name)

    async def process_event(self, event: Any) -> None:
        """Process an external event — global interceptors first."""
        if isinstance(event, OverrideEvent):
            if self._context:
                old = self._get_current_state_instance()
                if old:
                    await old.on_exit(self._context)
            self.to_override()
            new = self._get_current_state_instance()
            if new and self._context:
                await new.on_enter(self._context)
            return

        if isinstance(event, EmergencyEvent):
            if self._context:
                old = self._get_current_state_instance()
                if old:
                    await old.on_exit(self._context)
            self.to_emergency()
            new = self._get_current_state_instance()
            if new and self._context:
                await new.on_enter(self._context)
            return

        # Delegate to current state's handle method
        current = self._get_current_state_instance()
        if current:
            transition = current.handle(event)
            if transition and self._context:
                await self._perform_transition(transition, self._context)

    def stop(self) -> None:
        """Signal the run loop to stop."""
        self._running = False
