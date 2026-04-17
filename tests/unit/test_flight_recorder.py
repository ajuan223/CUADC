"""Unit tests for flight recorder."""

from __future__ import annotations

import csv
from pathlib import Path
from unittest.mock import MagicMock

import pytest

from striker.comms.telemetry import AttitudeData, BatteryData, SpeedData, SystemStatus
from striker.telemetry.flight_recorder import FlightRecorder, DEFAULT_FIELDS


class TestFlightRecorder:
    def test_csv_created_with_correct_headers(self, tmp_path: Path) -> None:
        output = tmp_path / "test_flight.csv"
        recorder = FlightRecorder(output_path=output, sample_rate_hz=10.0)

        # Simulate open + close
        recorder._open_file()
        recorder._close_file()

        assert output.exists()
        with open(output) as f:
            reader = csv.reader(f)
            headers = next(reader)
        assert headers == DEFAULT_FIELDS

    def test_telemetry_rows_written(self, tmp_path: Path) -> None:
        output = tmp_path / "test_flight.csv"
        recorder = FlightRecorder(output_path=output, sample_rate_hz=10.0)

        recorder._open_file()

        # Simulate a context snapshot
        ctx = MagicMock()
        ctx.connection.flightmode = "AUTO"
        ctx.current_position = MagicMock()
        ctx.current_position.lat = 30.0
        ctx.current_position.lon = 120.0
        ctx.current_position.alt_m = 100.0
        ctx.current_position.relative_alt_m = 50.0
        ctx.current_attitude = AttitudeData(roll_rad=0.1, pitch_rad=0.2, yaw_rad=0.3)
        ctx.current_speed = SpeedData(airspeed_mps=18.5, groundspeed_mps=17.2)
        ctx.current_battery = BatteryData(voltage_v=12.1, current_a=4.2, remaining_pct=87)
        ctx.current_system_status = SystemStatus(mode="AUTO", armed=True, system_status=4)

        row = recorder._snapshot(ctx)
        recorder._writer.writerow(row)
        recorder._close_file()

        with open(output) as f:
            reader = csv.DictReader(f)
            rows = list(reader)
        assert len(rows) == 1
        assert rows[0]["lat"] == "30.0"
        assert rows[0]["lon"] == "120.0"
        assert rows[0]["roll_rad"] == "0.1"
        assert rows[0]["airspeed_mps"] == "18.5"
        assert rows[0]["battery_voltage_v"] == "12.1"
        assert rows[0]["mode"] == "AUTO"
        assert rows[0]["armed"] == "True"

    def test_auto_flush_on_stop(self, tmp_path: Path) -> None:
        output = tmp_path / "test_flight.csv"
        recorder = FlightRecorder(output_path=output)
        recorder._open_file()
        recorder._close_file()

        # File should be flushed and closed
        assert output.exists()

    def test_custom_output_directory(self, tmp_path: Path) -> None:
        nested = tmp_path / "subdir" / "logs" / "flight.csv"
        recorder = FlightRecorder(output_path=nested)
        recorder._open_file()
        recorder._close_file()
        assert nested.exists()
