"""Shared memory receiver — reserved interface for SHM-based target input."""

from __future__ import annotations

import structlog

logger = structlog.get_logger(__name__)


class SharedMemReceiver:
    """Reserved: read targets from shared memory (stub implementation)."""

    def __init__(self, shm_name: str = "striker_vision") -> None:
        self._shm_name = shm_name
        self._latest = None

    async def start(self) -> None:
        logger.warning("SharedMemReceiver is a stub — not implemented")

    async def stop(self) -> None:
        pass

    def get_latest(self) -> object:
        return self._latest
