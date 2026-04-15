"""VisionReceiver protocol — interface for coordinate receivers."""

from __future__ import annotations

from typing import Protocol

from striker.vision.models import GpsTarget


class VisionReceiver(Protocol):
    """Protocol for vision coordinate receivers."""

    async def start(self) -> None:
        """Start the receiver."""
        ...

    async def stop(self) -> None:
        """Stop the receiver."""
        ...

    def get_latest(self) -> GpsTarget | None:
        """Return the most recently received target, or None."""
        ...
