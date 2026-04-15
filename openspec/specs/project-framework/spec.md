## ADDED Requirements

### Requirement: Project provides a package entry point
The system SHALL provide a runnable Python package entry point via `python -m striker` that prints the current version and exits cleanly.

#### Scenario: Running the package entry point
- **WHEN** a user executes `python -m striker`
- **THEN** the system prints the version string from `src/striker/__init__.__version__` to stdout and exits with code 0

#### Scenario: Version string is importable
- **WHEN** a caller imports `striker.__version__`
- **THEN** a non-empty string matching semantic versioning format (e.g. `0.1.0`) is returned

---

### Requirement: Package declares PEP 561 type marker
The system SHALL include a `py.typed` marker file in `src/striker/` to declare itself as a PEP 561 typed package.

#### Scenario: Type checker recognizes inline types
- **WHEN** `mypy` is invoked on code that imports from `striker`
- **THEN** `mypy` resolves type information from the package without requiring stubs

---

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

### Requirement: Source layout follows src-layout convention
The system SHALL use the `src/striker/` layout (PEP 517 src-layout) so that the package is not importable from the project root without installation.

#### Scenario: Package is not accidentally importable from project root
- **WHEN** a Python interpreter is launched from the project root directory without activating the virtual environment
- **THEN** `import striker` raises `ModuleNotFoundError`

#### Scenario: Package is importable after installation
- **WHEN** the package is installed via `uv sync` and the virtual environment is active
- **THEN** `import striker` succeeds

---

### Requirement: Project metadata is defined in pyproject.toml
The system SHALL declare project metadata (name, version, description, Python version requirement) in a single `pyproject.toml` file using the `[project]` table.

#### Scenario: pyproject.toml contains required metadata fields
- **WHEN** `pyproject.toml` is parsed
- **THEN** it contains `name = "striker"`, a `version` field, and `requires-python = ">=3.13"`

#### Scenario: Core runtime dependencies are declared
- **WHEN** `pyproject.toml` is parsed
- **THEN** the `[project.dependencies]` list includes `pymavlink`, `pydantic-settings`, and `structlog`

---

### Requirement: Config example template includes Phase 2 fields
The `config.example.json` file SHALL include all Phase 2 configuration fields with descriptive comments.

#### Scenario: Example config contains all fields
- **WHEN** `config.example.json` is parsed
- **THEN** it contains keys for: `serial_port`, `serial_baud`, `loiter_radius_m`, `loiter_timeout_s`, `max_scan_cycles`, `forced_strike_enabled`, `field`, `dry_run`, `log_level`
