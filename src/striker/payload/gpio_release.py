"""GPIO release controller — direct GPIO pin drive via gpiod."""

from __future__ import annotations

import structlog

from striker.payload import register_release
from striker.payload.models import ReleaseConfig

logger = structlog.get_logger(__name__)


class GpioRelease:
    """GPIO-based release controller.

    Uses gpiod for direct GPIO pin control.
    Handles gpiod import gracefully on non-GPIO platforms.

    Parameters
    ----------
    config:
        Release mechanism configuration.
    """

    def __init__(self, config: ReleaseConfig) -> None:
        self._config = config
        self._armed = False
        self._released = False
        self._line = None
        self._gpiod = None

        try:
            import gpiod

            self._gpiod = gpiod
            chip = gpiod.Chip("gpiochip0")
            self._line = chip.get_line(config.gpio_pin)
            self._line.request(consumer="striker-release", type=gpiod.LINE_REQ_DIR_OUT)
        except Exception:
            logger.warning("GPIO not available — running in simulation mode")

    @property
    def is_armed(self) -> bool:
        return self._armed

    @property
    def is_released(self) -> bool:
        return self._released

    async def arm(self) -> None:
        """Arm the release (set pin to inactive state)."""
        if self._config.dry_run:
            logger.info("DRY_RUN: Would arm GPIO release")
            self._armed = True
            return

        inactive = 0 if self._config.gpio_active_high else 1
        if self._line:
            self._line.set_value(inactive)
        self._armed = True
        logger.info("GPIO release armed", pin=self._config.gpio_pin)

    async def release(self) -> bool:
        """Trigger release by toggling GPIO pin."""
        if self._config.dry_run:
            logger.info("DRY_RUN: Would trigger GPIO release")
            self._released = True
            return True

        active = 1 if self._config.gpio_active_high else 0
        if self._line:
            self._line.set_value(active)
        self._released = True
        logger.info("GPIO release triggered", pin=self._config.gpio_pin)
        return True


register_release("gpio", GpioRelease)
