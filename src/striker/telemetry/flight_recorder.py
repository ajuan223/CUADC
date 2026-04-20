"""Flight recorder — CSV recording of telemetry data snapshots."""

from __future__ import annotations

import asyncio
import csv
import io
from pathlib import Path
from typing import TYPE_CHECKING, Any

import structlog

if TYPE_CHECKING:
    from striker.core.context import MissionContext

logger = structlog.get_logger(__name__)

# Default CSV field names
DEFAULT_FIELDS = [
    "timestamp",
    "lat",
    "lon",
    "alt_m",
    "relative_alt_m",
    "roll_rad",
    "pitch_rad",
    "yaw_rad",
    "airspeed_mps",
    "groundspeed_mps",
    "battery_voltage_v",
    "battery_remaining_pct",
    "mode",
    "armed",
    "release_triggered",
    "release_timestamp",
    "planned_drop_lat",
    "planned_drop_lon",
    "planned_drop_source",
    "actual_drop_lat",
    "actual_drop_lon",
    "actual_drop_source",
]


class FlightRecorder:
    """CSV flight data recorder.

    Parameters
    ----------
    output_path:
        Path to the output CSV file.
    fields:
        CSV column names (default: standard telemetry fields).
    sample_rate_hz:
        Recording sample rate (default 1.0 Hz).
    """

    def __init__(
        self,
        output_path: str | Path = "flight_log.csv",
        fields: list[str] | None = None,
        sample_rate_hz: float = 1.0,
    ) -> None:
        self._output_path = Path(output_path)
        self._fields = fields or DEFAULT_FIELDS
        self._sample_rate_hz = sample_rate_hz
        self._running = False
        self._file: io.TextIOBase | None = None
        self._writer: csv.DictWriter | None = None  # type: ignore[type-arg]

    def _open_file(self) -> None:
        """Open CSV file and write header."""
        self._output_path.parent.mkdir(parents=True, exist_ok=True)
        self._file = open(self._output_path, "w", newline="", encoding="utf-8")  # noqa: SIM115
        self._writer = csv.DictWriter(self._file, fieldnames=self._fields, extrasaction="ignore")
        self._writer.writeheader()

    def _close_file(self) -> None:
        """Flush and close the CSV file."""
        if self._file is not None:
            self._file.flush()
            self._file.close()
            self._file = None

    def _snapshot(self, context: MissionContext) -> dict[str, Any]:
        """Capture a telemetry snapshot from the context."""
        import time

        pos = context.current_position
        attitude = context.current_attitude
        speed = context.current_speed
        battery = context.current_battery
        system_status = context.current_system_status
        planned_drop_point = context.planned_drop_point
        actual_drop_point = context.actual_drop_point
        return {
            "timestamp": time.monotonic(),
            "lat": pos.lat if pos else "",
            "lon": pos.lon if pos else "",
            "alt_m": pos.alt_m if pos else "",
            "relative_alt_m": pos.relative_alt_m if pos else "",
            "roll_rad": attitude.roll_rad if attitude else "",
            "pitch_rad": attitude.pitch_rad if attitude else "",
            "yaw_rad": attitude.yaw_rad if attitude else "",
            "airspeed_mps": speed.airspeed_mps if speed else "",
            "groundspeed_mps": speed.groundspeed_mps if speed else "",
            "battery_voltage_v": battery.voltage_v if battery else "",
            "battery_remaining_pct": battery.remaining_pct if battery else "",
            "mode": system_status.mode if system_status else context.connection.flightmode,
            "armed": system_status.armed if system_status else "",
            "release_triggered": context.release_triggered,
            "release_timestamp": context.release_timestamp if context.release_timestamp is not None else "",
            "planned_drop_lat": planned_drop_point[0] if planned_drop_point else "",
            "planned_drop_lon": planned_drop_point[1] if planned_drop_point else "",
            "planned_drop_source": context.drop_point_source,
            "actual_drop_lat": actual_drop_point[0] if actual_drop_point else "",
            "actual_drop_lon": actual_drop_point[1] if actual_drop_point else "",
            "actual_drop_source": context.actual_drop_source,
        }

    async def run(self, context: MissionContext) -> None:
        """Periodic telemetry snapshot recording coroutine."""
        self._running = True
        self._open_file()
        interval = 1.0 / self._sample_rate_hz
        logger.info("Flight recorder started", path=str(self._output_path), rate_hz=self._sample_rate_hz)

        try:
            while self._running:
                if self._writer:
                    row = self._snapshot(context)
                    self._writer.writerow(row)
                    assert self._file is not None
                    self._file.flush()
                await asyncio.sleep(interval)
        finally:
            self._close_file()
            logger.info("Flight recorder stopped")

    def stop(self) -> None:
        """Stop recording and flush."""
        self._running = False
