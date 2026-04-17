"""Flight-log analysis helpers for preserved optimization rounds."""

from __future__ import annotations

import csv
import math
from dataclasses import dataclass
from pathlib import Path

from striker.telemetry.optimization_rounds import OptimizationRoundPaths

TERMINAL_WINDOW_SIZE = 10


@dataclass(frozen=True)
class TerminalTelemetrySummary:
    sample_count: int
    min_relative_alt_m: float | None
    max_relative_alt_m: float | None
    min_groundspeed_mps: float | None
    max_groundspeed_mps: float | None
    min_airspeed_mps: float | None
    max_airspeed_mps: float | None
    max_abs_roll_deg: float | None
    max_abs_pitch_deg: float | None
    mode_values: tuple[str, ...]
    armed_values: tuple[str, ...]
    final_mode: str | None
    final_armed: str | None


@dataclass(frozen=True)
class FlightLogSummary:
    sample_count: int
    first_fix_line: int | None
    max_relative_alt_m: float | None
    final_relative_alt_m: float | None
    max_groundspeed_mps: float | None
    mode_values: tuple[str, ...]
    terminal_window: TerminalTelemetrySummary


@dataclass(frozen=True)
class StackMilestoneSummary:
    takeoff_detected: bool
    scan_complete_detected: bool
    release_detected: bool
    landing_detected: bool
    mission_completed: bool


