## Context

The Striker system recently underwent a massive architectural simplification. It replaced the complex multi-stage dynamic mission uploading system (which involved temporary attack missions, ballistic reverse-calculations, and sequence-syncing logic) with a streamlined "Preburned Mission + GUIDED Takeover" architecture. In this new architecture, a single mission is burned before takeoff. Striker interrupts the mission via `GUIDED` mode (`MAV_CMD_DO_REPOSITION`) to execute a zero-latency gate-crossing drop, and then relinquishes control back to `AUTO` mode for landing.

The existing specifications in `openspec/specs/` document the old, complex logic. This mismatch causes significant technical debt, misleading future development and violating the single source of truth principle.

## Goals / Non-Goals

**Goals:**
- Completely align `openspec/specs/` with the current codebase reality.
- Archive or deprecate `ballistic-solver` and `attack-run` specifications.
- Introduce `guided-strike-control-loop` to serve as the definitive specification for the new `GUIDED` mode takeover architecture.
- Update `payload-release` and `strike-fullchain-validation` to reflect the new zero-latency fire-and-forget release trigger and the single-mission validation flow.

**Non-Goals:**
- Modifying any application code or tests. This is purely a documentation synchronization effort.
- Reverting the architecture to the old model.

## Decisions

1. **New Spec Creation**: We will create `guided-strike-control-loop/spec.md`. This document will define the `GUIDED` mode intervention, the generation of the `approach` and `exit` points on the attack axis, and the `MAV_CMD_DO_REPOSITION` sequence.
2. **Deprecation Strategy**: Instead of deleting old specs completely, we will move them to an `archive/` folder or prefix them with a deprecation notice. The OpenSpec architecture favors keeping them in their current path but modifying their content to state they are obsolete, ensuring trace-ability. We will update `attack-run/spec.md` and `ballistic-solver/spec.md` to clearly mark them as archived/obsolete.
3. **Trigger Logic Updates**: In `payload-release/spec.md`, the requirement for `COMMAND_ACK` will be explicitly struck down. The new requirement will mandate a non-blocking `send_command` execution to guarantee millisecond-level precision upon cross-track gate entry.

## Risks / Trade-offs

- **Risk**: Archiving docs might confuse developers looking for historical context on why ballistic solvers were built.
- **Mitigation**: We will leave a clear historical note in the deprecated specs explaining *why* they were removed (e.g., "The target coordinates are now assumed to be the exact spatial release point, negating the need for ballistic compensation").
