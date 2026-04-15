## ADDED Requirements

### Requirement: Project Mission Statement
`CHARTER.md` SHALL contain a concise mission statement describing Striker's purpose as an autonomous fixed-wing drone flight control system for precision airdrop missions.

#### Scenario: Mission statement presence
- **WHEN** a developer or AI agent reads `CHARTER.md`
- **THEN** the file MUST contain a mission statement section within the first 10 lines

### Requirement: Project OKR Definition
`CHARTER.md` SHALL define Objectives and Key Results (OKR) for the Striker project, covering at minimum: flight safety, mission success rate, code quality, and autonomous operation reliability.

#### Scenario: OKR completeness
- **WHEN** `CHARTER.md` is reviewed
- **THEN** it MUST contain at least 3 Objectives, each with 2+ measurable Key Results

#### Scenario: OKR measurability
- **WHEN** a Key Result is defined
- **THEN** it MUST include a quantifiable metric or binary pass/fail criterion (e.g., "0 unhandled exceptions in flight", not "good error handling")

### Requirement: Red Lines Definition
`CHARTER.md` SHALL define exactly 10 inviolable Red Lines — safety and engineering constraints that MUST NOT be violated under any circumstance across all project phases.

#### Scenario: Red Lines count and coverage
- **WHEN** `CHARTER.md` is reviewed
- **THEN** it MUST contain exactly 10 numbered Red Lines covering: ARM safety, Safety Monitor persistence, Override finality, pymavlink encapsulation, GPS validation, no hardcoding, research-before-code, field profile validation, field profile schema enforcement, and forced-strike geofence safety

#### Scenario: Red Line referenceability
- **WHEN** a Red Line is defined
- **THEN** it MUST have a unique identifier (e.g., `RL-01` through `RL-10`) so downstream artifacts can reference it by ID

### Requirement: Charter Brevity
`CHARTER.md` MUST NOT exceed 80 lines of content (excluding blank lines), ensuring it remains a concise reference document rather than a sprawling manual.

#### Scenario: Line count validation
- **WHEN** `CHARTER.md` is authored
- **THEN** counting non-blank lines MUST yield ≤ 80