def summarize_flight_log(path: str | Path) -> FlightLogSummary:
    """Summarize a preserved CSV flight log for round analysis."""
    with Path(path).open(encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        sample_count = 0
        first_fix_line: int | None = None
        max_relative_alt_m: float | None = None
        final_relative_alt_m: float | None = None
        max_groundspeed_mps: float | None = None
        mode_values: list[str] = []
        rows: list[dict[str, str]] = []

        for row in reader:
            rows.append(row)
            sample_count += 1
            if first_fix_line is None and row.get("lat") and row.get("lon"):
                first_fix_line = sample_count
            relative_alt = _parse_float(row.get("relative_alt_m", ""))
            if relative_alt is not None:
                max_relative_alt_m = relative_alt if max_relative_alt_m is None else max(max_relative_alt_m, relative_alt)
                final_relative_alt_m = relative_alt
            groundspeed = _parse_float(row.get("groundspeed_mps", ""))
            if groundspeed is not None:
                max_groundspeed_mps = groundspeed if max_groundspeed_mps is None else max(max_groundspeed_mps, groundspeed)
            mode = row.get("mode", "").strip()
            if mode and mode not in mode_values:
                mode_values.append(mode)

    return FlightLogSummary(
        sample_count=sample_count,
        first_fix_line=first_fix_line,
        max_relative_alt_m=max_relative_alt_m,
        final_relative_alt_m=final_relative_alt_m,
        max_groundspeed_mps=max_groundspeed_mps,
        mode_values=tuple(mode_values),
        terminal_window=_summarize_terminal_window(rows),
    )


def summarize_stack_milestones(striker_log_path: str | Path) -> StackMilestoneSummary:
    """Extract mission-phase milestone presence from a preserved striker log."""
    content = Path(striker_log_path).read_text(encoding="utf-8", errors="ignore")
    return StackMilestoneSummary(
        takeoff_detected="Target altitude reached" in content,
        scan_complete_detected="Scan complete" in content,
        release_detected="Payload released (native DO_SET_SERVO)" in content,
        landing_detected="Landing detected" in content,
        mission_completed="Mission completed successfully!" in content,
    )


def render_round_analysis(
    round_paths: OptimizationRoundPaths,
    flight_log_summary: FlightLogSummary,
    stack_summary: StackMilestoneSummary,
    *,
    software_hypothesis: str,
) -> str:
    """Render a persisted markdown analysis for one preserved round."""
    terminal = flight_log_summary.terminal_window
    return "\n".join([
        f"# Flight Log Analysis {round_paths.round_index}",
        "",
        "## Evidence",
        f"- Field: `{round_paths.field}`",
        f"- Raw run directory: `{round_paths.raw_run_dir}`",
        f"- Copied flight log: `{round_paths.copied_log_path.name}`",
        f"- Striker log: `{round_paths.raw_run_dir / 'striker.log'}`",
        "",
        "## Flight log summary",
        f"- Samples: {flight_log_summary.sample_count}",
        f"- First GPS fix row: {flight_log_summary.first_fix_line if flight_log_summary.first_fix_line is not None else 'not observed'}",
        f"- Max relative altitude (m): {_fmt_number(flight_log_summary.max_relative_alt_m)}",
        f"- Final relative altitude (m): {_fmt_number(flight_log_summary.final_relative_alt_m)}",
        f"- Max groundspeed (m/s): {_fmt_number(flight_log_summary.max_groundspeed_mps)}",
        f"- Observed modes: {', '.join(flight_log_summary.mode_values) if flight_log_summary.mode_values else 'none recorded'}",
        "",
        "## Terminal landing window telemetry",
        f"- Terminal window samples: {terminal.sample_count}",
        f"- Relative altitude range in terminal window (m): {_fmt_range(terminal.min_relative_alt_m, terminal.max_relative_alt_m)}",
        f"- Groundspeed range in terminal window (m/s): {_fmt_range(terminal.min_groundspeed_mps, terminal.max_groundspeed_mps)}",
        f"- Airspeed range in terminal window (m/s): {_fmt_range(terminal.min_airspeed_mps, terminal.max_airspeed_mps)}",
        f"- Max |roll| in terminal window (deg): {_fmt_number(terminal.max_abs_roll_deg)}",
        f"- Max |pitch| in terminal window (deg): {_fmt_number(terminal.max_abs_pitch_deg)}",
        f"- Terminal window modes: {', '.join(terminal.mode_values) if terminal.mode_values else 'none recorded'}",
        f"- Terminal window armed states: {', '.join(terminal.armed_values) if terminal.armed_values else 'none recorded'}",
        f"- Final mode in terminal window: {terminal.final_mode or 'not recorded'}",
        f"- Final armed state in terminal window: {terminal.final_armed or 'not recorded'}",
        "",
        "## Mission-phase correlation",
        f"- Takeoff milestone detected: {_yes_no(stack_summary.takeoff_detected)}",
        f"- Scan complete detected: {_yes_no(stack_summary.scan_complete_detected)}",
        f"- Release detected: {_yes_no(stack_summary.release_detected)}",
        f"- Landing detected: {_yes_no(stack_summary.landing_detected)}",
        f"- Mission completed: {_yes_no(stack_summary.mission_completed)}",
        "",
        "## Assessment",
        "- This round analysis is grounded in the preserved flight log plus Striker mission milestones.",
        "- Use it to judge takeoff, route tracking, strike handoff, and landing before the next software-only tuning change.",
        "- The terminal telemetry window reflects the last recorded samples before shutdown, so it is a better landing-quality signal than relying on the final relative-altitude row alone.",
        "",
        "## Next bounded software-side hypothesis",
        f"- {software_hypothesis}",
        "",
    ])


def _summarize_terminal_window(rows: list[dict[str, str]]) -> TerminalTelemetrySummary:
    telemetry_rows = [row for row in rows if _has_terminal_telemetry(row)]
    if not telemetry_rows:
        return TerminalTelemetrySummary(
            sample_count=0,
            min_relative_alt_m=None,
            max_relative_alt_m=None,
            min_groundspeed_mps=None,
            max_groundspeed_mps=None,
            min_airspeed_mps=None,
            max_airspeed_mps=None,
            max_abs_roll_deg=None,
            max_abs_pitch_deg=None,
            mode_values=(),
            armed_values=(),
            final_mode=None,
            final_armed=None,
        )

    terminal_rows = telemetry_rows[-TERMINAL_WINDOW_SIZE:]
    relative_alts = _parse_column(terminal_rows, "relative_alt_m")
    groundspeeds = _parse_column(terminal_rows, "groundspeed_mps")
    airspeeds = _parse_column(terminal_rows, "airspeed_mps")
    roll_degs = [math.degrees(abs(value)) for value in _parse_column(terminal_rows, "roll_rad")]
    pitch_degs = [math.degrees(abs(value)) for value in _parse_column(terminal_rows, "pitch_rad")]
    mode_values = _unique_non_empty(row.get("mode", "") for row in terminal_rows)
    armed_values = _unique_non_empty(row.get("armed", "") for row in terminal_rows)

    return TerminalTelemetrySummary(
        sample_count=len(terminal_rows),
        min_relative_alt_m=min(relative_alts) if relative_alts else None,
        max_relative_alt_m=max(relative_alts) if relative_alts else None,
        min_groundspeed_mps=min(groundspeeds) if groundspeeds else None,
        max_groundspeed_mps=max(groundspeeds) if groundspeeds else None,
        min_airspeed_mps=min(airspeeds) if airspeeds else None,
        max_airspeed_mps=max(airspeeds) if airspeeds else None,
        max_abs_roll_deg=max(roll_degs) if roll_degs else None,
        max_abs_pitch_deg=max(pitch_degs) if pitch_degs else None,
        mode_values=tuple(mode_values),
        armed_values=tuple(armed_values),
        final_mode=_last_non_empty(terminal_rows, "mode"),
        final_armed=_last_non_empty(terminal_rows, "armed"),
    )


def _has_terminal_telemetry(row: dict[str, str]) -> bool:
    return any(
        row.get(key, "").strip()
        for key in (
            "relative_alt_m",
            "groundspeed_mps",
            "airspeed_mps",
            "roll_rad",
            "pitch_rad",
            "mode",
            "armed",
        )
    )


def _parse_column(rows: list[dict[str, str]], key: str) -> list[float]:
    values: list[float] = []
    for row in rows:
        value = _parse_float(row.get(key, ""))
        if value is not None:
            values.append(value)
    return values


def _last_non_empty(rows: list[dict[str, str]], key: str) -> str | None:
    for row in reversed(rows):
        value = row.get(key, "").strip()
        if value:
            return value
    return None


def _unique_non_empty(values: list[str] | tuple[str, ...] | object) -> list[str]:
    unique: list[str] = []
    for raw_value in values:
        value = str(raw_value).strip()
        if value and value not in unique:
            unique.append(value)
    return unique


def _parse_float(value: str) -> float | None:
    stripped = value.strip()
    if not stripped:
        return None
    return float(stripped)


def _fmt_number(value: float | None) -> str:
    if value is None:
        return "not recorded"
    return f"{value:.2f}"


def _fmt_range(min_value: float | None, max_value: float | None) -> str:
    if min_value is None or max_value is None:
        return "not recorded"
    return f"{min_value:.2f}–{max_value:.2f}"


def _yes_no(value: bool) -> str:
    return "yes" if value else "no"
