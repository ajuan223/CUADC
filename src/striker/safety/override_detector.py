"""Override detector — monitors FC mode changes for human takeover."""

from __future__ import annotations

from collections.abc import Callable

import structlog

from striker.core.events import OverrideEvent

logger = structlog.get_logger(__name__)


class OverrideDetector:
    """Detects manual mode switch indicating human override.

    Monitors the current flight controller mode and emits an OverrideEvent
    when the mode changes to one of the configured override modes.

    Parameters
    ----------
    override_modes:
        Set of mode names that indicate human override (default: MANUAL, STABILIZE).
    """

    def __init__(
        self,
        override_modes: set[str] | None = None,
        on_override: Callable[[OverrideEvent], None] | None = None,
    ) -> None:
        self._override_modes = override_modes or {"MANUAL", "STABILIZE", "FBWA"}
        self._on_override = on_override
        self._last_mode: str = ""

    def check_mode(self, current_mode: str) -> OverrideEvent | None:
        """Check if the current mode indicates a human override.

        Returns
        -------
        OverrideEvent or None
            OverrideEvent if override detected, None otherwise.
        """
        if not self._last_mode:
            self._last_mode = current_mode
            return None

        if current_mode != self._last_mode:
            logger.info("Mode changed", old=self._last_mode, new=current_mode)
            self._last_mode = current_mode

            if current_mode.upper() in {m.upper() for m in self._override_modes}:
                event = OverrideEvent(reason=f"Mode switched to {current_mode}")
                if self._on_override:
                    self._on_override(event)
                return event

        return None
