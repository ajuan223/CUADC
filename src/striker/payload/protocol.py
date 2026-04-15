"""Release controller protocol — interface for release mechanisms."""

from __future__ import annotations

from typing import Protocol


class ReleaseController(Protocol):
    """Protocol for payload release mechanisms."""

    async def arm(self) -> None:
        """Prepare the release mechanism."""
        ...

    async def release(self) -> bool:
        """Trigger the release. Returns True on success."""
        ...

    @property
    def is_armed(self) -> bool:
        """Whether the release mechanism is armed."""
        ...

    @property
    def is_released(self) -> bool:
        """Whether the payload has been released."""
        ...
