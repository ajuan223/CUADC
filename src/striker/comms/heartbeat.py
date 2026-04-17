"""Heartbeat monitor — send/receive heartbeat with watchdog timeout.

Manages periodic heartbeat transmission (1Hz default) and a receive
watchdog that detects connection loss within a configurable timeout.
"""

from __future__ import annotations

import asyncio
import contextlib
from collections.abc import Callable
from typing import TYPE_CHECKING

import structlog

from striker.comms.messages import build_heartbeat_msg

if TYPE_CHECKING:
    from striker.comms.connection import MAVLinkConnection

logger = structlog.get_logger(__name__)

# Callback type for health status changes
HealthCallback = Callable[[bool], None]


class HeartbeatMonitor:
    """Heartbeat send/receive monitor with health tracking.

    Parameters
    ----------
    conn:
        MAVLinkConnection instance (must be connected).
    send_interval_s:
        Heartbeat send period in seconds (default 1.0).
    receive_timeout_s:
        Seconds without heartbeat receive before marking unhealthy (default 3.0).
    """

    def __init__(
        self,
        conn: MAVLinkConnection,
        send_interval_s: float = 1.0,
        receive_timeout_s: float = 3.0,
    ) -> None:
        self._conn = conn
        self._send_interval_s = send_interval_s
        self._receive_timeout_s = receive_timeout_s
        self._heartbeat_event = asyncio.Event()
        self._stop_event = asyncio.Event()
        self._healthy = False
        self._running = False
        self._health_callbacks: list[HealthCallback] = []

    @property
    def is_healthy(self) -> bool:
        """Whether the connection heartbeat is within timeout."""
        return self._healthy

    def notify_heartbeat_received(self) -> None:
        """Called when a HEARTBEAT message is received."""
        self._heartbeat_event.set()

    def seed_healthy(self) -> None:
        """Mark the link healthy after initial connect established heartbeat."""
        self._set_healthy(True)

    def register_health_callback(self, callback: HealthCallback) -> None:
        """Register a callback invoked when health status changes."""
        self._health_callbacks.append(callback)

    def _set_healthy(self, healthy: bool) -> None:
        if self._healthy == healthy:
            return
        self._healthy = healthy
        logger.info("Heartbeat health changed", healthy=healthy)
        for cb in self._health_callbacks:
            try:
                cb(healthy)
            except Exception:
                logger.exception("Health callback error")

    # ── Coroutines ────────────────────────────────────────────────

    async def run(self) -> None:
        """Run both heartbeat sender and watchdog concurrently."""
        self._running = True
        self._stop_event.clear()
        await asyncio.gather(
            self._heartbeat_sender(),
            self._heartbeat_watchdog(),
        )

    async def _heartbeat_sender(self) -> None:
        """Periodic heartbeat send at configured interval."""
        while self._running:
            try:
                msg = build_heartbeat_msg(
                    self._conn.mav.target_system,
                    self._conn.mav.target_component,
                )
                self._conn.send(msg)
            except Exception:
                if self._running:
                    logger.exception("Heartbeat send error")
            try:
                await asyncio.wait_for(self._stop_event.wait(), timeout=self._send_interval_s)
            except TimeoutError:
                continue

    async def _heartbeat_watchdog(self) -> None:
        """Watchdog: detect connection loss via heartbeat timeout."""
        while self._running:
            self._heartbeat_event.clear()
            heartbeat_wait = asyncio.create_task(self._heartbeat_event.wait())
            stop_wait = asyncio.create_task(self._stop_event.wait())
            done, pending = await asyncio.wait(
                {heartbeat_wait, stop_wait},
                timeout=self._receive_timeout_s,
                return_when=asyncio.FIRST_COMPLETED,
            )
            for task in pending:
                task.cancel()
            for task in pending:
                with contextlib.suppress(asyncio.CancelledError):
                    await task

            if stop_wait in done or not self._running:
                return
            if heartbeat_wait in done:
                self._set_healthy(True)
                continue

            self._set_healthy(False)
            if self._running:
                logger.warning("Heartbeat timeout", timeout_s=self._receive_timeout_s)

    def stop(self) -> None:
        """Signal both coroutines to stop."""
        self._running = False
        self._stop_event.set()
        self._heartbeat_event.set()
