## 1. Stack launch alignment

- [x] 1.1 Update the repo launcher and integration fixtures to use the validated ArduPlane binary, explicit `--home`, `sitl_merged.param`, and `Tools/autotest/models/plane.parm`
- [x] 1.2 Start MAVProxy from the project `.venv` and wire Striker to the validated UDP transport topology with fail-fast prerequisite checks
- [x] 1.3 Route SITL, MAVProxy, Striker, and recorder outputs into per-run artifact paths instead of fixed overwrite-only files

## 2. Full-chain validation coverage

- [x] 2.1 Replace the skipped normal-path full-mission placeholder with runnable guarded validation that asserts mission upload, ordered state progression, release, and landing/completion milestones
- [x] 2.1a Request `MISSION_CURRENT` / `MISSION_ITEM_REACHED` explicitly so scan/enroute progression is observable in the validated MAVProxy transport path
- [x] 2.1b Re-baseline the normal-path runtime budget against the actual `sitl_default` scan duration and close the remaining end-to-end timeout gap
- [x] 2.1c Ignore stale post-upload mission sequence values until the attack mission syncs into its new sequence range
- [x] 2.1d Keep `MISSION_CURRENT` and `MISSION_ITEM_REACHED` separated so stale reached events cannot corrupt attack-run progression
- [x] 2.1e Preserve the attack mission exit leg during landing handoff instead of forcing `DO_LAND_START`
- [x] 2.1f Align the no-wind attack-run exit with the published landing corridor instead of using the transient scan-end bearing
- [x] 2.1g Cap the no-wind attack-run exit distance so the exit waypoint stays ahead of the landing-approach gate rather than overshooting it
- [x] 2.2 Add fallback-path coverage that runs through the same stack without a resolved vision drop point and verifies release plus landing milestones
- [x] 2.2a Isolate fallback validation from stale vision publishers by using a per-run vision socket
- [x] 2.2b Re-aim no-wind fallback attack runs toward the derived landing-approach gate so the target sequence can complete
- [x] 2.2c Give the fallback attack target an explicit acceptance radius so fixed-wing SITL can progress through release
- [x] 2.3 Add override-path coverage that verifies autonomous progression stops cleanly and the override handover outcome is recorded

## 3. Validation and debug closure

- [x] 3.1 Run targeted project-venv SITL/MAVProxy/Striker validation and inspect the preserved artifacts until the stack is reproducible
- [x] 3.2 Update the SITL usage/debug docs to match the validated launch workflow and common failure checks
