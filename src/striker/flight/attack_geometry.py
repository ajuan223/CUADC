"""Simplified attack geometry computation for preburned slot overwrite."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from striker.comms.messages import MAV_CMD_DO_SET_SERVO, MAV_CMD_NAV_WAYPOINT
from striker.utils.geo import destination_point

if TYPE_CHECKING:
    pass

def compute_attack_slots(
    drop_lat: float,
    drop_lon: float,
    approach_heading_deg: float,
    approach_distance_m: float,
    exit_distance_m: float,
    attack_alt_m: float,
    release_channel: int,
    release_pwm: int,
    mav: Any,
) -> list[Any]:
    """Compute approach and exit waypoints and return 5 slot mission items.

    Slots:
    0: approach NAV_WP
    1: target NAV_WP
    2: release DO_SET_SERVO
    3: exit NAV_WP
    4: spare NAV_WP (same as exit)
    """
    # Approach point is behind target
    approach_lat, approach_lon = destination_point(
        drop_lat, drop_lon, (approach_heading_deg + 180) % 360, approach_distance_m
    )
    # Exit point is ahead of target
    exit_lat, exit_lon = destination_point(
        drop_lat, drop_lon, approach_heading_deg, exit_distance_m
    )

    items = []

    # Slot 0: Approach
    items.append(mav.mavlink.MAVLink_mission_item_int_message(
        mav.target_system, mav.target_component,
        0, 3, MAV_CMD_NAV_WAYPOINT, 0, 1,
        0, 0, 0, 0,
        int(approach_lat * 1e7), int(approach_lon * 1e7), attack_alt_m
    ))

    # Slot 1: Target
    items.append(mav.mavlink.MAVLink_mission_item_int_message(
        mav.target_system, mav.target_component,
        0, 3, MAV_CMD_NAV_WAYPOINT, 0, 1,
        0, 0, 0, 0,
        int(drop_lat * 1e7), int(drop_lon * 1e7), attack_alt_m
    ))

    # Slot 2: Servo
    items.append(mav.mavlink.MAVLink_mission_item_int_message(
        mav.target_system, mav.target_component,
        0, 3, MAV_CMD_DO_SET_SERVO, 0, 1,
        release_channel, release_pwm, 0, 0,
        0, 0, 0
    ))

    # Slot 3: Exit
    items.append(mav.mavlink.MAVLink_mission_item_int_message(
        mav.target_system, mav.target_component,
        0, 3, MAV_CMD_NAV_WAYPOINT, 0, 1,
        0, 0, 0, 0,
        int(exit_lat * 1e7), int(exit_lon * 1e7), attack_alt_m
    ))

    # Slot 4: Spare (copy of exit for safety)
    items.append(mav.mavlink.MAVLink_mission_item_int_message(
        mav.target_system, mav.target_component,
        0, 3, MAV_CMD_NAV_WAYPOINT, 0, 1,
        0, 0, 0, 0,
        int(exit_lat * 1e7), int(exit_lon * 1e7), attack_alt_m
    ))

    return items
