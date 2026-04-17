"""Unit tests for preserved flight-log analysis."""

from __future__ import annotations

from pathlib import Path

import pytest

from striker.telemetry.flight_log_analysis import (
    render_round_analysis,
    summarize_flight_log,
    summarize_stack_milestones,
)
from striker.telemetry.optimization_rounds import preserve_round_artifacts


class TestFlightLogAnalysis:
    def test_summarize_flight_log_reads_enriched_columns(self, tmp_path: Path) -> None:
        flight_log = tmp_path / "flight_log.csv"
        flight_log.write_text(
            "timestamp,lat,lon,alt_m,relative_alt_m,roll_rad,pitch_rad,yaw_rad,airspeed_mps,groundspeed_mps,battery_voltage_v,battery_remaining_pct,mode,armed\n"
            "1,,,,,,,,,,,,,\n"
            "2,30.30,120.07,100,40,0.1,0.2,0.3,18.5,17.2,12.1,87,AUTO,True\n"
            "3,30.31,120.08,90,15,0.0,0.1,0.2,16.0,14.5,11.9,83,MANUAL,False\n",
            encoding="utf-8",
        )

        summary = summarize_flight_log(flight_log)

        assert summary.sample_count == 3
        assert summary.first_fix_line == 2
        assert summary.max_relative_alt_m == 40.0
        assert summary.final_relative_alt_m == 15.0
        assert summary.max_groundspeed_mps == 17.2
        assert summary.mode_values == ("AUTO", "MANUAL")
        assert summary.terminal_window.sample_count == 2
        assert summary.terminal_window.min_relative_alt_m == 15.0
        assert summary.terminal_window.max_relative_alt_m == 40.0
        assert summary.terminal_window.min_groundspeed_mps == 14.5
        assert summary.terminal_window.max_groundspeed_mps == 17.2
        assert summary.terminal_window.min_airspeed_mps == 16.0
        assert summary.terminal_window.max_airspeed_mps == 18.5
        assert summary.terminal_window.max_abs_roll_deg == pytest.approx(5.73, abs=0.01)
        assert summary.terminal_window.max_abs_pitch_deg == pytest.approx(11.46, abs=0.01)
        assert summary.terminal_window.mode_values == ("AUTO", "MANUAL")
        assert summary.terminal_window.armed_values == ("True", "False")
        assert summary.terminal_window.final_mode == "MANUAL"
        assert summary.terminal_window.final_armed == "False"

    def test_render_round_analysis_links_preserved_artifacts(self, tmp_path: Path) -> None:
        raw_run = tmp_path / "integration_runs" / "zjg-run-1"
        raw_run.mkdir(parents=True)
        (raw_run / "flight_log.csv").write_text(
            "timestamp,lat,lon,alt_m,relative_alt_m,roll_rad,pitch_rad,yaw_rad,airspeed_mps,groundspeed_mps,battery_voltage_v,battery_remaining_pct,mode,armed\n"
            "1,30.30,120.07,100,40,0.1,0.2,0.3,18.5,17.2,12.1,87,AUTO,True\n",
            encoding="utf-8",
        )
        (raw_run / "striker.log").write_text(
            (
                "Target altitude reached\n"
                "Scan complete\n"
                "Payload released (native DO_SET_SERVO)\n"
                "Landing detected\n"
                "Mission completed successfully!\n"
            ),
            encoding="utf-8",
        )
        (raw_run / "sitl.log").write_text("sitl ok\n", encoding="utf-8")
        (raw_run / "mavproxy.log").write_text("mavproxy ok\n", encoding="utf-8")

        round_paths = preserve_round_artifacts("zjg", raw_run, base_dir=tmp_path / "optimization_runs")
        flight_summary = summarize_flight_log(round_paths.copied_log_path)
        stack_summary = summarize_stack_milestones(round_paths.raw_run_dir / "striker.log")
        content = render_round_analysis(
            round_paths,
            flight_summary,
            stack_summary,
            software_hypothesis="Reduce attack exit aggressiveness before the next rerun.",
        )

        assert "# Flight Log Analysis 1" in content
        assert "`log_1.csv`" in content
        assert "## Terminal landing window telemetry" in content
        assert "Groundspeed range in terminal window (m/s): 17.20-17.20" in content
        assert "Takeoff milestone detected: yes" in content
        assert "Mission completed: yes" in content
        assert "Reduce attack exit aggressiveness" in content
        assert "better landing-quality signal" in content
