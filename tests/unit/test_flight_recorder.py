"""Unit tests for flight recorder."""

from __future__ import annotations

import csv
from pathlib import Path
from unittest.mock import MagicMock

import pytest

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
        ctx.current_position = MagicMock()
        ctx.current_position.lat = 30.0
        ctx.current_position.lon = 120.0
        ctx.current_position.alt_m = 100.0
        ctx.current_position.relative_alt_m = 50.0

        row = recorder._snapshot(ctx)
        recorder._writer.writerow(row)
        recorder._close_file()

        with open(output) as f:
            reader = csv.DictReader(f)
            rows = list(reader)
        assert len(rows) == 1
        assert rows[0]["lat"] == "30.0"
        assert rows[0]["lon"] == "120.0"

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
