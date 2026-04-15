"""Mission events — enums and data classes for FSM transitions."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum, unique


# ── System Events ─────────────────────────────────────────────────


@unique
class SystemEvent(Enum):
    """System-level events."""

    INIT_COMPLETE = "INIT_COMPLETE"
    SHUTDOWN = "SHUTDOWN"


# ── Flight Events ─────────────────────────────────────────────────


@unique
class FlightEvent(Enum):
    """Flight phase events."""

    TAKEOFF_COMPLETE = "TAKEOFF_COMPLETE"
    LANDING_COMPLETE = "LANDING_COMPLETE"
    MISSION_LOADED = "MISSION_LOADED"
    ARM_SUCCESS = "ARM_SUCCESS"


# ── Scan Events ───────────────────────────────────────────────────


@unique
class ScanEvent(Enum):
    """Scan/loiter cycle events."""

    SCAN_COMPLETE = "SCAN_COMPLETE"
    LOITER_TIMEOUT = "LOITER_TIMEOUT"
    TARGET_ACQUIRED = "TARGET_ACQUIRED"


# ── Override / Emergency ──────────────────────────────────────────


@dataclass(frozen=True)
class OverrideEvent:
    """Human override detected — transition to OVERRIDE state."""

    reason: str = "Human took manual control"


@dataclass(frozen=True)
class EmergencyEvent:
    """Safety violation detected — transition to EMERGENCY state."""

    reason: str = "Safety check failed"


# ── Transition ────────────────────────────────────────────────────


@dataclass(frozen=True)
class Transition:
    """State transition directive returned by state handlers."""

    target_state: str
    reason: str = ""
