"""Platform detection — identify the runtime hardware / simulation environment."""

import enum
import os
from pathlib import Path


class Platform(enum.Enum):
    """Known runtime platforms."""

    RPi5 = "rpi5"
    Orin = "orin"
    SITL = "sitl"
    Unknown = "unknown"


def detect_platform() -> Platform:
    """Return the detected runtime platform.

    Detection order (first match wins):
    1. ``STRIKER_PLATFORM`` env var (manual override)
    2. ``MAVLINK_SITL`` env var (ArduPlane SITL)
    3. ``/proc/device-tree/model`` contains ``Raspberry Pi 5``
    4. ``/etc/nv_tegra_release`` exists (NVIDIA Orin)
    5. Fallback: ``Platform.Unknown``
    """
    # 1. Manual override
    override = os.environ.get("STRIKER_PLATFORM", "").lower()
    if override:
        mapping = {
            "rpi5": Platform.RPi5,
            "orin": Platform.Orin,
            "sitl": Platform.SITL,
            "unknown": Platform.Unknown,
        }
        return mapping.get(override, Platform.Unknown)

    # 2. SITL environment
    if "MAVLINK_SITL" in os.environ:
        return Platform.SITL

    # 3. Raspberry Pi 5
    try:
        model = Path("/proc/device-tree/model").read_text(encoding="utf-8").rstrip("\x00")
        if "Raspberry Pi 5" in model:
            return Platform.RPi5
    except (FileNotFoundError, PermissionError):
        pass

    # 4. NVIDIA Orin
    if Path("/etc/nv_tegra_release").exists():
        return Platform.Orin

    return Platform.Unknown
