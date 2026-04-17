## 1. ZJG runtime readiness

- [x] 1.1 Normalize `data/fields/zjg/field.json` into the runtime coordinate frame expected by the field loader and add regression coverage for the chosen representation
- [x] 1.2 Add per-field SITL launch inputs so launcher/harness home and params are not pinned to `sitl_default` when running `--field zjg`
- [x] 1.3 Provide or generate the field-specific merged SITL params required to boot the `zjg` closed loop without manual command edits

## 2. Iteration artifact retention

- [x] 2.1 Add a dedicated `runtime_data` optimization-round layout for `zjg` that preserves raw run directories plus monotonic `log_N.csv` copies
- [x] 2.2 Persist `flight_log_analysis_N.md` artifacts alongside the corresponding preserved round evidence
- [x] 2.3 Add tests or assertions that prevent optimization rounds from overwriting prior copied logs or analyses

## 3. Flight-log analysis pipeline

- [x] 3.1 Expand the recorder or analysis inputs as needed so round reports can evaluate takeoff, routing, strike, and landing behavior from preserved evidence
- [x] 3.2 Implement the first round-analysis workflow that correlates `flight_log.csv` with mission-phase logs and writes `flight_log_analysis_1.md`
- [x] 3.3 Document the round-to-round analysis workflow and naming convention for subsequent optimization iterations
- [x] 3.4 Promote landing-window telemetry from existing recorder fields into the persisted round analysis so touchdown quality can be judged without adding FC-param tuning

## 4. Software-only tuning loop

- [x] 4.1 Run the first full `zjg` closed-loop round with preserved artifacts and capture the baseline behavior
- [x] 4.2 Apply one bounded Striker-side tuning change based on the preserved round analysis, without changing FC params
- [x] 4.3 Rerun the full `zjg` closed loop after each tuning change and record whether safety/stability improved or regressed
- [x] 4.4 Reduce landing-window energy by aligning temporary attack-mission altitude with the derived landing handoff geometry, then rerun `zjg` and preserve the next round
- [x] 4.5 Prevent false-positive landing completion from transient `SIM Hit ground` status while the aircraft is still airborne, then rerun `zjg` and preserve the next round
- [x] 4.6 Relax, gate, or revert round-6 attack-mission altitude shaping after preserving the round-7 landing-sequence regression, then rerun `zjg` and preserve the next round
- [x] 4.7 Diagnose and tune the landing handoff waypoint sequencing/placement after round-8 preserved evidence shows `NAV_LAND` hanging above ground, then rerun `zjg` and preserve the next round
- [x] 4.8 Shorten or gate the temporary exit leg when it leaves too little straight-in spacing before the landing-approach waypoint, then rerun `zjg` and preserve round-9 evidence
- [x] 4.9 Tighten landing-approach waypoint acceptance after round-9 preserved evidence shows the approach gate still being passed far too loosely, then rerun `zjg` and preserve round-10 evidence
- [x] 4.10 Decouple landing from the appended temporary attack mission after round-10 preserved evidence shows early `NAV_LAND` activation still persists, then rerun `zjg` and preserve round-11 evidence
- [x] 4.11 Keep the dedicated post-release landing handoff but activate the landing approach gate directly after round-11 preserved evidence shows starting from `DO_LAND_START` still skips convergence, then rerun `zjg` and preserve round-12 evidence
- [x] 4.12 Omit `DO_LAND_START` from the dedicated post-release landing-only mission after round-12 preserved evidence shows direct activation still passes the approach gate far too loosely, then rerun `zjg` and preserve round-13 evidence
- [x] 4.13 Restore the round-12 landing-only mission shape and tighten the remaining post-release landing-only approach gating after round-13 preserved evidence shows removing `DO_LAND_START` regresses into a high-altitude `NAV_LAND` hang, then rerun `zjg` and preserve round-14 evidence
