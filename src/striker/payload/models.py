"""Payload models — data classes for ballistic parameters and release config."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class BallisticParams:
    """Physical parameters for ballistic calculation."""

    gravity: float = 9.81  # m/s^2
    default_altitude_m: float = 100.0


@dataclass(frozen=True)
class ReleaseConfig:
    """Release mechanism configuration."""

    method: str = "mavlink"  # "mavlink" or "gpio"
    channel: int = 6
    pwm_open: int = 2000
    pwm_close: int = 1000
    gpio_pin: int = 17
    gpio_active_high: bool = True
    dry_run: bool = False
