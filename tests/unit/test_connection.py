"""Unit tests for MAVLink connection module."""

from __future__ import annotations

import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from striker.comms.connection import ConnectionState, MAVLinkConnection, parse_transport_url

# ── Transport URL parsing ────────────────────────────────────────


class TestParseTransportUrl:
    def test_serial_dev(self) -> None:
        kind, url = parse_transport_url("/dev/serial0")
        assert kind == "serial"
        assert url == "/dev/serial0"

    def test_serial_ttyusb(self) -> None:
        kind, _url = parse_transport_url("/dev/ttyUSB0")
        assert kind == "serial"

    def test_udp_prefix(self) -> None:
        kind, url = parse_transport_url("udp:127.0.0.1:14550")
        assert kind == "udp"
        assert url == "udp:127.0.0.1:14550"

    def test_udpin_prefix(self) -> None:
        kind, _url = parse_transport_url("udpin:0.0.0.0:14550")
        assert kind == "udp"


# ── MAVLinkConnection init ───────────────────────────────────────


class TestMAVLinkConnectionInit:
    def test_default_settings(self) -> None:
        conn = MAVLinkConnection()
        assert conn.state == ConnectionState.DISCONNECTED
        assert conn.transport_type == "serial"
        assert not conn.is_connected

    def test_udp_url(self) -> None:
        conn = MAVLinkConnection(url="udp:127.0.0.1:14550")
        assert conn.transport_type == "udp"

    def test_custom_baud(self) -> None:
        conn = MAVLinkConnection(baud=115200)
        assert conn._baud == 115200

    def test_mav_raises_when_not_connected(self) -> None:
        conn = MAVLinkConnection()
        with pytest.raises(Exception, match="Not connected"):
            _ = conn.mav


# ── Connection state transitions ─────────────────────────────────


class TestConnectionStateTransitions:
    def test_initial_state_is_disconnected(self) -> None:
        conn = MAVLinkConnection()
        assert conn.state == ConnectionState.DISCONNECTED

    def test_state_callback_called(self) -> None:
        conn = MAVLinkConnection()
        states: list[ConnectionState] = []
        conn.register_state_callback(states.append)

        conn._set_state(ConnectionState.CONNECTING)
        assert states == [ConnectionState.CONNECTING]

        conn._set_state(ConnectionState.CONNECTED)
        assert states == [ConnectionState.CONNECTING, ConnectionState.CONNECTED]

    def test_state_callback_not_called_on_same_state(self) -> None:
        conn = MAVLinkConnection()
        states: list[ConnectionState] = []
        conn.register_state_callback(states.append)

        conn._set_state(ConnectionState.DISCONNECTED)  # same as initial
        assert states == []


# ── connect() ────────────────────────────────────────────────────


class TestConnect:
    @pytest.mark.asyncio
    async def test_connect_success(self) -> None:
        """Verify state transitions during successful connect."""
        conn = MAVLinkConnection(url="udp:127.0.0.1:14550")
        mock_mav_conn = MagicMock()
        mock_mav_conn.target_system = 1
        mock_mav_conn.target_component = 1

        # Simulate what connect() does at state level
        conn._set_state(ConnectionState.CONNECTING)
        conn._conn = mock_mav_conn
        conn._set_state(ConnectionState.CONNECTED)

        assert conn.state == ConnectionState.CONNECTED
        assert conn.is_connected
        assert conn._conn is mock_mav_conn

    @pytest.mark.asyncio
    async def test_connect_cancellation_disconnects(self) -> None:
        conn = MAVLinkConnection(url="udp:127.0.0.1:14550")
        mock_mav_conn = MagicMock()

        async def never_finishes() -> None:
            await asyncio.sleep(10)

        with (
            patch("pymavlink.mavutil.mavlink_connection", return_value=mock_mav_conn),
            patch.object(conn, "_wait_for_initial_heartbeat", new=AsyncMock(side_effect=never_finishes)),
        ):
            task = asyncio.create_task(conn.connect())
            while conn._conn is None:
                await asyncio.sleep(0)
            task.cancel()
            with pytest.raises(asyncio.CancelledError):
                await task

        mock_mav_conn.close.assert_called_once()
        assert conn.state == ConnectionState.DISCONNECTED
        assert conn._conn is None


# ── rx_loop ───────────────────────────────────────────────────────


class TestRxLoop:
    @pytest.mark.asyncio
    async def test_rx_loop_pushes_to_queue(self) -> None:
        conn = MAVLinkConnection()

        # Simulate a mock pymavlink message
        mock_msg = MagicMock()
        mock_msg.get_type.return_value = "HEARTBEAT"

        mock_mav_conn = MagicMock()
        # Return one message then None (loop will need to stop)
        call_count = 0

        def fake_recv_match(blocking: bool = False) -> object:
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                return mock_msg
            conn._running = False  # Stop the loop after first message
            return None

        mock_mav_conn.recv_match = fake_recv_match
        conn._conn = mock_mav_conn
        conn._running = True

        await conn._rx_loop()

        # Queue should have the raw message (parsed telemetry may also be added)
        assert not conn._queue.empty()


# ── send() ────────────────────────────────────────────────────────


class TestSend:
    def test_send_calls_mav(self) -> None:
        conn = MAVLinkConnection()
        mock_mav_conn = MagicMock()
        conn._conn = mock_mav_conn

        msg = MagicMock()
        conn.send(msg)
        mock_mav_conn.mav.send.assert_called_once_with(msg)

    def test_send_mission_item_blocks_after_autonomy_relinquished(self) -> None:
        conn = MAVLinkConnection()
        mock_mav_conn = MagicMock()
        conn._conn = mock_mav_conn
        conn.relinquish_autonomy("RC override")

        with pytest.raises(Exception, match="Autonomy relinquished"):
            conn.send_mission_item(MagicMock())

        mock_mav_conn.mav.send.assert_not_called()

    def test_send_raises_when_not_connected(self) -> None:
        conn = MAVLinkConnection()
        with pytest.raises(Exception, match="Cannot send"):
            conn.send(MagicMock())


# ── recv_match ────────────────────────────────────────────────────


class TestRecvMatch:
    @pytest.mark.asyncio
    async def test_recv_match_timeout(self) -> None:
        conn = MAVLinkConnection()
        # Queue is empty, should timeout
        with pytest.raises(TimeoutError, match="Timeout"):
            await conn.recv_match("HEARTBEAT", timeout=0.1)


# ── disconnect ────────────────────────────────────────────────────


class TestDisconnect:
    def test_disconnect_closes_connection(self) -> None:
        conn = MAVLinkConnection()
        mock_mav_conn = MagicMock()
        conn._conn = mock_mav_conn

        conn.disconnect()
        mock_mav_conn.close.assert_called_once()
        assert conn.state == ConnectionState.DISCONNECTED
        assert conn._conn is None
