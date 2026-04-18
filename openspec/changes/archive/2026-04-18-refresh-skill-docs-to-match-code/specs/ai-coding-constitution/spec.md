## ADDED Requirements

### Requirement: AGENTS.md SHALL delegate Skill routing to `SKILL_REGISTRY.md`
`AGENTS.md` MUST describe Skill loading through a compact bridge rule that points agents to `.agent/SKILL_REGISTRY.md` before touching source directories. It MUST NOT duplicate the full routing table inline once the registry file exists.

#### Scenario: Top-level constitution uses registry indirection
- **WHEN** `AGENTS.md` is reviewed for Skill loading guidance
- **THEN** it MUST direct the reader to `.agent/SKILL_REGISTRY.md`
- **AND** it MUST NOT contain a duplicated static module-to-Skill table
