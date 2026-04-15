"""Payload system — ballistic solver and release controllers."""

from __future__ import annotations

from typing import Any

# Release controller type registry
_release_types: dict[str, type] = {}


def register_release(name: str, cls: type) -> None:
    _release_types[name] = cls


def create_release_controller(method: str, **kwargs: Any) -> Any:
    """Factory: create a release controller by method name."""
    cls = _release_types.get(method)
    if cls is None:
        msg = f"Unknown release method: {method}. Available: {list(_release_types)}"
        raise ValueError(msg)
    return cls(**kwargs)
