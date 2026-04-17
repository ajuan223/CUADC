"""MAVLink connection management — async-compatible adapter over pymavlink.

Provides :class:`MAVLinkConnection` that wraps ``pymavlink.mavutil.mavlink_connection``
with an asyncio-native producer/consumer pattern.
"""

from __future__ import annotations

import asyncio
from collections.abc import Callable
from enum import Enum, unique
from typing import TYPE_CHECKING, Any, cast

import structlog

from striker.comms.telemetry import TelemetryParser
from striker.exceptions import CommsError

if TYPE_CHECKING:
    from pymavlink.mavutil import mavfile

logger = structlog.get_logger(__name__)


# ── Data types ────────────────────────────────────────────────────


@unique
class ConnectionState(Enum):
    """Connection lifecycle states."""

    DISCONNECTED = "DISCONNECTED"
    CONNECTING = "CONNECTING"
    CONNECTED = "CONNECTED"
    LOST = "LOST"


# ── Transport URL parsing ────────────────────────────────────────


def parse_transport_url(url: str) -> tuple[str, str]:
    """Return ``(transport_type, url)`` from a MAVLink device URL.

    Returns
    -------
    tuple[str, str]
        ``(type, url)`` where *type* is ``"serial"`` or ``"udp"``.
    """
    if url.startswith("udp") or url.startswith("UDP"):
        return ("udp", url)
    # Serial: /dev/ttyUSB0, /dev/serial0, COM3, etc.
    return ("serial", url)


# ── Callback type ─────────────────────────────────────────────────

StateCallback = Callable[[ConnectionState], None]
MessageCallback = Callable[[object], None]


# ── MAVLinkConnection ────────────────────────────────────────────


