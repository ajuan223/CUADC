"""State registry for the mission state machine."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from striker.core.states.base import BaseState

# Global state name → class registry
_state_registry: dict[str, type[BaseState]] = {}


def register_state(name: str, cls: type[BaseState]) -> None:
    """Register a state class by name."""
    _state_registry[name] = cls


def get_state(name: str) -> type[BaseState]:
    """Look up a registered state class by name."""
    if name not in _state_registry:
        msg = f"State '{name}' not registered. Available: {list(_state_registry)}"
        raise KeyError(msg)
    return _state_registry[name]


def all_states() -> dict[str, type[BaseState]]:
    """Return a copy of the state registry."""
    return dict(_state_registry)


from striker.core.states.attack_run import AttackRunState  # noqa: E402
from striker.core.states.completed import CompletedState  # noqa: E402
from striker.core.states.emergency import EmergencyState  # noqa: E402
from striker.core.states.init import InitState  # noqa: E402
from striker.core.states.landing_monitor import LandingMonitorState  # noqa: E402
from striker.core.states.loiter_hold import LoiterHoldState  # noqa: E402
from striker.core.states.override import OverrideState  # noqa: E402
from striker.core.states.release_monitor import ReleaseMonitorState  # noqa: E402
from striker.core.states.scan_monitor import ScanMonitorState  # noqa: E402
from striker.core.states.standby import StandbyState  # noqa: E402

__all__ = [
    "AttackRunState",
    "CompletedState",
    "EmergencyState",
    "InitState",
    "LandingMonitorState",
    "LoiterHoldState",
    "OverrideState",
    "ReleaseMonitorState",
    "ScanMonitorState",
    "StandbyState",
]
