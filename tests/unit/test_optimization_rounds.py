"""Unit tests for optimization round artifact retention."""

from __future__ import annotations

from pathlib import Path

import pytest

from striker.telemetry.optimization_rounds import preserve_round_artifacts, write_round_analysis


class TestOptimizationRounds:
    def test_preserve_round_artifacts_copies_raw_run_and_monotonic_log(self, tmp_path: Path) -> None:
        raw_run = tmp_path / "integration_runs" / "zjg-run-1"
        raw_run.mkdir(parents=True)
        (raw_run / "sitl.log").write_text("sitl ready\n", encoding="utf-8")
        (raw_run / "mavproxy.log").write_text("mavproxy ready\n", encoding="utf-8")
        (raw_run / "striker.log").write_text("mission complete\n", encoding="utf-8")
        (raw_run / "flight_log.csv").write_text("timestamp,lat\n1,30.3\n", encoding="utf-8")

        first = preserve_round_artifacts("zjg", raw_run, base_dir=tmp_path / "optimization_runs")
        second = preserve_round_artifacts("zjg", raw_run, base_dir=tmp_path / "optimization_runs")

        assert first.round_index == 1
        assert first.round_dir.name == "round_001"
        assert first.raw_run_dir.joinpath("sitl.log").exists()
        assert first.copied_log_path.name == "log_1.csv"
        assert first.copied_log_path.read_text(encoding="utf-8") == "timestamp,lat\n1,30.3\n"

        assert second.round_index == 2
        assert second.round_dir.name == "round_002"
        assert second.copied_log_path.name == "log_2.csv"
        assert first.copied_log_path.exists()

    def test_write_round_analysis_rejects_overwrite(self, tmp_path: Path) -> None:
        raw_run = tmp_path / "integration_runs" / "zjg-run-1"
        raw_run.mkdir(parents=True)
        (raw_run / "flight_log.csv").write_text("timestamp,lat\n1,30.3\n", encoding="utf-8")

        round_paths = preserve_round_artifacts("zjg", raw_run, base_dir=tmp_path / "optimization_runs")
        analysis_path = write_round_analysis(round_paths, "# Round 1\n")

        assert analysis_path.name == "flight_log_analysis_1.md"
        assert analysis_path.read_text(encoding="utf-8") == "# Round 1\n"

        with pytest.raises(FileExistsError):
            write_round_analysis(round_paths, "# Round 1 retry\n")

    def test_preserve_round_artifacts_requires_flight_log(self, tmp_path: Path) -> None:
        raw_run = tmp_path / "integration_runs" / "zjg-run-1"
        raw_run.mkdir(parents=True)

        with pytest.raises(FileNotFoundError, match="missing raw flight log"):
            preserve_round_artifacts("zjg", raw_run, base_dir=tmp_path / "optimization_runs")
