## ADDED Requirements

### Requirement: structlog global configuration function
The system SHALL provide `configure_logging(level: str = "INFO")` in `src/striker/telemetry/logger.py` that configures structlog globally.

#### Scenario: Calling configure_logging sets up structlog
- **WHEN** `configure_logging()` is called
- **THEN** `structlog.is_configured()` returns `True`

#### Scenario: Configure with custom log level
- **WHEN** `configure_logging(level="DEBUG")` is called
- **THEN** DEBUG-level log messages are processed and output

---

### Requirement: TTY-aware renderer selection
The system SHALL automatically select `ConsoleRenderer` when stderr is a TTY (development) and `JSONRenderer` when stderr is not a TTY (production/SITL).

#### Scenario: TTY environment uses ConsoleRenderer
- **WHEN** `configure_logging()` is called and `sys.stderr.isatty()` returns `True`
- **THEN** log output is formatted using `ConsoleRenderer` (human-readable)

#### Scenario: Non-TTY environment uses JSONRenderer
- **WHEN** `configure_logging()` is called and `sys.stderr.isatty()` returns `False`
- **THEN** log output is formatted as JSON

---

### Requirement: Fixed processor chain
The system SHALL configure structlog with the following processor chain: `merge_contextvars` → `add_log_level` → `TimeStamper(fmt="iso", utc=True)` → `format_exc_info` → `dict_tracebacks` → Renderer.

#### Scenario: Log entries contain timestamp
- **WHEN** a log message is emitted after `configure_logging()`
- **THEN** the output includes an ISO 8601 UTC timestamp

#### Scenario: Log entries contain log level
- **WHEN** a log message is emitted at INFO level
- **THEN** the output includes the level indicator "info"

#### Scenario: Context variables are merged
- **WHEN** a context variable (e.g., `mission_id`) is bound via `structlog.contextvars`
- **THEN** subsequent log entries include that context variable in their output

---

### Requirement: All modules use structlog exclusively
The system SHALL use structlog as the only logging framework. No code in `src/striker/` SHALL import stdlib `logging` or use `print()`.

#### Scenario: Logger is obtained via structlog
- **WHEN** any module needs a logger
- **THEN** it calls `structlog.get_logger()` to obtain a bound logger instance

---

### Requirement: Cache logger on first use
The system SHALL configure structlog with `cache_logger_on_first_use=True` for performance.

#### Scenario: Logger configuration is cached
- **WHEN** `configure_logging()` is called
- **THEN** the `cache_logger_on_first_use` option is set to `True` in the structlog configuration
