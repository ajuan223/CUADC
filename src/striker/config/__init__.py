"""Striker configuration system — three-layer priority + field profiles."""

from striker.config.platform import Platform, detect_platform
from striker.config.settings import StrikerSettings

__all__ = ["Platform", "StrikerSettings", "detect_platform"]
