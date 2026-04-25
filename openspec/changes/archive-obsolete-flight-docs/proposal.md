## Why

The current documentation in `openspec/specs/` is heavily outdated and no longer reflects the true architecture and execution logic of the Striker system. Specifically:
1. It describes dynamically uploading a temporary attack mission and waiting for sequence syncing, but the actual implementation uses a single preburned mission encompassing Takeoff + Scan + Landing, with Striker intervening via `GUIDED` mode (`DO_REPOSITION`).
2. It mandates the use of a real-time `BallisticCalculator` to find a drop point ahead of the target, whereas the current system assumes the provided coordinate is the absolute release gate and requires zero ballistic compensation.
3. It relies on a large `release_acceptance_radius_m` (e.g., 35m) for proximity fallback, which caused premature releases. This has been replaced by a strict 2.0m fallback radius prioritizing exact cross-track gate calculation.
4. It waits for `COMMAND_ACK` for payload release, but the code uses a fire-and-forget `send_command` wrapper for zero-latency drops.

Archiving and rewriting these specifications is necessary to eliminate this technical debt and ensure the documentation serves as a reliable source of truth.

## What Changes

1. **Archive Obsolete Specs**: `ballistic-solver`, `attack-run`, and portions of `strike-fullchain-validation` that mandate mission uploading and sequence syncing will be archived or marked deprecated.
2. **Rewrite Payload Release & Control Loop Specs**: We will introduce updated documentation (`guided-strike-control-loop`) that formally specifies the new "Preburned Mission + GUIDED Takeover" architecture, and update `payload-release` to reflect the zero-latency fire-and-forget trigger mechanism.

## Capabilities

### New Capabilities
- `guided-strike-control-loop`: Defines the new strike architecture where Striker takes over a preburned mission using `GUIDED` mode and `MAV_CMD_DO_REPOSITION` without uploading temporary missions.

### Modified Capabilities
- `attack-run`: Mark as obsolete/archived, as its dynamic mission upload requirements are no longer valid.
- `ballistic-solver`: Mark as obsolete/archived, as Striker now treats the drop point as an absolute release coordinate.
- `payload-release`: Update requirement to remove `COMMAND_ACK` verification in favor of the zero-latency fire-and-forget trigger.
- `strike-fullchain-validation`: Remove testing requirements regarding "sequence syncing" and "temporary attack mission" uploads, reflecting the single preburned mission test flow.

## Impact

- `openspec/specs/attack-run/spec.md` (Archived)
- `openspec/specs/ballistic-solver/spec.md` (Archived)
- `openspec/specs/payload-release/spec.md` (Updated)
- `openspec/specs/strike-fullchain-validation/spec.md` (Updated)
- `openspec/specs/guided-strike-control-loop/spec.md` (Newly created)
