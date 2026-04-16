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
    from striker.flight.mission_geometry import MissionGeometryResult

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
    logger.info("Mission upload: clearing all", count=count)
    mav.mav.mission_clear_all_send(mav.target_system, mav.target_component, 0)
    try:
        await conn.recv_match(MISSION_ACK, timeout=2.0)
    except TimeoutError:
        pass

    # Step 2: Send count
    logger.info("Mission upload: sending count", count=count)
    mav.mav.mission_count_send(mav.target_system, mav.target_component, count)

    # Step 3: Respond to MISSION_REQUEST_INT / MISSION_REQUEST for each item.
    sent_count = 0
    while sent_count < count:
        try:
            req = await _recv_mission_request(conn, timeout=_STEP_TIMEOUT)
            req_seq = req.seq
            if req_seq >= count:
                raise MissionUploadError(f"Request seq={req_seq} out of range (count={count})")
            if req_seq != sent_count:
                logger.warning("SITL re-requested item", requested_seq=req_seq, expected_seq=sent_count)
            mav.mav.send(items[req_seq])
            logger.debug("Sent mission item", seq=req_seq, request_type=req.get_type())
            if req_seq >= sent_count:
                sent_count = req_seq + 1
        except TimeoutError:
            raise MissionUploadError(f"Timeout waiting for mission request (sent={sent_count}/{count})") from None

    # Step 4: Final ACK
    try:
        final_ack = await conn.recv_match(MISSION_ACK, timeout=_STEP_TIMEOUT)
        if final_ack.type != MAV_RESULT_ACCEPTED:
            raise MissionUploadError(f"Final MISSION_ACK rejected: type={final_ack.type}")
    except TimeoutError:
        raise MissionUploadError("Timeout waiting for final MISSION_ACK") from None

    logger.info("Mission upload complete", count=count)


async def upload_full_mission(
    conn: MAVLinkConnection,
    geometry: MissionGeometryResult,
) -> int:
    """Upload the full fixed-wing mission and return landing start index."""
    from striker.flight.landing_sequence import generate_landing_sequence
    from striker.flight.navigation import build_waypoint_sequence

    landing_items = generate_landing_sequence(geometry, conn.mav, start_seq=0)
    # Landing items will be re-sequenced by build_waypoint_sequence
    items = build_waypoint_sequence(geometry, landing_items, conn.mav)

    # Recompute indices based on actual mission items
    geometry.compute_indices()

    await upload_mission(conn, items)
    return geometry.landing_start_seq


async def upload_attack_mission(
    conn: MAVLinkConnection,
    field_profile: FieldProfile,
    geometry: MissionGeometryResult,
    context: Any,
    target_lat: float,
    target_lon: float,
    approach_lat: float,
    approach_lon: float,
    exit_lat: float,
    exit_lon: float,
    dry_run: bool,
    release_channel: int,
    release_pwm: int,
) -> tuple[int, int]:
    """Upload attack run + landing mission and return (target_seq, landing_start_seq).

    Updates context.landing_sequence_start_index.
    """
    from striker.flight.landing_sequence import generate_landing_sequence
    from striker.flight.navigation import build_attack_run_mission

    attack_alt = field_profile.scan.altitude_m
    landing_items = generate_landing_sequence(geometry, conn.mav, start_seq=0)

    items, target_seq, landing_start_seq = build_attack_run_mission(
        approach_lat=approach_lat,
        approach_lon=approach_lon,
        target_lat=target_lat,
        target_lon=target_lon,
        exit_lat=exit_lat,
        exit_lon=exit_lon,
        attack_alt_m=attack_alt,
        release_channel=release_channel,
        release_pwm=release_pwm,
        acceptance_radius_m=field_profile.attack_run.release_acceptance_radius_m,
        dry_run=dry_run,
        landing_items=landing_items,
        mav=conn.mav,
    )

    await upload_mission(conn, items)
    context.landing_sequence_start_index = landing_start_seq

    logger.info(
        "Attack mission uploaded",
        target_seq=target_seq,
        landing_start_seq=landing_start_seq,
        dry_run=dry_run,
    )
    return target_seq, landing_start_seq
