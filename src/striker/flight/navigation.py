"""Navigation — waypoint generation and mission item creation."""

from __future__ import annotations

from typing import Any

import structlog

from striker.comms.messages import (
    MAV_CMD_DO_LAND_START,
    MAV_CMD_NAV_LAND,
    MAV_CMD_NAV_TAKEOFF,
    MAV_CMD_NAV_WAYPOINT,
    MAV_FRAME_GLOBAL_RELATIVE_ALT,
)
from striker.config.field_profile import GeoPoint

logger = structlog.get_logger(__name__)


# ── Mission item creation helpers ─────────────────────────────────


def make_nav_waypoint(
    seq: int,
    lat: float,
    lon: float,
    alt_m: float,
    mav: Any,
) -> Any:
    """Create a NAV_WAYPOINT mission item."""
    return mav.mav.mission_item_int_encode(
        target_system=mav.target_system,
        target_component=mav.target_component,
        seq=seq,
        frame=MAV_FRAME_GLOBAL_RELATIVE_ALT,
        command=MAV_CMD_NAV_WAYPOINT,
        current=0,
        autocontinue=1,
        param1=0,  # hold time
        param2=0,  # acceptance radius
        param3=0,  # pass radius
        param4=0,  # yaw
        x=int(lat * 1e7),
        y=int(lon * 1e7),
        z=alt_m,
    )


def make_nav_takeoff(
    seq: int,
    alt_m: float,
    mav: Any,
    pitch_deg: float = 12.0,
) -> Any:
    """Create a NAV_TAKEOFF mission item."""
    return mav.mav.mission_item_int_encode(
        target_system=mav.target_system,
        target_component=mav.target_component,
        seq=seq,
        frame=MAV_FRAME_GLOBAL_RELATIVE_ALT,
        command=MAV_CMD_NAV_TAKEOFF,
        current=0,
        autocontinue=1,
        param1=pitch_deg,
        param2=0, param3=0, param4=0,
        x=0, y=0, z=alt_m,
    )


def make_do_land_start(
    seq: int,
    mav: Any,
) -> Any:
    """Create a DO_LAND_START mission item."""
    return mav.mav.mission_item_int_encode(
        target_system=mav.target_system,
        target_component=mav.target_component,
        seq=seq,
        frame=MAV_FRAME_GLOBAL_RELATIVE_ALT,
        command=MAV_CMD_DO_LAND_START,
        current=0,
        autocontinue=1,
        param1=0, param2=0, param3=0, param4=0,
        x=0, y=0, z=0,
    )


def make_nav_land(
    seq: int,
    lat: float,
    lon: float,
    alt_m: float,
    mav: Any,
) -> Any:
    """Create a NAV_LAND mission item."""
    return mav.mav.mission_item_int_encode(
        target_system=mav.target_system,
        target_component=mav.target_component,
        seq=seq,
        frame=MAV_FRAME_GLOBAL_RELATIVE_ALT,
        command=MAV_CMD_NAV_LAND,
        current=0,
        autocontinue=1,
        param1=0,  # abort alt
        param2=0,  # land mode
        param3=0, param4=0,
        x=int(lat * 1e7),
        y=int(lon * 1e7),
        z=alt_m,
    )


# ── Waypoint generation ──────────────────────────────────────────


def generate_scan_waypoints(field_profile: Any) -> list[GeoPoint]:
    """Generate scan waypoints from field profile scan_waypoints config."""
    return field_profile.scan_waypoints.waypoints


def build_waypoint_sequence(
    scan_waypoints: list[GeoPoint],
    scan_alt_m: float,
    landing_items: list[Any],
    mav: Any,
    include_takeoff: bool = False,
) -> list[Any]:
    """Build complete waypoint sequence: scan waypoints + landing items.

    Returns a list of MAVLink mission_item_int messages.
    """
    items: list[Any] = []
    seq = 0

    if include_takeoff:
        # ArduPlane replaces mission item 0 with its HOME waypoint.
        # Prepend a dummy waypoint at seq=0 so our TAKEOFF survives at seq=1.
        items.append(make_nav_waypoint(seq, 0, 0, 0, mav))
        seq += 1
        items.append(make_nav_takeoff(seq, scan_alt_m, mav))
        seq += 1

    # Scan waypoints
    for wp in scan_waypoints:
        items.append(make_nav_waypoint(seq, wp.lat, wp.lon, scan_alt_m, mav))
        seq += 1

    # Landing items
    for item in landing_items:
        items.append(item)
        seq += 1

    return items
