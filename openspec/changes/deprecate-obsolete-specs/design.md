## Context

Striker recently underwent a major architectural change: we transitioned away from procedural generation of missions (where Striker calculated scan paths, takeoffs, and landings and uploaded them at runtime in a PREFLIGHT state). Instead, we now use a Preburned Mission approach (using Mission Planner) where the entire mission is burned to the flight controller, and Striker monitors the `SCAN` progress, then takes over in `GUIDED` mode for the `GUIDED_STRIKE` payload release.

While the primary code and end-user documentation were updated to reflect this, the `openspec/specs/` directory remains littered with old specifications asserting the procedural methodology and the old state machine chain (`PREFLIGHT → TAKEOFF → SCAN → ENROUTE`).

## Goals / Non-Goals

**Goals:**
- Formally mark all legacy procedural and old-FSM specifications as obsolete.
- Add an explicit status block to the top of each deprecated spec to prevent future AI agents or developers from adhering to them.

**Non-Goals:**
- Rewrite the old specs entirely (they should remain intact for historical context but visibly marked obsolete).
- Touch code logic in `src/striker/`.

## Decisions

**D1: In-Place Obsolete Tagging**
Instead of deleting the specs, we will add the following block at the top of each affected `spec.md`:
```markdown
**Status: Obsolete/Replaced**
**Reason**: Replaced by `preburned-mission-refactor`. The concepts in this specification (such as procedural mission generation or the old state chain `PREFLIGHT → ENROUTE`) are no longer used in the current `GUIDED` takeover architecture.
```
*Rationale:* OpenSpec relies on historical specs for context. Deleting them removes context. Deprecating them safely preserves the knowledge while turning off active validation.

## Risks / Trade-offs

- **Risk:** Some old specs might contain a mix of obsolete and still-valid requirements.
- **Mitigation:** We will mark the entire file obsolete and assume any surviving logic is already captured in the active, newer specs (like `guided-strike-control-loop` and `strike-fullchain-validation`).
