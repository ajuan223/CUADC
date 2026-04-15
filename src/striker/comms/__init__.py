"""MAVLink communication layer — connection, heartbeat, telemetry parsing.

All pymavlink imports are confined to this package (RL-04).
"""

from striker.comms.connection import ConnectionState, MAVLinkConnection
from striker.comms.heartbeat import HeartbeatMonitor
from striker.comms.messages import (
    ATTITUDE,
    COMMAND_ACK,
    GLOBAL_POSITION_INT,
    HEARTBEAT,
    MISSION_ACK,
    MISSION_COUNT,
    MISSION_ITEM_REACHED,
    MISSION_REQUEST_INT,
    STATUSTEXT,
    SYS_STATUS,
    VFR_HUD,
    WIND,
    send_command_long,
    wait_for_command_ack,
    wait_for_message,
)
from striker.comms.telemetry import (
    AttitudeData,
    BatteryData,
    GeoPosition,
    SpeedData,
    SystemStatus,
    TelemetryParser,
    WindData,
)

__all__ = [
    # Connection
    "ConnectionState",
    "MAVLinkConnection",
    # Heartbeat
    "HeartbeatMonitor",
    # Messages
    "ATTITUDE",
    "COMMAND_ACK",
    "GLOBAL_POSITION_INT",
    "HEARTBEAT",
    "MISSION_ACK",
    "MISSION_COUNT",
    "MISSION_ITEM_REACHED",
    "MISSION_REQUEST_INT",
    "STATUSTEXT",
    "SYS_STATUS",
    "VFR_HUD",
    "WIND",
    "send_command_long",
    "wait_for_command_ack",
    "wait_for_message",
    # Telemetry
    "AttitudeData",
    "BatteryData",
    "GeoPosition",
    "SpeedData",
    "SystemStatus",
    "TelemetryParser",
    "WindData",
]
