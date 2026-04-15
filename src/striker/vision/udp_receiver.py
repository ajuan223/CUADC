"""UDP receiver — accept GPS target coordinates via UDP datagrams."""

from __future__ import annotations

import asyncio
import json

import structlog

from striker.vision import register_receiver
from striker.vision.models import GpsTarget

logger = structlog.get_logger(__name__)


class UdpReceiver:
    """UDP receiver for GPS target coordinates as JSON datagrams.

    Message format: ``{"lat": float, "lon": float, "confidence": float}``

    Parameters
    ----------
    host:
        Bind address (default ``"0.0.0.0"``).
    port:
        UDP port (default ``9876``).
    """

    def __init__(self, host: str = "0.0.0.0", port: int = 9876) -> None:
        self._host = host
        self._port = port
        self._latest: GpsTarget | None = None
        self._transport: asyncio.DatagramTransport | None = None
        self._running = False

    async def start(self) -> None:
        self._running = True
        loop = asyncio.get_event_loop()
        self._transport, _ = await loop.create_datagram_endpoint(
            lambda: _UdpProtocol(self),
            local_addr=(self._host, self._port),
        )
        logger.info("UDP receiver started", host=self._host, port=self._port)

    async def stop(self) -> None:
        self._running = False
        if self._transport:
            self._transport.close()
        logger.info("UDP receiver stopped")

    def get_latest(self) -> GpsTarget | None:
        return self._latest


class _UdpProtocol(asyncio.DatagramProtocol):
    """Internal UDP protocol handler."""

    def __init__(self, receiver: UdpReceiver) -> None:
        self._receiver = receiver

    def datagram_received(self, data: bytes, addr: tuple[str, int]) -> None:
        try:
            obj = json.loads(data.decode("utf-8"))
            self._receiver._latest = GpsTarget.from_dict(obj)
        except (json.JSONDecodeError, ValueError, KeyError) as exc:
            logger.warning("Malformed UDP datagram", error=str(exc))

    def error_received(self, exc: Exception) -> None:
        logger.error("UDP error", error=str(exc))


register_receiver("udp", UdpReceiver)
