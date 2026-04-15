## MODIFIED Requirements

### Requirement: Global exception hierarchy is defined
The system SHALL define a root exception class `StrikerError(Exception)` in `src/striker/exceptions.py`, along with categorized sub-classes covering configuration, communication, flight, safety, payload, and field validation domains.

#### Scenario: Catching all Striker exceptions
- **WHEN** any Striker-specific exception is raised
- **THEN** it is catchable via `except StrikerError`

#### Scenario: Exception sub-classes are importable
- **WHEN** a module imports `ConfigError`, `CommsError`, `FlightError`, `SafetyError`, `PayloadError`, or `FieldValidationError` from `striker.exceptions`
- **THEN** each is a subclass of `StrikerError`

#### Scenario: Exception instances carry descriptive messages
- **WHEN** a `StrikerError` subclass is instantiated with a message string
- **THEN** `str(error)` returns that message

#### Scenario: FieldValidationError carries field context
- **WHEN** a `FieldValidationError` is raised with a field name and reason
- **THEN** the error message includes both the field name and reason

---

## ADDED Requirements

### Requirement: Config example template includes Phase 2 fields
The `config.example.json` file SHALL include all Phase 2 configuration fields with descriptive comments.

#### Scenario: Example config contains all fields
- **WHEN** `config.example.json` is parsed
- **THEN** it contains keys for: `serial_port`, `serial_baud`, `loiter_radius_m`, `loiter_timeout_s`, `max_scan_cycles`, `forced_strike_enabled`, `field`, `dry_run`, `log_level`
