"""Vision receiver package — external solver coordinate reception."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from striker.vision.protocol import VisionReceiver


# Receiver type registry
_receiver_types: dict[str, type] = {}


def register_receiver(name: str, cls: type) -> None:
    _receiver_types[name] = cls


def create_vision_receiver(receiver_type: str, **kwargs: object) -> "VisionReceiver":
    """Factory: create a vision receiver by type name."""
    cls = _receiver_types.get(receiver_type)
    if cls is None:
        msg = f"Unknown receiver type: {receiver_type}. Available: {list(_receiver_types)}"
        raise ValueError(msg)
    return cls(**kwargs)  # type: ignore[no-any-return]
