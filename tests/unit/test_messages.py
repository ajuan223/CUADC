"""Unit tests for message helpers."""

from __future__ import annotations

import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from striker.comms.connection import MAVLinkConnection
from striker.comms.messages import send_command_long, wait_for_message


class TestSendCommandLong:
    @pytest.mark.asyncio
    async def test_sends_correct_command(self) -> None:
        """Verify send_command_long sends the command and verifies ACK."""
        from pymavlink import mavutil as real_mavutil

        conn = MAVLinkConnection()
        mock_mav = MagicMock()
        mock_conn = MagicMock()
        mock_conn.mav = mock_mav
        conn._conn = mock_conn

        # Mock ACK with ACCEPTED result
        mock_ack = MagicMock()
        mock_ack.get_type.return_value = "COMMAND_ACK"
        mock_ack.command = 400  # MAV_CMD_COMPONENT_ARM_DISARM
        mock_ack.result = real_mavutil.mavlink.MAV_RESULT_ACCEPTED

        # Override recv_match to return ACK
        conn.recv_match = AsyncMock(return_value=mock_ack)  # type: ignore[assignment]

        result = await send_command_long(conn, 400, param1=1.0)
        mock_mav.command_long_send.assert_called_once()
        assert result == mock_ack


class TestWaitForMessage:
    @pytest.mark.asyncio
    async def test_timeout_behavior(self) -> None:
        conn = MAVLinkConnection()
        # Empty queue → timeout
        with pytest.raises(TimeoutError):
            await wait_for_message(conn, "HEARTBEAT", timeout=0.1)
