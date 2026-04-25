## ADDED Requirements

### Requirement: Obsolete specifications shall be marked
All specifications relating to the legacy `INIT → PREFLIGHT → TAKEOFF → SCAN → ENROUTE` state chain and the procedural mission geometry generation SHALL be explicitly marked as obsolete.

#### Scenario: Agent or developer reviews legacy specs
- **WHEN** an AI agent or a developer reads a deprecated specification like `procedural-mission-geometry/spec.md`
- **THEN** they MUST see a prominent `**Status: Obsolete/Replaced**` block at the top of the file warning them that the concepts are replaced by the `preburned-mission-refactor`.
