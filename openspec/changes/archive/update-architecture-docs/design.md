## Context

The Striker codebase recently underwent the `preburned-mission-refactor`, moving from an architecture where Striker generated all mission geometry (takeoff, scan, landing) to an architecture where an externally designed preburned mission is loaded onto the flight controller. Striker now passively monitors this mission until the scan finishes, then uses `GUIDED` mode (`DO_REPOSITION`) to execute the attack run before returning control to `AUTO` mode for landing.

However, the main user-facing documentation (`user_manual.md`, `init愿景.md`, `sitl_setup.md`) still heavily promotes the old "Procedural Mission Generation" architecture. This causes a fundamental disconnect between the documentation and the actual implementation.

## Goals / Non-Goals

**Goals:**
- Eliminate all mentions of programmatic generation for takeoff, scan, and landing geometry in user-facing documentation.
- Update the documented state machine sequence to accurately reflect reality: `INIT → STANDBY → SCAN_MONITOR → GUIDED_STRIKE → RELEASE_MONITOR → LANDING_MONITOR`.
- Archive the obsolete `init愿景.md` as it fundamentally conflicts with the current preburned mission paradigm.
- Correct the `sitl_setup.md` guide so developers know what log outputs and behaviors to actually expect.

**Non-Goals:**
- Modifying any Python code or flight logic.
- Rewriting the AI Agent coding constitution or `CHARTER.md`.
- Addressing the separate topic of UI/frontend features (e.g., `fe-waypoint-exporter`).

## Decisions

- **Archive vs Rewrite for `init愿景.md`**: Since `init愿景.md`'s entire thesis is "why we chose programmatic generation over manual waypoints", and the project just reverted to manual waypoints (preburned missions), the document cannot be simply updated. It will be moved to `docs/archive/procedural_generation_vision.md` to preserve its historical context.
- **`user_manual.md` Overhaul**: Section 1 and Section 4 will be heavily rewritten. We will remove the formulas for calculating landing approach distances and boustrophedon generation, replacing them with explanations of the `STANDBY` preburned mission download and `GUIDED_STRIKE` takeover mechanism.
- **SITL Setup Guide Realignment**: We will remove the outdated "Procedural landing geometry" validation checks from `sitl_setup.md`, and update the "Expected Log Milestones" to match the actual logs emitted by the new state machine.

## Risks / Trade-offs

- **Risk**: Losing the rationale for *why* the fallback drop point logic exists.
  - **Mitigation**: Ensure `user_manual.md` still clearly documents the 3-level fallback drop point strategy (external vision -> field JSON fallback -> geometric centroid), which was kept intact during the refactor.
- **Risk**: Archiving `init愿景.md` might leave the project without a high-level "vision" document.
  - **Mitigation**: The `CHARTER.md` and the updated `user_manual.md` provide sufficient high-level overview. A new vision document can be written in the future if needed, but for now, preventing confusion is paramount.
