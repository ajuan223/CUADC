## ADDED Requirements

### Requirement: PEP 561 py.typed marker file exists
The system SHALL include an empty `src/striker/py.typed` file declaring PEP 561 type support.

#### Scenario: Type checker recognizes inline types
- **WHEN** `mypy` is invoked on code that imports from `striker`
- **THEN** `mypy` resolves type information from the package without requiring stubs

#### Scenario: py.typed file exists in source tree
- **WHEN** checking `src/striker/py.typed`
- **THEN** the file exists (may be empty)

### Requirement: Environment variable example template exists
The system SHALL include a `.env.example` file listing all supported `STRIKER_*` environment variables with their default values as comments.

#### Scenario: All config fields have corresponding env var entries
- **WHEN** `.env.example` is parsed
- **THEN** it contains entries for `STRIKER_SERIAL_PORT`, `STRIKER_SERIAL_BAUD`, `STRIKER_TRANSPORT`, `STRIKER_FIELD`, `STRIKER_DRY_RUN`, `STRIKER_LOG_LEVEL`

### Requirement: pkg/ workspace directory skeleton exists
The system SHALL include a `pkg/` directory with `pkg/README.md` (explaining its purpose) and `pkg/.gitkeep` to ensure the empty directory is tracked by git.

#### Scenario: pkg directory is tracked by git
- **WHEN** `git status` is run
- **THEN** `pkg/` directory is visible (not untracked)

#### Scenario: pkg README explains workspace rules
- **WHEN** `pkg/README.md` is read
- **THEN** it describes that pkg/ is for vendor/frozen packages and the uv workspace membership rules
