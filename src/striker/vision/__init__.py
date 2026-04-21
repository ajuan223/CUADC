"""Vision receiver package — external solver coordinate reception."""

from __future__ import annotations

from striker.vision.global_var import get_vision_drop_point, set_vision_drop_point
from striker.vision.models import GpsDropPoint, validate_gps

__all__ = [
    "GpsDropPoint",
    "get_vision_drop_point",
    "set_vision_drop_point",
    "validate_gps",
]
