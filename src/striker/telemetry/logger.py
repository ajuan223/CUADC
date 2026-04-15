"""Structlog global configuration for Striker.

- TTY (development) → ``ConsoleRenderer`` (human-readable)
- Non-TTY (production / SITL) → ``JSONRenderer`` (machine-parseable)
- Processor chain: ``merge_contextvars`` → ``add_log_level`` → ``TimeStamper``
  → ``format_exc_info`` → ``dict_tracebacks`` → Renderer
"""

import logging
import sys

import structlog


def configure_logging(level: str = "INFO") -> None:
    """Configure structlog globally.

    Parameters
    ----------
    level:
        Minimum log level to emit (e.g. ``"DEBUG"``, ``"INFO"``).
        Mapped to :mod:`logging` integer levels internally.
    """
    log_level = getattr(logging, level.upper(), logging.INFO)

    shared_processors: list[structlog.types.Processor] = [
        structlog.contextvars.merge_contextvars,
        structlog.processors.add_log_level,
        structlog.processors.TimeStamper(fmt="iso", utc=True),
        structlog.processors.format_exc_info,
        structlog.processors.dict_tracebacks,
    ]

    if sys.stderr.isatty():
        renderer: structlog.types.Processor = structlog.dev.ConsoleRenderer()
    else:
        renderer = structlog.processors.JSONRenderer()

    structlog.configure(
        processors=[*shared_processors, renderer],
        wrapper_class=structlog.make_filtering_bound_logger(log_level),
        context_class=dict,
        logger_factory=structlog.PrintLoggerFactory(),
        cache_logger_on_first_use=True,
    )
