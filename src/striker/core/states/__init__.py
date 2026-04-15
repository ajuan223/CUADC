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