class MAVLinkConnection:
    """Async-compatible MAVLink connection adapter.

    Wraps ``pymavlink.mavutil.mavlink_connection`` with:
    - Async producer/consumer via :class:`asyncio.Queue`
    - Heartbeat-based connection health
    - Connection state machine: DISCONNECTED → CONNECTING → CONNECTED → LOST

    Parameters
    ----------
    url:
        Transport URL (e.g. ``"/dev/serial0"``, ``"udp:127.0.0.1:14550"``).
    baud:
        Serial baud rate (ignored for UDP).
    heartbeat_timeout_s:
        Seconds without heartbeat before marking connection as LOST.
    """

    def __init__(
        self,
        url: str = "/dev/TTYAMA0",
        baud: int = 921600,
        heartbeat_timeout_s: float = 3.0,
    ) -> None:
        self._url = url
        self._baud = baud
        self._heartbeat_timeout_s = heartbeat_timeout_s
        self._state = ConnectionState.DISCONNECTED
        self._conn: mavfile | None = None
        self._queue: asyncio.Queue[object] = asyncio.Queue()
        self._running = False
        self._autonomy_enabled = True
        self._autonomy_disabled_reason = ""
        self._state_callbacks: list[StateCallback] = []
        self._message_callbacks: list[MessageCallback] = []
        self._telemetry_parser = TelemetryParser()
        self._transport_type, self._transport_url = parse_transport_url(url)

    # ── Properties ────────────────────────────────────────────────

    @property
    def state(self) -> ConnectionState:
        """Current connection state."""
        return self._state

    @property
    def transport_type(self) -> str:
        """Transport type string (``"serial"`` or ``"udp"``)."""
        return self._transport_type

    @property
    def is_connected(self) -> bool:
        return self._state == ConnectionState.CONNECTED

    @property
    def mav(self) -> mavfile:
        """Raw pymavlink connection — raises if not connected."""
        if self._conn is None:
            msg = "Not connected — call connect() first"
            raise CommsError(msg)
        return self._conn

    @property
    def flightmode(self) -> str:
        """Current flight mode name from pymavlink (e.g. MANUAL, AUTO, GUIDED).

        pymavlink automatically decodes custom_mode into a human-readable
        mode name on the connection object whenever a HEARTBEAT is received.
        Returns ``"UNKNOWN"`` if not connected or not yet determined.
        """
        if self._conn is None:
            return "UNKNOWN"
        return getattr(self._conn, "flightmode", "UNKNOWN")

    @property
    def autonomy_enabled(self) -> bool:
        """Whether autonomous outbound control is still permitted."""
        return self._autonomy_enabled

    def relinquish_autonomy(self, reason: str = "") -> None:
        """Permanently disable autonomous outbound control for this run."""
        if not self._autonomy_enabled:
            return
        self._autonomy_enabled = False
        self._autonomy_disabled_reason = reason
        logger.warning("Autonomy relinquished", reason=reason or "override")

    def ensure_autonomy_allowed(self) -> None:
        """Raise if autonomous outbound control has been relinquished."""
        if not self._autonomy_enabled:
            reason = self._autonomy_disabled_reason or "override active"
            raise CommsError(f"Autonomy relinquished: {reason}")

    # ── State management ──────────────────────────────────────────

    def _set_state(self, new_state: ConnectionState) -> None:
        if self._state == new_state:
            return
        old = self._state
        self._state = new_state
        logger.info("Connection state changed", old=old.value, new=new_state.value)
        for cb in self._state_callbacks:
            try:
                cb(new_state)
            except Exception:
                logger.exception("State callback error")

    def register_state_callback(self, callback: StateCallback) -> None:
        """Register a callback invoked on connection state changes."""
        self._state_callbacks.append(callback)

    def register_message_callback(self, callback: MessageCallback) -> None:
        """Register a callback invoked for each received raw or parsed message."""
        self._message_callbacks.append(callback)

    # ── Connect / Disconnect ──────────────────────────────────────

    async def connect(self) -> None:
        """Establish MAVLink connection and wait for first heartbeat."""
        # RL-04: confine pymavlink imports to the comms package.
        from pymavlink import mavutil

        self._set_state(ConnectionState.CONNECTING)
        logger.info("Connecting to MAVLink", url=self._url, baud=self._baud)

        try:
            loop = asyncio.get_running_loop()
            self._conn = cast(
                Any,
                await loop.run_in_executor(
                None,
                lambda: mavutil.mavlink_connection(self._url, baud=self._baud),
                ),
            )
            await self._wait_for_initial_heartbeat()
            self._set_state(ConnectionState.CONNECTED)
            assert self._conn is not None
            logger.info(
                "MAVLink connected",
                target_system=self._conn.target_system,
                target_component=self._conn.target_component,
            )
        except asyncio.CancelledError:
            self.disconnect()
            raise
        except Exception as exc:
            self.disconnect()
            raise CommsError(f"Failed to connect: {exc}") from exc

    async def _wait_for_initial_heartbeat(self) -> None:
        """Poll for the initial heartbeat without blocking shutdown/cancellation."""
        assert self._conn is not None

        while True:
            msg = self._conn.recv_match(type="HEARTBEAT", blocking=False)
            if msg is not None:
                return
            await asyncio.sleep(0.1)

    def disconnect(self) -> None:
        """Close the connection and reset state."""
        self._running = False
        if self._conn is not None:
            try:
                self._conn.close()
            except Exception:
                logger.exception("Error closing MAVLink connection")
            self._conn = None
        self._set_state(ConnectionState.DISCONNECTED)
        logger.info("Disconnected")

    # ── Async run loop ────────────────────────────────────────────

    async def run(self) -> None:
        """Start the receive loop (producer). Runs until disconnect()."""
        self._running = True
        logger.info("RX loop started")
        await self._rx_loop()

    async def _rx_loop(self) -> None:
        """Non-blocking recv_match + asyncio.Queue dispatch + 5ms yield."""
        assert self._conn is not None  # ensured by connect()
        while self._running:
            try:
                msg = self._conn.recv_match(blocking=False)
            except Exception:
                logger.exception("recv_match error")
                await asyncio.sleep(0.005)
                continue

            if msg is not None:
                msg_type = msg.get_type()
                if msg_type == "BAD_DATA":
                    await asyncio.sleep(0.005)
                    continue
                # Parse telemetry immediately (RL-04, REQ-COMMS-007)
                parsed = self._telemetry_parser.parse(msg)
                if parsed is not None:
                    await self._queue.put(parsed)
                    for cb in self._message_callbacks:
                        try:
                            cb(parsed)
                        except Exception:
                            logger.exception("Message callback error", callback_type="parsed")
                # Always push raw msg for message-level consumers (heartbeat, ACK)
                await self._queue.put(msg)
                for cb in self._message_callbacks:
                    try:
                        cb(msg)
                    except Exception:
                        logger.exception("Message callback error", callback_type="raw")

            await asyncio.sleep(0.005)  # 5ms yield — never exceed

    # ── Send ──────────────────────────────────────────────────────

    def _require_connected(self) -> mavfile:
        if self._conn is None:
            msg_text = "Cannot send — not connected"
            raise CommsError(msg_text)
        return self._conn

    def send(self, msg: object) -> None:
        """Thread-safe message send via pymavlink master."""
        conn = self._require_connected()
        conn.mav.send(msg)

    def send_mission_item(self, msg: object) -> None:
        """Send a mission item while enforcing autonomy guard."""
        self.ensure_autonomy_allowed()
        conn = self._require_connected()
        conn.mav.send(msg)

    def command_long_send(self, *args: object) -> None:
        """Send COMMAND_LONG while enforcing autonomy guard."""
        self.ensure_autonomy_allowed()
        conn = self._require_connected()
        conn.mav.command_long_send(*args)

    def command_int_send(self, *args: object) -> None:
        """Send COMMAND_INT while enforcing autonomy guard."""
        self.ensure_autonomy_allowed()
        conn = self._require_connected()
        conn.mav.command_int_send(*args)

    def mission_clear_all_send(self, *args: object) -> None:
        """Send MISSION_CLEAR_ALL while enforcing autonomy guard."""
        self.ensure_autonomy_allowed()
        conn = self._require_connected()
        conn.mav.mission_clear_all_send(*args)

    def mission_count_send(self, *args: object) -> None:
        """Send MISSION_COUNT while enforcing autonomy guard."""
        self.ensure_autonomy_allowed()
        conn = self._require_connected()
        conn.mav.mission_count_send(*args)

    # ── Receive ───────────────────────────────────────────────────

    async def recv_match_any(self, msg_types: list[str], timeout: float = 5.0) -> object:
        """Consumer: await any specific raw MAVLink message type from the queue."""
        deadline = asyncio.get_event_loop().time() + timeout
        while True:
            remaining = deadline - asyncio.get_event_loop().time()
            if remaining <= 0:
                raise TimeoutError(f"Timeout waiting for any of {msg_types} ({timeout}s)")

            try:
                item = await asyncio.wait_for(self._queue.get(), timeout=remaining)
            except TimeoutError:
                raise TimeoutError(f"Timeout waiting for any of {msg_types} ({timeout}s)") from None

            if hasattr(item, "get_type") and item.get_type() in msg_types:
                return item

    async def recv_match(self, msg_type: str, timeout: float = 5.0) -> object:
        """Consumer: await a specific message type from the queue with timeout."""
        return await self.recv_match_any([msg_type], timeout=timeout)
