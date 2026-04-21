"""Mission Upload Protocol — MAVLink waypoint upload implementation."""

from __future__ import annotations

from contextlib import suppress
from typing import TYPE_CHECKING, Any, Protocol, cast

import structlog

from striker.comms.messages import (
    MAV_RESULT_ACCEPTED,
    MISSION_ACK,
    MISSION_COUNT,
    MISSION_REQUEST,
    MISSION_REQUEST_INT,
)
from striker.exceptions import MissionDownloadError, MissionUploadError

if TYPE_CHECKING:
    from striker.comms.connection import MAVLinkConnection

logger = structlog.get_logger(__name__)

# Timeout per protocol step
_STEP_TIMEOUT = 5.0


class _MissionRequestLike(Protocol):
    seq: int

    def get_type(self) -> str: ...


class _MissionAckLike(Protocol):
    type: int


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
    conn.ensure_autonomy_allowed()
    mav = conn.mav
    count = len(items)

    # Step 1: Clear all missions.
    logger.info("Mission upload: clearing all", count=count)
    conn.mission_clear_all_send(mav.target_system, mav.target_component, 0)
    with suppress(TimeoutError):
        await conn.recv_match(MISSION_ACK, timeout=2.0)

    # Step 2: Send count
    logger.info("Mission upload: sending count", count=count)
    conn.mission_count_send(mav.target_system, mav.target_component, count)

    # Step 3: Respond to MISSION_REQUEST_INT / MISSION_REQUEST for each item.
    sent_count = 0
    while sent_count < count:
        try:
            req = cast(_MissionRequestLike, await _recv_mission_request(conn, timeout=_STEP_TIMEOUT))
            req_seq = req.seq
            if req_seq >= count:
                raise MissionUploadError(f"Request seq={req_seq} out of range (count={count})")
            if req_seq != sent_count:
                logger.warning("SITL re-requested item", requested_seq=req_seq, expected_seq=sent_count)
            conn.send_mission_item(items[req_seq])
            logger.debug("Sent mission item", seq=req_seq, request_type=req.get_type())
            if req_seq >= sent_count:
                sent_count = req_seq + 1
        except TimeoutError:
            raise MissionUploadError(f"Timeout waiting for mission request (sent={sent_count}/{count})") from None

    # Step 4: Final ACK
    try:
        final_ack = cast(_MissionAckLike, await conn.recv_match(MISSION_ACK, timeout=_STEP_TIMEOUT))
        if final_ack.type != MAV_RESULT_ACCEPTED:
            raise MissionUploadError(f"Final MISSION_ACK rejected: type={final_ack.type}")
    except TimeoutError:
        raise MissionUploadError("Timeout waiting for final MISSION_ACK") from None

    logger.info("Mission upload complete", count=count)


async def partial_write_mission(
    conn: MAVLinkConnection,
    start_seq: int,
    end_seq: int,
    items: list[Any],
) -> None:
    """Execute MAVLink MISSION_WRITE_PARTIAL_LIST protocol.

    Overwrites mission items from start_seq to end_seq (inclusive).
    The number of items must match (end_seq - start_seq + 1).
    """
    conn.ensure_autonomy_allowed()
    mav = conn.mav
    count = len(items)
    expected_count = end_seq - start_seq + 1
    if count != expected_count:
        raise ValueError(f"Items count {count} does not match seq range [{start_seq}, {end_seq}]")

    logger.info("Mission partial write", start_seq=start_seq, end_seq=end_seq, count=count)

    # Step 1: Send MISSION_WRITE_PARTIAL_LIST
    conn.mav.mav.mission_write_partial_list_send(
        mav.target_system,
        mav.target_component,
        start_seq,
        end_seq,
    )

    # Step 2: Respond to MISSION_REQUEST_INT / MISSION_REQUEST
    sent_count = 0
    while sent_count < count:
        try:
            req = cast(_MissionRequestLike, await _recv_mission_request(conn, timeout=_STEP_TIMEOUT))
            req_seq = req.seq

            if not (start_seq <= req_seq <= end_seq):
                raise MissionUploadError(f"Request seq={req_seq} outside partial range [{start_seq}, {end_seq}]")

            item_index = req_seq - start_seq
            conn.send_mission_item(items[item_index])
            logger.debug("Sent partial mission item", seq=req_seq, request_type=req.get_type())

            if req_seq >= start_seq + sent_count:
                sent_count = item_index + 1
        except TimeoutError:
            raise MissionUploadError(f"Timeout waiting for mission request (sent={sent_count}/{count})") from None

    # Step 3: Final ACK
    try:
        final_ack = cast(_MissionAckLike, await conn.recv_match(MISSION_ACK, timeout=_STEP_TIMEOUT))
        if final_ack.type != MAV_RESULT_ACCEPTED:
            raise MissionUploadError(f"Final MISSION_ACK rejected: type={final_ack.type}")
    except TimeoutError:
        raise MissionUploadError("Timeout waiting for final MISSION_ACK in partial write") from None

    logger.info("Mission partial write complete")


async def download_mission(conn: MAVLinkConnection) -> list[Any]:
    """Execute MAVLink Mission Download Protocol.

    Steps:
    1. MISSION_REQUEST_LIST
    2. Wait for MISSION_COUNT
    3. Send MISSION_REQUEST_INT for each seq 0 to count-1
    4. Wait for MISSION_ITEM_INT for each seq

    Raises:
        MissionDownloadError on timeout or protocol failure.
    """
    conn.ensure_autonomy_allowed()
    mav = conn.mav

    logger.info("Mission download: requesting list")
    conn.mav.mav.mission_request_list_send(mav.target_system, mav.target_component)

    try:
        count_msg = cast(Any, await conn.recv_match(MISSION_COUNT, timeout=_STEP_TIMEOUT))
        count = count_msg.count
    except TimeoutError:
        raise MissionDownloadError("Timeout waiting for MISSION_COUNT") from None

    logger.info("Mission download: received count", count=count)
    if count == 0:
        return []

    items = []
    for seq in range(count):
        conn.mav.mav.mission_request_int_send(mav.target_system, mav.target_component, seq)
        try:
            item_msg = cast(Any, await conn.recv_match_any(["MISSION_ITEM_INT", "MISSION_ITEM"], timeout=_STEP_TIMEOUT))
            if item_msg.seq != seq:
                raise MissionDownloadError(f"Received seq {item_msg.seq} but expected {seq}")
            items.append(item_msg)
        except TimeoutError:
            raise MissionDownloadError(f"Timeout waiting for item seq={seq}") from None

    # Acknowledge the download
    conn.mav.mav.mission_ack_send(mav.target_system, mav.target_component, MAV_RESULT_ACCEPTED)

    logger.info("Mission download complete", count=len(items))
    return items
