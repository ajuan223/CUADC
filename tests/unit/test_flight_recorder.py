"""Unit tests for flight recorder."""

from __future__ import annotations

import csv
from pathlib import Path
from unittest.mock import MagicMock

from striker.comms.telemetry import AttitudeData, BatteryData, SpeedData, SystemStatus
from striker.telemetry.flight_recorder import DEFAULT_FIELDS, FlightRecorder


class TestFlightRecorder:
    def test_csv_created_with_correct_headers(self, tmp_path: Path) -> None:
        output = tmp_path / "test_flight.csv"
        recorder = FlightRecorder(output_path=output, sample_rate_hz=10.0)

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

        ctx = self._make_context()
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
        assert rows[0]["release_triggered"] == "False"
        assert rows[0]["release_timestamp"] == ""
        assert rows[0]["planned_drop_lat"] == ""
        assert rows[0]["actual_drop_lat"] == ""

    def test_snapshot_includes_release_and_drop_result_fields(self) -> None:
        recorder = FlightRecorder(output_path="unused.csv", sample_rate_hz=10.0)
        ctx = self._make_context()
        ctx.release_triggered = True
        ctx.release_timestamp = 123.456
        ctx.planned_drop_point = (30.1001, 120.1002)
        ctx.drop_point_source = "vision"
        ctx.actual_drop_point = (30.2001, 120.2002)
        ctx.actual_drop_source = "vision"

        row = recorder._snapshot(ctx)

        assert row["release_triggered"] is True
        assert row["release_timestamp"] == 123.456
        assert row["planned_drop_lat"] == 30.1001
        assert row["planned_drop_lon"] == 120.1002
        assert row["planned_drop_source"] == "vision"
        assert row["actual_drop_lat"] == 30.2001
        assert row["actual_drop_lon"] == 120.2002
        assert row["actual_drop_source"] == "vision"

    def test_snapshot_keeps_actual_drop_fields_empty_without_confirmation(self) -> None:
        recorder = FlightRecorder(output_path="unused.csv", sample_rate_hz=10.0)
        ctx = self._make_context()
        ctx.release_triggered = True
        ctx.release_timestamp = 321.0
        ctx.planned_drop_point = (30.1001, 120.1002)
        ctx.drop_point_source = "fallback_midpoint"
        ctx.actual_drop_point = None
        ctx.actual_drop_source = ""

        row = recorder._snapshot(ctx)

        assert row["release_triggered"] is True
        assert row["release_timestamp"] == 321.0
        assert row["planned_drop_lat"] == 30.1001
        assert row["planned_drop_source"] == "fallback_midpoint"
        assert row["actual_drop_lat"] == ""
        assert row["actual_drop_lon"] == ""
        assert row["actual_drop_source"] == ""

    def test_auto_flush_on_stop(self, tmp_path: Path) -> None:
        output = tmp_path / "test_flight.csv"
        recorder = FlightRecorder(output_path=output)
        recorder._open_file()
        recorder._close_file()

        assert output.exists()

    def test_custom_output_directory(self, tmp_path: Path) -> None:
        nested = tmp_path / "subdir" / "logs" / "flight.csv"
        recorder = FlightRecorder(output_path=nested)
        recorder._open_file()
        recorder._close_file()
        assert nested.exists()

    def _make_context(self) -> MagicMock:
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
        ctx.release_triggered = False
        ctx.release_timestamp = None
        ctx.drop_point_source = ""
        ctx.planned_drop_point = None
        ctx.actual_drop_point = None
        ctx.actual_drop_source = ""
        return ctx
