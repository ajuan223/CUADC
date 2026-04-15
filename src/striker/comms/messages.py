"""Message helpers — command sending and ACK verification.

Provides :func:`send_command_long`, :func:`wait_for_message`, and
:func:`wait_for_command_ack` for higher-level flight code.
"""

from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING, Any

import structlog

from striker.exceptions import CommsError

if TYPE_CHECKING:
    from striker.comms.connection import MAVLinkConnection

logger = structlog.get_logger(__name__)

# ── Message type constants ────────────────────────────────────────

HEARTBEAT = "HEARTBEAT"
GLOBAL_POSITION_INT = "GLOBAL_POSITION_INT"
ATTITUDE = "ATTITUDE"
VFR_HUD = "VFR_HUD"
WIND = "WIND"
SYS_STATUS = "SYS_STATUS"
STATUSTEXT = "STATUSTEXT"
COMMAND_ACK = "COMMAND_ACK"
MISSION_ITEM_REACHED = "MISSION_ITEM_REACHED"
MISSION_REQUEST_INT = "MISSION_REQUEST_INT"
MISSION_ACK = "MISSION_ACK"
MISSION_COUNT = "MISSION_COUNT"
RANGEFINDER = "RANGEFINDER"


# ── Command helpers ───────────────────────────────────────────────


async def send_command_long(
    conn: MAVLinkConnection,
    command: int,
    param1: float = 0.0,
    param2: float = 0.0,
    param3: float = 0.0,
    param4: float = 0.0,
    param5: float = 0.0,
    param6: float = 0.0,
    param7: float = 0.0,
    timeout: float = 5.0,
) -> Any:
    """Send a MAVLink COMMAND_LONG and wait for COMMAND_ACK.

    Parameters
    ----------
    conn:
        Active MAVLinkConnection.
    command:
        MAVLink command ID (e.g. ``MAV_CMD_COMPONENT_ARM_DISARM``).
    param1 … param7:
        Command parameters.
    timeout:
        Seconds to wait for COMMAND_ACK.

    Returns
    -------
    COMMAND_ACK message on success.

    Raises
    ------
    CommsError
        If ACK result is not ACCEPTED.
    TimeoutError
        If no ACK received within *timeout*.
    """
    from pymavlink import mavutil  # noqa: RL-04 — confined to comms/

    mav = conn.mav
    mav.mav.command_long_send(
        mav.target_system,
        mav.target_component,
        command,
        0,  # confirmation
        param1, param2, param3, param4, param5, param6, param7,
    )

    ack = await wait_for_command_ack(conn, command, timeout)

    # Check result
    result = ack.result
    if result != mavutil.mavlink.MAV_RESULT_ACCEPTED:
        raise CommsError(
            f"Command {command} rejected: result={result}",
        )

    return ack


async def wait_for_message(
    conn: MAVLinkConnection,
    msg_type: str,
    timeout: float = 5.0,
) -> Any:
    """Wait for a specific MAVLink message type with timeout.

    Raises
    ------
    TimeoutError
        If message not received within *timeout* seconds.
    """
    return await conn.recv_match(msg_type, timeout=timeout)


async def wait_for_command_ack(
    conn: MAVLinkConnection,
    command_id: int,
    timeout: float = 5.0,
) -> Any:
    """Wait for a COMMAND_ACK matching *command_id*.

    Raises
    ------
    TimeoutError
        If no matching ACK received within *timeout* seconds.
    """
    deadline = asyncio.get_event_loop().time() + timeout
    while True:
        remaining = deadline - asyncio.get_event_loop().time()
        if remaining <= 0:
            raise TimeoutError(f"Timeout waiting for COMMAND_ACK (command={command_id})")

        msg = await conn.recv_match(COMMAND_ACK, timeout=remaining)
        if msg.command == command_id:
            return msg
