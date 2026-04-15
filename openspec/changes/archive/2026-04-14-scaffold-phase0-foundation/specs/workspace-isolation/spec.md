## ADDED Requirements

### Requirement: UV workspace is configured with pkg/ member path
The system SHALL configure `uv` workspace in the root `pyproject.toml` with `members = ["pkg/*"]`, establishing a monorepo-style isolation boundary for future internal library packages.

#### Scenario: Workspace configuration exists
- **WHEN** `pyproject.toml` is inspected
- **THEN** a `[tool.uv.workspace]` section is present with `members = ["pkg/*"]`

#### Scenario: uv sync succeeds with workspace configured
- **WHEN** `uv sync` is executed in the project root
- **THEN** the command exits with code 0 and the virtual environment is created/updated successfully

---

### Requirement: pkg/ directory scaffold exists with documentation
The system SHALL create a `pkg/` directory containing a `README.md` that explains the workspace isolation strategy and rules for adding internal packages, plus a `.gitkeep` to ensure the directory is tracked by git.

#### Scenario: pkg/ directory is tracked by git
- **WHEN** the repository is inspected
- **THEN** `pkg/` directory exists and contains at least `.gitkeep` and `README.md`

#### Scenario: pkg/README.md explains isolation rules
- **WHEN** `pkg/README.md` is read
- **THEN** it contains guidance on: the purpose of the workspace, how to add a new internal package, and the prohibition against circular dependencies between `src/` and `pkg/`

---

### Requirement: Project scaffold includes runtime_data directory
The system SHALL create a `runtime_data/` directory with a `.gitkeep` file, and the directory MUST be listed in `.gitignore` (except for `.gitkeep`) so that runtime artifacts are never committed.

#### Scenario: runtime_data/ exists but contents are gitignored
- **WHEN** the repository is inspected
- **THEN** `runtime_data/.gitkeep` exists AND `.gitignore` contains a rule for `runtime_data/`

---

### Requirement: Project scaffold includes docs and scripts directories
The system SHALL create `docs/` and `scripts/` skeleton directories with `.gitkeep` files to establish the project's documentation and automation layout.

#### Scenario: docs/ directory exists
- **WHEN** the repository is inspected
- **THEN** `docs/` directory exists and contains at least a `.gitkeep` file

#### Scenario: scripts/ directory exists
- **WHEN** the repository is inspected
- **THEN** `scripts/` directory exists and contains at least a `.gitkeep` file

---

### Requirement: Field configuration template directory exists
The system SHALL create `data/fields/sitl_default/field.json` as a SITL default field profile template, and `data/fields/README.md` explaining how to create new field configurations.

#### Scenario: SITL default field profile template exists
- **WHEN** `data/fields/sitl_default/field.json` is inspected
- **THEN** it contains a valid JSON object with placeholder field profile structure (boundary polygon, landing parameters, scan waypoints)

#### Scenario: Field configuration guide exists
- **WHEN** `data/fields/README.md` is read
- **THEN** it explains how to create a new field configuration by copying the `sitl_default` template

---

### Requirement: Project engineering files are present
The system SHALL include `.gitignore` (covering Python, uv, runtime_data, config.json), `README.md` (project overview), `.env.example` (environment variable template), and `config.example.json` (configuration template).

#### Scenario: .gitignore covers required patterns
- **WHEN** `.gitignore` is inspected
- **THEN** it includes rules for `__pycache__/`, `.venv/`, `runtime_data/`, `config.json`, `*.pyc`, and `.env`

#### Scenario: README.md provides project overview
- **WHEN** `README.md` is read
- **THEN** it contains the project name, a brief description, and basic usage instructions

#### Scenario: Environment and config templates exist
- **WHEN** the project root is inspected
- **THEN** `.env.example` and `config.example.json` files are present with placeholder values

---

### Requirement: Python version is pinned to 3.13
The system SHALL include a `.python-version` file containing `3.13` to ensure all tooling (uv, IDE, CI) uses the correct interpreter version.

#### Scenario: .python-version specifies 3.13
- **WHEN** `.python-version` is read
- **THEN** its content is exactly `3.13`
