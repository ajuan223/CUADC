"""Striker global exception hierarchy.

All Striker-specific exceptions inherit from :class:`StrikerError`,
enabling callers to catch every domain error with a single handler.
"""


class StrikerError(Exception):
    """Root exception for all Striker subsystems."""


# ── Configuration ────────────────────────────────────────────────
class ConfigError(StrikerError):
    """Raised when configuration loading, parsing, or validation fails."""


# ── Communications ───────────────────────────────────────────────
class CommsError(StrikerError):
    """Raised on MAVLink connection, heartbeat, or message errors."""


# ── Flight Control ───────────────────────────────────────────────
class FlightError(StrikerError):
    """Raised when a flight command (arm, takeoff, goto, mode change) fails."""


# ── Safety ───────────────────────────────────────────────────────
class SafetyError(StrikerError):
    """Raised when a safety constraint is violated (geofence, battery, etc.)."""


# ── Payload ──────────────────────────────────────────────────────
class PayloadError(StrikerError):
    """Raised when the payload release or ballistic subsystem encounters an error."""
