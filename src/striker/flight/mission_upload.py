"""Mission Upload Protocol — MAVLink waypoint upload implementation."""

from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING, Any

import structlog

from striker.comms.messages import (
    MAV_RESULT_ACCEPTED,
    MISSION_ACK,
    MISSION_REQUEST,
    MISSION_REQUEST_INT,
)
from striker.exceptions import MissionUploadError

if TYPE_CHECKING:
    from striker.comms.connection import MAVLinkConnection
    from striker.config.field_profile import FieldProfile

logger = structlog.get_logger(__name__)

# Timeout per protocol step
_STEP_TIMEOUT = 5.0


async def _recv_mission_request(conn: MAVLinkConnection, timeout: float) -> object:
    """Wait for either MISSION_REQUEST_INT or legacy MISSION_REQUEST."""
    return await conn.recv_match_any([MISSION_REQUEST_INT, MISSION_REQUEST], timeout=timeout)


async def upload_mission(conn: MAVLinkConnection, items: list[Any]) -> None:
    """Execute full MAVLink Mission Upload Protocol.

    Steps:
    1. MISSION_CLEAR_ALL + ACK verification
    2. MISSION_COUNT with item count
    3. Respond to MISSION_REQUEST_INT or MISSION_REQUEST per item by index
    4. Final MISSION_ACK verification (type == ACCEPTED)

    Parameters
    ----------
    conn:
        Active MAVLinkConnection.
    items:
        List of MAVLink mission item messages.

    Raises
    ------
    MissionUploadError
        If any protocol step fails or times out.
    """
    mav = conn.mav
    count = len(items)

    # Step 1: Clear all missions.
    # NOTE: MAVProxy may return MISSION_ACK type=1 (UNSUPPORTED) for
    # MISSION_CLEAR_ALL, but ArduPlane still processes it.  We drain
    # the ACK without checking its result to avoid false failures.
    logger.info("Mission upload: clearing all", count=count)
    mav.mav.mission_clear_all_send(mav.target_system, mav.target_component, 0)
    try:
        await conn.recv_match(MISSION_ACK, timeout=2.0)
    except TimeoutError:
        pass  # No ACK is fine — some setups don't respond

    # Step 2: Send count
    logger.info("Mission upload: sending count", count=count)
    mav.mav.mission_count_send(mav.target_system, mav.target_component, count)

    # Step 3: Respond to MISSION_REQUEST_INT / MISSION_REQUEST for each item
    for i in range(count):
        try:
            req = await _recv_mission_request(conn, timeout=_STEP_TIMEOUT)
            if req.seq != i:
                logger.warning("Unexpected request sequence", expected=i, got=req.seq)
            mav.mav.send(items[i])
            logger.debug("Sent mission item", seq=i, request_type=req.get_type())
        except TimeoutError:
            raise MissionUploadError(f"Timeout waiting for mission request seq={i}") from None

    # Step 4: Final ACK
    try:
        final_ack = await conn.recv_match(MISSION_ACK, timeout=_STEP_TIMEOUT)
        if final_ack.type != MAV_RESULT_ACCEPTED:
            raise MissionUploadError(f"Final MISSION_ACK rejected: type={final_ack.type}")
    except TimeoutError:
        raise MissionUploadError("Timeout waiting for final MISSION_ACK") from None

    logger.info("Mission upload complete", count=count)


async def upload_full_mission(conn: MAVLinkConnection, field_profile: FieldProfile) -> int:
    """Upload the full fixed-wing mission and return landing start index."""
    from striker.flight.landing_sequence import generate_landing_sequence
    from striker.flight.navigation import build_waypoint_sequence, generate_scan_waypoints

    waypoints = generate_scan_waypoints(field_profile)
    landing_start_index = 1 + len(waypoints)
    landing_items = generate_landing_sequence(
        field_profile,
        conn.mav,
        start_seq=landing_start_index,
    )
    items = build_waypoint_sequence(
        waypoints,
        field_profile.scan_waypoints.altitude_m,
        landing_items,
        conn.mav,
        include_takeoff=True,
    )
    await upload_mission(conn, items)
    return landing_start_index


async def upload_scan_waypoints(conn: MAVLinkConnection, field_profile: FieldProfile) -> None:
    """Upload scan waypoints from field profile."""
    from striker.flight.navigation import build_waypoint_sequence, generate_scan_waypoints

    waypoints = generate_scan_waypoints(field_profile)
    # Build mission items without landing items for scan upload
    items = build_waypoint_sequence(waypoints, field_profile.scan_waypoints.altitude_m, [], conn.mav)
    await upload_mission(conn, items)


async def upload_landing_sequence(conn: MAVLinkConnection, field_profile: FieldProfile) -> None:
    """Upload landing sequence from field profile."""
    from striker.flight.landing_sequence import generate_landing_sequence

    items = generate_landing_sequence(field_profile, conn.mav)
    await upload_mission(conn, items)
