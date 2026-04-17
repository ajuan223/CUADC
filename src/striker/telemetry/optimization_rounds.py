"""Optimization round artifact retention helpers."""

from __future__ import annotations

import re
import shutil
from dataclasses import dataclass
from pathlib import Path

ROUND_DIR_PATTERN = re.compile(r"^round_(\d{3,})$")
DEFAULT_OPTIMIZATION_ROOT = Path("runtime_data/optimization_runs")
RAW_RUN_DIRNAME = "raw_run"
RAW_FLIGHT_LOG_NAME = "flight_log.csv"


@dataclass(frozen=True)
class OptimizationRoundPaths:
    """Filesystem layout for one preserved optimization round."""

    field: str
    round_index: int
    field_root: Path
    round_dir: Path
    raw_run_dir: Path
    copied_log_path: Path
    analysis_path: Path


def optimization_field_root(field: str, *, base_dir: Path = DEFAULT_OPTIMIZATION_ROOT) -> Path:
    return Path(base_dir) / field


def reserve_round_paths(field: str, *, base_dir: Path = DEFAULT_OPTIMIZATION_ROOT) -> OptimizationRoundPaths:
    """Reserve the next monotonic round directory for *field*."""
    field_root = optimization_field_root(field, base_dir=base_dir)
    field_root.mkdir(parents=True, exist_ok=True)

    round_index = _next_round_index(field_root)
    round_dir = field_root / f"round_{round_index:03d}"
    round_dir.mkdir()

    return OptimizationRoundPaths(
        field=field,
        round_index=round_index,
        field_root=field_root,
        round_dir=round_dir,
        raw_run_dir=round_dir / RAW_RUN_DIRNAME,
        copied_log_path=round_dir / f"log_{round_index}.csv",
        analysis_path=round_dir / f"flight_log_analysis_{round_index}.md",
    )


def preserve_round_artifacts(
    field: str,
    source_run_dir: str | Path,
    *,
    base_dir: Path = DEFAULT_OPTIMIZATION_ROOT,
) -> OptimizationRoundPaths:
    """Copy one raw run directory into the next preserved optimization round."""
    source_path = Path(source_run_dir)
    if not source_path.is_dir():
        raise FileNotFoundError(f"raw run directory not found: {source_path}")

    source_flight_log = source_path / RAW_FLIGHT_LOG_NAME
    if not source_flight_log.exists():
        raise FileNotFoundError(f"missing raw flight log: {source_flight_log}")

    round_paths = reserve_round_paths(field, base_dir=base_dir)
    shutil.copytree(source_path, round_paths.raw_run_dir)
    shutil.copy2(source_flight_log, round_paths.copied_log_path)
    return round_paths


def write_round_analysis(round_paths: OptimizationRoundPaths, content: str) -> Path:
    """Write the round analysis file exactly once."""
    if round_paths.analysis_path.exists():
        raise FileExistsError(f"analysis already exists: {round_paths.analysis_path}")
    round_paths.analysis_path.write_text(content, encoding="utf-8")
    return round_paths.analysis_path


def _next_round_index(field_root: Path) -> int:
    max_index = 0
    for child in field_root.iterdir():
        if not child.is_dir():
            continue
        match = ROUND_DIR_PATTERN.fullmatch(child.name)
        if match is None:
            continue
        max_index = max(max_index, int(match.group(1)))
    return max_index + 1
