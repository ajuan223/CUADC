"""Striker telemetry — structlog structured logging + flight recording."""

from striker.telemetry.flight_log_analysis import (
    FlightLogSummary,
    StackMilestoneSummary,
    render_round_analysis,
    summarize_flight_log,
    summarize_stack_milestones,
)
from striker.telemetry.flight_recorder import FlightRecorder
from striker.telemetry.logger import configure_logging
from striker.telemetry.optimization_rounds import (
    DEFAULT_OPTIMIZATION_ROOT,
    OptimizationRoundPaths,
    optimization_field_root,
    preserve_round_artifacts,
    reserve_round_paths,
    write_round_analysis,
)

__all__ = [
    "DEFAULT_OPTIMIZATION_ROOT",
    "FlightLogSummary",
    "FlightRecorder",
    "OptimizationRoundPaths",
    "StackMilestoneSummary",
    "configure_logging",
    "optimization_field_root",
    "preserve_round_artifacts",
    "render_round_analysis",
    "reserve_round_paths",
    "summarize_flight_log",
    "summarize_stack_milestones",
    "write_round_analysis",
]
