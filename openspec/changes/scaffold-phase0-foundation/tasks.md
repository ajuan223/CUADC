## 1. Project Initialization (uv + Python 3.13)

- [x] 1.1 Run `uv init --package ./` to initialize the project with src-layout
- [x] 1.2 Run `uv python pin 3.13` to create `.python-version` with content `3.13`
- [x] 1.3 Configure `pyproject.toml` `[project]` table: `name = "striker"`, `version = "0.1.0"`, `requires-python = ">=3.13"`, description

## 2. Dependencies

- [x] 2.1 Run `uv add pymavlink pydantic-settings structlog` to install core runtime dependencies
- [x] 2.2 Run `uv add --dev ruff mypy pytest pytest-asyncio` to install dev-only dependencies
- [x] 2.3 Verify `[project.dependencies]` contains pymavlink, pydantic-settings, structlog and `[dependency-groups]` dev group contains ruff, mypy, pytest, pytest-asyncio

## 3. Source Package Skeleton

- [x] 3.1 Create `src/striker/__init__.py` with `__version__ = "0.1.0"`
- [x] 3.2 Create `src/striker/__main__.py` that prints version and exits (entry point for `python -m striker`)
- [x] 3.3 Create `src/striker/py.typed` empty marker file (PEP 561)
- [x] 3.4 Create `src/striker/exceptions.py` with `StrikerError(Exception)` base class and sub-classes: `ConfigError`, `CommsError`, `FlightError`, `SafetyError`, `PayloadError`

## 4. Test Scaffold

- [x] 4.1 Create `tests/__init__.py` (empty)
- [x] 4.2 Create `tests/conftest.py` with pytest fixtures skeleton (empty or minimal)

## 5. Toolchain Configuration (pyproject.toml)

- [x] 5.1 Add `[tool.ruff]` section: `target-version = "py313"`, selected rule codes (E, F, I, W), `[tool.ruff.lint]` select
- [x] 5.2 Add `[tool.mypy]` section: `strict = true`, `python_version = "3.13"`
- [x] 5.3 Add `[tool.pytest.ini_options]` section: `asyncio_mode = "auto"`, test paths
- [x] 5.4 Add `[tool.uv.workspace]` section: `members = ["pkg/*"]`

## 6. Workspace & Directory Scaffold

- [x] 6.1 Create `pkg/README.md` explaining workspace isolation rules and how to add internal packages
- [x] 6.2 Create `pkg/.gitkeep`
- [x] 6.3 Create `runtime_data/.gitkeep`
- [x] 6.4 Create `docs/.gitkeep`
- [x] 6.5 Create `scripts/.gitkeep`

## 7. Field Configuration Template

- [x] 7.1 Create `data/fields/sitl_default/field.json` with placeholder SITL field profile (boundary polygon, landing params, scan waypoints)
- [x] 7.2 Create `data/fields/README.md` explaining how to create new field configurations

## 8. Engineering Files

- [x] 8.1 Update `.gitignore` to cover `__pycache__/`, `.venv/`, `runtime_data/`, `config.json`, `*.pyc`, `.env`, `uv.lock` patterns
- [x] 8.2 Create `README.md` with project name, description, prerequisites, and basic usage
- [x] 8.3 Create `.env.example` with `STRIKER_` prefixed environment variable placeholders
- [x] 8.4 Create `config.example.json` with configuration template matching future StrikerSettings schema

## 9. Verification

- [x] 9.1 Run `uv sync` — must succeed
- [x] 9.2 Run `uv run python -m striker` — must print version and exit 0
- [x] 9.3 Run `uv run ruff check .` — must pass with zero violations
- [x] 9.4 Run `uv run mypy src/ --strict` — must pass with zero errors
- [x] 9.5 Run `uv run pytest` — must run without errors (0 tests collected OK)
- [x] 9.6 Run `uv run python -c "from striker.exceptions import StrikerError, ConfigError, CommsError, FlightError, SafetyError, PayloadError; print('OK')"` — must print OK
