"""Navigation — waypoint generation and mission item creation."""

from __future__ import annotations

from typing import Any

import structlog

from striker.comms.messages import (
    MAV_CMD_DO_LAND_START,
    MAV_CMD_DO_SET_SERVO,
    MAV_CMD_NAV_LAND,
    MAV_CMD_NAV_TAKEOFF,
    MAV_CMD_NAV_WAYPOINT,
    MAV_FRAME_GLOBAL_RELATIVE_ALT,
)
from striker.config.field_profile import GeoPoint
from striker.flight.mission_geometry import MissionGeometryResult

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


def make_do_set_servo(
    seq: int,
    channel: int,
    pwm: int,
    mav: Any,
) -> Any:
    """Create a DO_SET_SERVO mission item for payload release."""
    return mav.mav.mission_item_int_encode(
        target_system=mav.target_system,
        target_component=mav.target_component,
        seq=seq,
        frame=MAV_FRAME_GLOBAL_RELATIVE_ALT,
        command=MAV_CMD_DO_SET_SERVO,
        current=0,
        autocontinue=1,
        param1=channel,
        param2=pwm,
        param3=0, param4=0,
        x=0, y=0, z=0,
    )


# ── Waypoint generation ──────────────────────────────────────────


def build_waypoint_sequence(
    geometry: MissionGeometryResult,
    landing_items: list[Any],
    mav: Any,
) -> list[Any]:
    """Build complete waypoint sequence from procedural geometry.

    Returns a list of MAVLink mission_item_int messages.
    """
    items: list[Any] = []
    seq = 0

    # ArduPlane replaces mission item 0 with its HOME waypoint.
    items.append(make_nav_waypoint(seq, 0, 0, 0, mav))
    seq += 1

    # Takeoff
    start = geometry.takeoff_start
    climbout = geometry.takeoff_climbout
    items.append(make_nav_takeoff(seq, climbout[2], mav))
    seq += 1
    items.append(make_nav_waypoint(seq, climbout[0], climbout[1], climbout[2], mav))
    seq += 1

    # Scan waypoints
    for lat, lon, alt in geometry.scan_waypoints:
        items.append(make_nav_waypoint(seq, lat, lon, alt, mav))
        seq += 1

    # Landing items — re-sequence to correct seq numbers
    for item in landing_items:
        item.seq = seq
        items.append(item)
        seq += 1

    return items


def build_attack_run_mission(
    approach_lat: float,
    approach_lon: float,
    target_lat: float,
    target_lon: float,
    exit_lat: float,
    exit_lon: float,
    attack_alt_m: float,
    release_channel: int,
    release_pwm: int,
    acceptance_radius_m: float,
    dry_run: bool,
    landing_items: list[Any],
    mav: Any,
) -> tuple[list[Any], int, int]:
    """Build attack run + landing mission sequence.

    Returns (items, target_seq, landing_start_seq).
    """
    items: list[Any] = []
    seq = 0

    # seq 0: dummy HOME (ArduPlane replaces item 0)
    items.append(make_nav_waypoint(seq, 0, 0, 0, mav))
    seq += 1

    # seq 1: approach waypoint
    items.append(make_nav_waypoint(seq, approach_lat, approach_lon, attack_alt_m, mav))
    seq += 1

    # seq 2: target waypoint (with optional acceptance radius)
    items.append(make_nav_waypoint(seq, target_lat, target_lon, attack_alt_m, mav))
    target_seq = seq
    seq += 1

    # seq 3 (optional): DO_SET_SERVO for native release
    if not dry_run:
        items.append(make_do_set_servo(seq, release_channel, release_pwm, mav))
        seq += 1

    # seq 3 or 4: exit waypoint
    items.append(make_nav_waypoint(seq, exit_lat, exit_lon, attack_alt_m, mav))
    seq += 1

    # Landing items — re-sequence to correct seq numbers
    landing_start_seq = seq
    for item in landing_items:
        item.seq = seq
        items.append(item)
        seq += 1

    return items, target_seq, landing_start_seq
