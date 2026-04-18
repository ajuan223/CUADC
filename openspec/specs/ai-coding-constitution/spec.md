## Purpose

Define the top-level AI coding constitution for the repository, including global instruction limits, mandatory coding rules, and the entry point for module-level Skill loading.
## Requirements
### Requirement: AGENTS.md SHALL delegate Skill routing to `SKILL_REGISTRY.md`
`AGENTS.md` MUST describe Skill loading through a compact bridge rule that points agents to `.agent/SKILL_REGISTRY.md` before touching source directories. It MUST NOT duplicate the full routing table inline once the registry file exists.

#### Scenario: Top-level constitution uses registry indirection
- **WHEN** `AGENTS.md` is reviewed for Skill loading guidance
- **THEN** it MUST direct the reader to `.agent/SKILL_REGISTRY.md`
- **AND** it MUST NOT contain a duplicated static module-to-Skill table

## ADDED Requirements

### Requirement: Instruction Budget Constraint
`AGENTS.md` MUST contain fewer than 100 lines of effective instructions (blank lines, horizontal rules, and comment-only lines are excluded from the count).

#### Scenario: Line budget enforcement
- **WHEN** `AGENTS.md` is authored or modified
- **THEN** counting effective instruction lines (non-blank, non-comment, non-rule lines) MUST yield < 100

#### Scenario: Budget overflow rejection
- **WHEN** a proposed edit to `AGENTS.md` would cause effective lines ≥ 100
- **THEN** the edit MUST be rejected, and the content MUST be moved to an L2 module Skill instead

### Requirement: Naming Convention Rules
`AGENTS.md` SHALL define mandatory naming conventions covering: module names (snake_case), class names (PascalCase), constants (UPPER_SNAKE_CASE), and file names (snake_case.py).

#### Scenario: Naming convention completeness
- **WHEN** `AGENTS.md` is reviewed
- **THEN** it MUST specify conventions for modules, classes, constants, and files with concrete examples

### Requirement: Type Annotation Enforcement
`AGENTS.md` SHALL mandate `mypy --strict` compliance for all Python source code under `src/striker/`.

#### Scenario: Type strictness rule
- **WHEN** an AI agent writes new Python code
- **THEN** all functions MUST have fully annotated parameters and return types, all variables MUST have type annotations where inference is insufficient

### Requirement: Import Order Specification
`AGENTS.md` SHALL define a three-section import order: (1) stdlib, (2) third-party, (3) local — separated by blank lines, with `ruff` I-sorting enforced.

#### Scenario: Import order compliance
- **WHEN** an AI agent writes or modifies imports
- **THEN** imports MUST follow the three-section order and pass `ruff check --select I`

### Requirement: Logging Standard
`AGENTS.md` SHALL mandate `structlog` as the sole logging mechanism. `print()` statements and stdlib `logging` direct usage are FORBIDDEN in production code.

#### Scenario: Logging compliance
- **WHEN** an AI agent adds log output
- **THEN** it MUST use `structlog.get_logger()` or `structlog.stdlib.get_logger()`, never `print()` or `logging.getLogger()`

#### Scenario: Debug print exception
- **WHEN** code is in `tests/` directory
- **THEN** `print()` is permitted for test debugging purposes only

### Requirement: Skill Routing Table
`AGENTS.md` SHALL contain a static routing table mapping `src/striker/{module}/` directory patterns to their corresponding `.agent/skills/{module}-rules/SKILL.md` files.

#### Scenario: Routing table completeness
- **WHEN** `AGENTS.md` is reviewed
- **THEN** the routing table MUST cover all planned modules: `core/`, `comms/`, `flight/`, `safety/`, `vision/`, `payload/`, `config/`, `telemetry/`, `utils/`

#### Scenario: Routing table format
- **WHEN** an AI agent touches files in `src/striker/{module}/`
- **THEN** the routing table MUST indicate which Skill to load, using a compact markdown table format

### Requirement: Research-Before-Code Rule
`AGENTS.md` SHALL mandate that AI agents MUST perform code search and architecture research before creating or modifying any module. Blind code generation is FORBIDDEN.

#### Scenario: New module creation
- **WHEN** an AI agent is asked to create a new module under `src/striker/`
- **THEN** the agent MUST first search for existing related code, check `REGISTRY.md`, and review the module's Skill before writing any implementation

### Requirement: Capability Discovery Rule
`AGENTS.md` SHALL mandate checking `.agent/skills/capability-registry/REGISTRY.md` before implementing any utility function, to prevent reinventing existing capabilities.

#### Scenario: Utility function creation
- **WHEN** an AI agent needs a common utility (e.g., coordinate conversion, timing, validation)
- **THEN** it MUST first query `REGISTRY.md` and reuse existing entries before writing new code

### Requirement: Package Governance Anti-Corruption Wall
`AGENTS.md` SHALL define strict rules for `pkg/` workspace packages: version bumps on every change, `REGISTRY.md` synchronization, and absolute prohibition of bidirectional dependencies between `src/` ↔ `pkg/` or `pkg/` ↔ `pkg/`.

#### Scenario: Package modification
- **WHEN** an AI agent modifies a package in `pkg/{name}/`
- **THEN** it MUST bump the version in `pkg/{name}/pyproject.toml` AND update `REGISTRY.md`

#### Scenario: Circular dependency prevention
- **WHEN** an AI agent adds an import in `pkg/{a}/`
- **THEN** any import path MUST NOT resolve to `src/striker/` or another `pkg/{b}/` package

### Requirement: AGENTS.local.md Override Template
An `AGENTS.local.md` file SHALL be provided as an empty template with header comments explaining the override mechanism. It MUST be listed in `.gitignore`.

#### Scenario: Local override file existence
- **WHEN** the project is cloned
- **THEN** `AGENTS.local.md` MUST NOT exist (gitignored), but its template structure MUST be documented in `AGENTS.md` or as a committed example

#### Scenario: Override scope limitation
- **WHEN** a developer creates `AGENTS.local.md`
- **THEN** it MAY override style preferences (indent width, line length) but MUST NOT override Red Lines (RL-01 through RL-10) or safety rules

### Requirement: Rule Identifier Format
Every rule in `AGENTS.md` SHALL be assigned a unique identifier in the format `R{NN}` (e.g., `R01`, `R02`, ...) for cross-referencing from L2 Skills and task descriptions.

#### Scenario: Rule referenceability
- **WHEN** an L2 Skill references a top-level rule
- **THEN** it MUST use the `R{NN}` identifier, and the identifier MUST resolve to exactly one rule in `AGENTS.md`
