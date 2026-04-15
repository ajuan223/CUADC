"""Striker global exception hierarchy.

All Striker-specific exceptions inherit from :class:`StrikerError`,
enabling callers to catch every domain error with a single handler.
"""


class StrikerError(Exception):
    """Root exception for all Striker subsystems."""


# ── Configuration ────────────────────────────────────────────────
class ConfigError(StrikerError):
    """Raised when configuration loading, parsing, or validation fails."""


class FieldValidationError(StrikerError):
    """Raised when field profile validation fails (waypoints outside fence, etc.)."""

    def __init__(self, field_name: str, reason: str) -> None:
        self.field_name = field_name
        self.reason = reason
        super().__init__(f"Field validation failed [{field_name}]: {reason}")


# ── Communications ───────────────────────────────────────────────
class CommsError(StrikerError):
    """Raised on MAVLink connection, heartbeat, or message errors."""


class MavlinkConnectionError(CommsError):
    """Raised when MAVLink connection establishment fails."""


class HeartbeatTimeoutError(CommsError):
    """Raised when heartbeat watchdog detects connection loss."""


class MessageTimeoutError(CommsError):
    """Raised when waiting for a MAVLink message times out."""


class MissionUploadError(CommsError):
    """Raised during MAVLink Mission Upload Protocol failure."""


# ── Flight Control ───────────────────────────────────────────────
class FlightError(StrikerError):
    """Raised when a flight command (arm, takeoff, goto, mode change) fails."""


# ── Safety ───────────────────────────────────────────────────────
class SafetyError(StrikerError):
    """Raised when a safety constraint is violated (geofence, battery, etc.)."""


# ── Payload ──────────────────────────────────────────────────────
class PayloadError(StrikerError):
    """Raised when the payload release or ballistic subsystem encounters an error."""
