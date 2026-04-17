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
MISSION_CURRENT = "MISSION_CURRENT"
MAVLINK_MSG_ID_MISSION_CURRENT = 42
MAVLINK_MSG_ID_MISSION_ITEM_REACHED = 46
MISSION_REQUEST = "MISSION_REQUEST"
MISSION_REQUEST_INT = "MISSION_REQUEST_INT"
MISSION_ACK = "MISSION_ACK"
MISSION_COUNT = "MISSION_COUNT"
RANGEFINDER = "RANGEFINDER"

# ── MAVLink command / flag constants (sourced from pymavlink) ─────
# These integer values are MAVLink protocol constants. Extracted here
# so that non-comms modules never need to import pymavlink directly.

MAV_CMD_COMPONENT_ARM_DISARM = 400
MAV_CMD_NAV_TAKEOFF = 22
MAV_CMD_DO_SET_MODE = 176
MAV_CMD_DO_CHANGE_SPEED = 178
MAV_CMD_DO_SET_SERVO = 183
MAV_CMD_DO_LAND_START = 189
MAV_CMD_NAV_LAND = 21
MAV_CMD_NAV_WAYPOINT = 16
MAV_CMD_MISSION_SET_CURRENT = 224
MAV_CMD_SET_MESSAGE_INTERVAL = 511

MAV_MODE_FLAG_CUSTOM_MODE_ENABLED = 1
MAV_MODE_FLAG_SAFETY_ARMED = 128

MAV_RESULT_ACCEPTED = 0

MAV_TYPE_GCS = 6
MAV_AUTOPILOT_INVALID = 8

MAV_FRAME_GLOBAL_RELATIVE_ALT = 3
MAV_FRAME_GLOBAL_RELATIVE_ALT_INT = 6


def build_heartbeat_msg(
    target_system: int,
    target_component: int,
    type_: int = MAV_TYPE_GCS,
    autopilot: int = MAV_AUTOPILOT_INVALID,
    base_mode: int = 0,
    custom_mode: int = 0,
    system_status: int = 0,
) -> object:
    """Build a MAVLink HEARTBEAT message suitable for ``conn.send()``.

    Constructs the message using the pymavlink connection's message factory,
    so it must be called *after* the connection is established (so that the
    mavlink dialect is loaded).
    """
    from pymavlink import mavutil  # noqa: RL-04 — confined to comms/

    return mavutil.mavlink.MAVLink_heartbeat_message(
        type=type_,
        autopilot=autopilot,
        base_mode=base_mode,
        custom_mode=custom_mode,
        system_status=system_status,
        mavlink_version=0,
    )


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

    conn.ensure_autonomy_allowed()
    mav = conn.mav
    conn.command_long_send(
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
