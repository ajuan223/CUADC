## ADDED Requirements

### Requirement: Ruff is configured for linting and formatting
The system SHALL configure `ruff` in `pyproject.toml` with a rule set that enforces code style, import sorting, and basic error detection. The empty project skeleton SHALL pass `ruff check .` with zero violations.

#### Scenario: Ruff check passes on clean project
- **WHEN** `uv run ruff check .` is executed in the project root
- **THEN** the command exits with code 0 and reports no violations

#### Scenario: Ruff configuration exists in pyproject.toml
- **WHEN** `pyproject.toml` is inspected
- **THEN** a `[tool.ruff]` section is present with at minimum `target-version = "py313"` and selected rule codes

#### Scenario: Ruff detects intentional violation
- **WHEN** a Python file containing an unused import is checked by ruff
- **THEN** ruff reports an `F401` violation

---

### Requirement: Mypy is configured for strict type checking
The system SHALL configure `mypy` in `pyproject.toml` with strict mode settings. The empty project skeleton SHALL pass `mypy src/ --strict` with zero errors.

#### Scenario: Mypy strict check passes on clean project
- **WHEN** `uv run mypy src/ --strict` is executed
- **THEN** the command exits with code 0 and reports "Success: no issues found"

#### Scenario: Mypy configuration exists in pyproject.toml
- **WHEN** `pyproject.toml` is inspected
- **THEN** a `[tool.mypy]` section is present with `strict = true` and `python_version = "3.13"`

---

### Requirement: Pytest is configured with asyncio support
The system SHALL configure `pytest` in `pyproject.toml` with `pytest-asyncio` support. The test scaffold (`tests/conftest.py`, `tests/__init__.py`) SHALL be in place and `pytest` SHALL run successfully even with zero collected tests.

#### Scenario: Pytest runs with zero tests collected
- **WHEN** `uv run pytest` is executed
- **THEN** the command exits with code 0 (or code 5 for "no tests collected") and does not error out

#### Scenario: Pytest configuration exists in pyproject.toml
- **WHEN** `pyproject.toml` is inspected
- **THEN** a `[tool.pytest.ini_options]` section is present with `asyncio_mode = "auto"` configured

#### Scenario: Test directory scaffold exists
- **WHEN** the `tests/` directory is inspected
- **THEN** it contains `__init__.py` and `conftest.py` files

#### Scenario: Async tests are supported
- **WHEN** an async test function decorated with `@pytest.mark.asyncio` is added to the test suite
- **THEN** `pytest` discovers and runs it without additional configuration

---

### Requirement: Development dependencies are isolated from runtime
The system SHALL declare `ruff`, `mypy`, `pytest`, and `pytest-asyncio` as development-only dependencies in `pyproject.toml`, separate from runtime dependencies.

#### Scenario: Dev dependencies are in dev group
- **WHEN** `pyproject.toml` is inspected
- **THEN** `ruff`, `mypy`, `pytest`, and `pytest-asyncio` appear under `[dependency-groups]` dev group, NOT in `[project.dependencies]`

#### Scenario: Runtime install does not include dev tools
- **WHEN** the package is installed without the dev group (e.g. `uv sync --no-dev`)
- **THEN** `ruff`, `mypy`, and `pytest` are NOT available in the environment
