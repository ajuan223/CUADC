# skill-registry-routing Specification

## Purpose
TBD - created by archiving change refresh-skill-docs-to-match-code. Update Purpose after archive.
## Requirements
### Requirement: Skill routing SHALL use `SKILL_REGISTRY.md` as the single entry point
The repository SHALL define `.agent/SKILL_REGISTRY.md` as the single routing index for module and workflow Skill loading. The file SHALL describe which Skill applies to each source area and workflow domain.

#### Scenario: Skill routing index exists
- **WHEN** the repository is inspected for the Skill routing source of truth
- **THEN** `.agent/SKILL_REGISTRY.md` MUST exist
- **AND** it MUST enumerate the active Skill directories used by the project

### Requirement: Skill routing SHALL be named distinctly from capability registry
The Skill routing index MUST NOT share the same filename as the capability discovery registry under `.agent/skills/capability-registry/REGISTRY.md`.

#### Scenario: Routing index and capability registry are distinguishable
- **WHEN** an agent or developer looks for the Skill routing entry point and the reusable capability registry
- **THEN** the Skill routing file MUST be named `.agent/SKILL_REGISTRY.md`
- **AND** the capability registry MUST remain under `.agent/skills/capability-registry/REGISTRY.md`

