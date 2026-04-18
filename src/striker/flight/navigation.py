"""Navigation — waypoint generation and mission item creation."""

from __future__ import annotations

import math
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
from striker.config.field_profile import GeoPoint, point_in_polygon
from striker.flight.mission_geometry import MissionGeometryResult
from striker.utils.geo import (
    calculate_bearing,
    destination_point,
    haversine_distance,
    nearest_boundary_distance,
)

logger = structlog.get_logger(__name__)

LANDING_ONLY_FINAL_APPROACH_DISTANCE_M = 100.0
LANDING_ONLY_FINAL_APPROACH_MIN_BOUNDARY_MARGIN_M = 10.0


# ── Mission item creation helpers ─────────────────────────────────


def make_nav_waypoint(
    seq: int,
    lat: float,
    lon: float,
    alt_m: float,
    mav: Any,
    acceptance_radius_m: float = 0.0,
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
        param2=acceptance_radius_m,  # acceptance radius
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
    heading_deg: float = 0.0,
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
        param2=0, param3=0,
        param4=heading_deg,
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
    climbout = geometry.takeoff_climbout
    start = geometry.takeoff_start
    lat1r = math.radians(start[0])
    lat2r = math.radians(climbout[0])
    dlon = math.radians(climbout[1] - start[1])
    takeoff_heading = math.degrees(math.atan2(
        math.sin(dlon) * math.cos(lat2r),
        math.cos(lat1r) * math.sin(lat2r)
        - math.sin(lat1r) * math.cos(lat2r) * math.cos(dlon),
    )) % 360
    items.append(make_nav_takeoff(seq, climbout[2], mav, heading_deg=takeoff_heading))
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
    items.append(make_nav_waypoint(
        seq,
        target_lat,
        target_lon,
        attack_alt_m,
        mav,
        acceptance_radius_m=acceptance_radius_m,
    ))
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


def _build_landing_only_final_approach(
    geometry: MissionGeometryResult,
    boundary_polygon: list[GeoPoint],
) -> tuple[float, float, float] | None:
    """Derive a bounded final-approach gate between approach and touchdown."""
    if not boundary_polygon:
        return None

    approach_lat, approach_lon, approach_alt = geometry.landing_approach
    touchdown_lat, touchdown_lon, touchdown_alt = geometry.landing_touchdown
    approach_heading = calculate_bearing(approach_lat, approach_lon, touchdown_lat, touchdown_lon)
    approach_to_touchdown_m = haversine_distance(
        approach_lat,
        approach_lon,
        touchdown_lat,
        touchdown_lon,
    )
    if approach_to_touchdown_m <= LANDING_ONLY_FINAL_APPROACH_DISTANCE_M:
        return None

    candidate_lat, candidate_lon = destination_point(
        approach_lat,
        approach_lon,
        approach_heading,
        LANDING_ONLY_FINAL_APPROACH_DISTANCE_M,
    )
    if not point_in_polygon(candidate_lat, candidate_lon, boundary_polygon):
        return None
    boundary_margin_m = nearest_boundary_distance(candidate_lat, candidate_lon, boundary_polygon)
    if boundary_margin_m < LANDING_ONLY_FINAL_APPROACH_MIN_BOUNDARY_MARGIN_M:
        return None

    glide_fraction = LANDING_ONLY_FINAL_APPROACH_DISTANCE_M / approach_to_touchdown_m
    candidate_alt = approach_alt + (touchdown_alt - approach_alt) * glide_fraction
    return candidate_lat, candidate_lon, candidate_alt


def build_landing_only_mission(
    geometry: MissionGeometryResult,
    boundary_polygon: list[GeoPoint],
    landing_items: list[Any],
    mav: Any,
) -> tuple[list[Any], int]:
    """Build a landing-only AUTO mission with a fresh HOME item.

    Returns (items, landing_activation_seq).
    """
    items: list[Any] = []
    seq = 0

    items.append(make_nav_waypoint(seq, 0, 0, 0, mav))
    seq += 1

    final_approach = _build_landing_only_final_approach(geometry, boundary_polygon)

    landing_activation_seq: int | None = None
    for item in landing_items:
        item.seq = seq
        items.append(item)
        if (
            landing_activation_seq is None
            and getattr(item, "command", None) == MAV_CMD_NAV_WAYPOINT
        ):
            landing_activation_seq = seq
        seq += 1
        if (
            final_approach is not None
            and getattr(item, "command", None) == MAV_CMD_NAV_WAYPOINT
        ):
            final_approach_lat, final_approach_lon, final_approach_alt = final_approach
            landing_activation_seq = seq
            items.append(
                make_nav_waypoint(
                    seq,
                    final_approach_lat,
                    final_approach_lon,
                    final_approach_alt,
                    mav,
                )
            )
            seq += 1
            logger.info(
                "Landing-only final-approach gate added",
                lat=final_approach_lat,
                lon=final_approach_lon,
                alt_m=final_approach_alt,
                distance_from_approach_m=LANDING_ONLY_FINAL_APPROACH_DISTANCE_M,
                landing_activation_seq=landing_activation_seq,
            )
            final_approach = None

    if final_approach is not None:
        logger.info("Landing-only final-approach gate unavailable; using base landing sequence")

    if landing_activation_seq is None:
        landing_activation_seq = 1

    return items, landing_activation_seq
