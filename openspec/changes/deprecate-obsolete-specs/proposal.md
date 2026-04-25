## Why

The `openspec/specs/` directory is cluttered with legacy specifications that mandate the obsolete `INIT → PREFLIGHT → TAKEOFF → SCAN → ENROUTE` state machine and procedural geometry generation. These concepts were fundamentally replaced by the `preburned-mission-refactor` and `GUIDED` takeover architecture, but the spec files themselves remain intact, spreading conflicting constraints and causing technical debt in the OpenSpec knowledge base. 

## What Changes

This change will formally deprecate and mark obsolete the following specs by appending a `**Status: Obsolete/Replaced**` block and removing them from active validation checklists:
- `procedural-mission-geometry`
- `fixed-wing-takeoff-sequence`
- `mission-upload`
- `dryrun-validation-strategy`
- `attack-run-sitl-validation`
- `sitl-environment-setup`
- `sitl-default-field`
- `field-profile`
- `simplified-mission-flow`

## Capabilities

### New Capabilities
- `obsolete-specs-deprecation`: Adds deprecation warning banners and status updates to all obsolete specifications.

### Modified Capabilities

## Impact

- Affected code: Only documentation in `openspec/specs/` will be touched.
- No source code in `src/striker/` or `pkg/` will be affected.
