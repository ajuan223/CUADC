"""TCP receiver — accept GPS drop point coordinates via TCP JSON messages."""

from __future__ import annotations

import asyncio
import json

import structlog

from striker.vision import register_receiver
from striker.vision.models import GpsDropPoint

logger = structlog.get_logger(__name__)


class TcpReceiver:
    """TCP server that receives GPS drop point coordinates as JSON.

    Message format: ``{"lat": float, "lon": float, "confidence": float}``
    """

    def __init__(self, host: str = "0.0.0.0", port: int = 9876) -> None:
        self._host = host
        self._port = port
        self._latest: GpsDropPoint | None = None
        self._server: asyncio.Server | None = None
        self._running = False

    async def start(self) -> None:
        self._running = True
        self._server = await asyncio.start_server(
            self._handle_connection, self._host, self._port,
        )
        logger.info("TCP receiver started", host=self._host, port=self._port)

    async def stop(self) -> None:
        self._running = False
        if self._server:
            self._server.close()
            await self._server.wait_closed()
            self._server = None
        logger.info("TCP receiver stopped")

    def get_latest(self) -> GpsDropPoint | None:
        return self._latest

    async def _handle_connection(
        self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter,
    ) -> None:
        addr = writer.get_extra_info("peername")
        logger.debug("TCP connection", addr=addr)

        try:
            while self._running:
                data = await reader.readline()
                if not data:
                    break
                try:
                    obj = json.loads(data.decode("utf-8"))
                    self._latest = GpsDropPoint.from_dict(obj)
                except (json.JSONDecodeError, ValueError, KeyError) as exc:
                    logger.warning("Malformed TCP message", error=str(exc), raw=data)
        except asyncio.CancelledError:
            pass
        finally:
            writer.close()
            await writer.wait_closed()


register_receiver("tcp", TcpReceiver)
