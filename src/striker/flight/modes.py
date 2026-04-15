"""ArduPlane flight modes — enum with MAVLink mode ID mapping."""

from __future__ import annotations

from enum import Enum, unique


@unique
class ArduPlaneMode(Enum):
    """ArduPlane flight mode mapping to MAVLink mode IDs."""

    MANUAL = 0
    CIRCLE = 1
    STABILIZE = 2
    TRAINING = 3
    ACRO = 4
    FBWA = 5
    FBWB = 6
    CRUISE = 7
    AUTOTUNE = 8
    AUTO = 10
    RTL = 11
    LOITER = 12
    GUIDED = 15
    INITIALISING = 16
    QSTABILIZE = 17
    QHOVER = 18
    QLOITER = 19
    QLAND = 20
    QRTL = 21

    @classmethod
    def from_name(cls, name: str) -> "ArduPlaneMode":
        """Look up mode by name (case-insensitive)."""
        return cls[name.upper()]

    @property
    def mode_id(self) -> int:
        """MAVLink mode ID value."""
        return self.value
