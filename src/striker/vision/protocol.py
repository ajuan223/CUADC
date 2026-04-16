"""VisionReceiver protocol — interface for drop point receivers."""

from __future__ import annotations

from typing import Protocol

from striker.vision.models import GpsDropPoint


class VisionReceiver(Protocol):
    """Protocol for vision drop point receivers."""

    async def start(self) -> None:
        """Start the receiver."""
        ...

    async def stop(self) -> None:
        """Stop the receiver."""
        ...

    def get_latest(self) -> GpsDropPoint | None:
        """Return the most recently received drop point, or None."""
        ...
