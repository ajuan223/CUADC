"""GCS Reporter — reserved interface for ground control station reporting."""

from __future__ import annotations

from typing import Any, Protocol


class GcsReporter(Protocol):
    """Protocol for ground control station status reporting (reserved)."""

    async def send_status(self, status: dict[str, Any]) -> None:
        """Send a status update to the GCS."""
        ...
