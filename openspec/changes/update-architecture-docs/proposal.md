## Why

The project recently underwent a massive architectural pivot (`preburned-mission-refactor` followed by the `GUIDED_STRIKE` DO_REPOSITION mechanism). This pivot completely ripped out the "Field-driven Procedural Mission Generation" and replaced it with a "Preburned Mission + GUIDED Takeover" architecture.

However, the main root and `/docs` markdown documentation files (`user_manual.md`, `init愿景.md`, `sitl_setup.md`, `data/fields/README.md`) are completely trapped in the obsolete architecture. They still heavily pitch and describe the obsolete programmatic takeoff/scan/landing generation, and list the outdated `INIT → PREFLIGHT → TAKEOFF...` state chain. This causes a severe cognitive disconnect for developers and AI agents reading the repository.

We must aggressively rewrite or archive these documents to reflect the true, current state of the Striker system.

## What Changes

- **Rewrite `docs/user_manual.md`**: Update the state chain to `INIT → STANDBY → SCAN_MONITOR → GUIDED_STRIKE → RELEASE_MONITOR → LANDING_MONITOR`. Remove all mentions of programmatic generation.
- **Archive `init愿景.md`**: This document pitches the obsolete "procedural generation" vision. Move it to `docs/archive/procedural_generation_vision.md` as historical context.
- **Rewrite `docs/sitl_setup.md`**: Update the "What Gets Validated" section and "Expected Log Milestones" to reflect the new preburned mission download and GUIDED takeover flow.
- **Update `data/fields/README.md`**: Remove warnings/constraints regarding procedural approach geometry.

## Capabilities

### New Capabilities
- `architecture-docs-alignment`: Establishes the documentation standards and content required to reflect the Preburned Mission + GUIDED Takeover architecture.

### Modified Capabilities

## Impact

- `docs/user_manual.md` (Massive rewrite)
- `docs/sitl_setup.md` (Massive rewrite)
- `init愿景.md` (Archived)
- `data/fields/README.md` (Minor cleanup)
