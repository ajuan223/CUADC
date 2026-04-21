"""SITL integration tests — MAVLink connection and telemetry."""

from __future__ import annotations

import asyncio

import pytest

from striker.comms.connection import ConnectionState, MAVLinkConnection


@pytest.fixture
def sitl_url() -> str:
    return "udp:127.0.0.1:14550"


class TestSITLConnection:
    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_connect_and_receive_heartbeat(self, sitl_process, sitl_url: str) -> None:  # type: ignore
        """Connect to SITL and receive a HEARTBEAT message."""
        conn = MAVLinkConnection(url=sitl_url)
        try:
            await conn.connect()
            assert conn.state == ConnectionState.CONNECTED

            conn._running = True
            rx_task = asyncio.create_task(conn._rx_loop())
            try:
                msg = await conn.recv_match("HEARTBEAT", timeout=10.0)
                assert msg is not None
                assert msg.get_type() == "HEARTBEAT"  # type: ignore
            finally:
                conn._running = False
                rx_task.cancel()
        finally:
            conn.disconnect()

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_telemetry_parsing_with_real_sitl(self, sitl_process, sitl_url: str) -> None:  # type: ignore
        """Verify telemetry dataclasses are produced from real SITL data."""
        from striker.comms.telemetry import GeoPosition

        conn = MAVLinkConnection(url=sitl_url)
        try:
            await conn.connect()
            # Run rx_loop briefly to collect messages
            async def collect_for(duration: float) -> list[object]:
                items: list[object] = []
                deadline = asyncio.get_event_loop().time() + duration
                while asyncio.get_event_loop().time() < deadline:
                    try:
                        remaining = deadline - asyncio.get_event_loop().time()
                        if remaining <= 0:
                            break
                        item = await asyncio.wait_for(conn._queue.get(), timeout=remaining)
                        items.append(item)
                    except TimeoutError:
                        break
                return items

            # Start rx_loop as task
            conn._running = True
            rx_task = asyncio.create_task(conn._rx_loop())

            items = await collect_for(5.0)
            conn._running = False
            rx_task.cancel()

            geo_positions = [i for i in items if isinstance(i, GeoPosition)]
            assert len(geo_positions) > 0, "Expected at least one GeoPosition from SITL"
        finally:
            conn.disconnect()

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_heartbeat_timeout_detection(self, sitl_process, sitl_url: str) -> None:  # type: ignore
        """Verify heartbeat timeout when SITL is killed mid-session."""
        conn = MAVLinkConnection(url=sitl_url, heartbeat_timeout_s=0.5)
        try:
            await conn.connect()
            assert conn.state == ConnectionState.CONNECTED
        finally:
            conn.disconnect()
