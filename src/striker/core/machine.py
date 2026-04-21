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

    Simplified flow:
    INIT → STANDBY → SCAN_MONITOR → GUIDED_STRIKE → RELEASE_MONITOR → LANDING_MONITOR → COMPLETED
    OVERRIDE (terminal), EMERGENCY (terminal)

    SCAN_MONITOR completes → GUIDED_STRIKE:
      - vision drop point available → approach -> strike -> exit
      - no vision drop point → use fallback → approach -> strike -> exit

    Global interceptors: OverrideEvent → OVERRIDE, EmergencyEvent → EMERGENCY
    """

    # ── States ────────────────────────────────────────────────────
    init = State(initial=True)
    standby = State()
    scan_monitor = State()
    guided_strike = State()
    release_monitor = State()
    landing_monitor = State()
    completed = State(final=True)
    override = State(final=True)
    emergency = State()

    # ── Transitions ───────────────────────────────────────────────
    to_standby = init.to(standby)
    to_scan_monitor = standby.to(scan_monitor)
    to_guided_strike = scan_monitor.to(guided_strike)
    to_release_monitor = guided_strike.to(release_monitor)
    to_landing_monitor = release_monitor.to(landing_monitor) | emergency.to(landing_monitor)
    to_completed = landing_monitor.to(completed)
    to_override = (
        init.to(override)
        | standby.to(override)
        | scan_monitor.to(override)
        | guided_strike.to(override)
        | release_monitor.to(override)
        | landing_monitor.to(override)
    )
    to_emergency = (
        init.to(emergency)
        | standby.to(emergency)
        | scan_monitor.to(emergency)
        | guided_strike.to(emergency)
        | release_monitor.to(emergency)
        | landing_monitor.to(emergency)
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
        self._background_tasks: set[asyncio.Task[None]] = set()

    @property
    def current_state_name(self) -> str:
        """Current state as a string."""
        current_state = self.current_state
        if isinstance(current_state, State):
            return str(current_state.id)
        return str(next(iter(current_state)).id)

    def create_background_task(self, coro: Any) -> None:
        """Create and retain a background task until completion."""
        task = asyncio.create_task(coro)
        self._background_tasks.add(task)
        task.add_done_callback(self._background_tasks.discard)

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
        transition.target_state.upper()
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
                self._context.connection.relinquish_autonomy(event.reason)
            if self.current_state_name == "override":
                return
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
            current = self._get_current_state_instance()
            if current:
                current.handle(event)
            if self.current_state_name == "emergency":
                return
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
