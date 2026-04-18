## ADDED Requirements

### Requirement: Module Skills SHALL align with the current codebase, not archived planning states
Every active `.agent/skills/*/SKILL.md` file MUST describe the current code structure, data fields, script behavior, and state flow that exist in the repository. Skills MUST remove stale references once the corresponding runtime or tooling behavior no longer exists.

#### Scenario: Skills do not preserve stale planning-only behavior
- **WHEN** a module Skill is reviewed against the current repository
- **THEN** it MUST match active files, active states, and active field names
- **AND** it MUST NOT preserve superseded behavior solely because it existed in an earlier planning round

### Requirement: `testing-rules` SHALL reflect current generic testing boundaries
`testing-rules/SKILL.md` MUST describe the project's current testing split without treating ballistic solver or KAT coverage as a universal hard rule for all test work.

#### Scenario: Testing skill avoids stale ballistic-only constraints
- **WHEN** `testing-rules/SKILL.md` is read
- **THEN** it MUST describe unit and integration testing boundaries in terms of current modules and fixtures
- **AND** it MUST NOT require ballistic-solver-specific KAT or anti-mock rules as a generic repository-wide mandate

### Requirement: `sitl-param-merge-rules` SHALL avoid hard-coding a single field output path
`sitl-param-merge-rules/SKILL.md` MUST describe merged parameter outputs in a field-aware or workflow-aware way. It MUST NOT claim that all merged outputs are always written to `data/fields/sitl_default/sitl_merged.param`.

#### Scenario: SITL param merge skill is field-aware
- **WHEN** `sitl-param-merge-rules/SKILL.md` is read
- **THEN** it MUST describe parameter merge outputs without pinning every workflow to `sitl_default`
- **AND** it MUST stay consistent with the current field-profile-based SITL launch model

### Requirement: `sitl-autodebug-loop` SHALL reflect the current launcher and artifact flow
`sitl-autodebug-loop/SKILL.md` MUST describe the current `scripts/run_sitl.sh` responsibilities and the actual artifact paths used in the debug loop.

#### Scenario: SITL autodebug skill matches launcher behavior
- **WHEN** `sitl-autodebug-loop/SKILL.md` is read
- **THEN** it MUST match the current launcher chain and artifact outputs
- **AND** it MUST NOT assume a pre-launch sequence that contradicts the current `run_sitl.sh`
