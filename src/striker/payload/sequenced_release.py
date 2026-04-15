"""Sequenced release — reserved interface for multi-drop patterns."""

from __future__ import annotations

import structlog

logger = structlog.get_logger(__name__)


class SequencedRelease:
    """Reserved: interval/pattern-based multi-drop release (stub)."""

    def __init__(self) -> None:
        pass

    async def trigger_sequence(self) -> None:
        logger.warning("SequencedRelease is a stub — not implemented")
