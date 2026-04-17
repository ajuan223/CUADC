## Context

The repository already contains enough evidence to prove the intended R4 stack shape, but the implementation is split between validated docs and stale automation. `docs/sitl_setup.md` and `docs/sitl_integration_results.md` show a working raw ArduPlane SITL → repo-local `.venv` MAVProxy → `uv run python -m striker --field sitl_default` chain, with explicit `--home 30.2610,120.0950,0,180`, `data/fields/sitl_default/sitl_merged.param`, and `~/ardupilot/Tools/autotest/models/plane.parm`. In contrast, `scripts/run_sitl.sh` and `tests/integration/conftest.py` still use the obsolete `Tools/autotest/default_params/plane.parm` path, omit the validated home position, and do not model the full MAVProxy routing path that Striker actually depends on.

The result is that the current integration layer can prove only heartbeat connectivity and field-profile loading, while `tests/integration/test_sitl_full_mission.py` is still a set of skipped placeholders for the exact mission chain the user wants closed: startup, MAVLink bring-up, takeoff, scan, strike/release, landing, and completion. The runtime already exposes the observability needed for this work: `src/striker/app.py` logs FSM transitions and mission milestones, and `FlightRecorder` can persist telemetry CSV output through `STRIKER_RECORDER_OUTPUT_PATH`.

R4 therefore is not about inventing a new simulation architecture. It is about making the already-validated stack reproducible from the project environment, wiring that stack into repeatable validation coverage, and ensuring failures can be debugged with preserved evidence instead of ad-hoc `/tmp` inspection.

## Goals / Non-Goals

**Goals:**
- Align scripts and integration fixtures with the currently validated repo-local SITL → MAVProxy → Striker launch topology.
- Replace skipped full-mission placeholders with runnable, guarded full-chain validation that asserts the mission reaches strike/release and landing milestones.
- Preserve enough per-run artifacts (SITL log, MAVProxy log, Striker log, flight recorder CSV) to diagnose failures without rerunning blindly.
- Keep the debug workflow focused on the actual failure layers in this project: stack bring-up, transport routing, mission upload/progression, release, landing, and override handover.
- Make the validation workflow executable from the repository’s own Python environment instead of relying on system-level MAVProxy assumptions.

**Non-Goals:**
- Replacing ArduPilot SITL with another simulator.
- Tuning ArduPlane firmware parameters beyond the already checked-in field/SITL defaults.
- Reworking Striker mission-generation logic unrelated to full-chain reproducibility.
- Solving the open-ended flight-log optimization loop from R5 in this change.

## Decisions

- Standardize R4 on the raw `arduplane` binary plus repo-local `.venv/bin/mavproxy.py`, not `sim_vehicle.py`.
  - Alternative considered: switching all validation to `sim_vehicle.py`. Rejected because the repository already has validated raw-binary commands, the user explicitly wants the project’s internal venv to own the Python side, and the raw topology makes the MAVProxy routing chain explicit instead of hiding it inside another launcher.
- Make one validated source of truth for the stack invariants used by scripts and tests: ArduPlane binary path, `sitl_merged.param`, `Tools/autotest/models/plane.parm`, `--home 30.2610,120.0950,0,180`, TCP 5760 upstream, UDP 14550/14551 downstream, and `STRIKER_TRANSPORT=udp`.
  - Alternative considered: continue duplicating commands between docs, shell scripts, and pytest fixtures. Rejected because the current drift is exactly why the docs say “works” while the automated tests still launch the wrong stack.
- Keep prerequisite failures explicit and early.
  - Alternative considered: let subprocess startup fail later and infer the root cause from timeouts. Rejected because missing `.venv` MAVProxy, missing ArduPlane binary, wrong defaults path, or missing field params all produce noisy failures that are much slower to debug than a direct preflight error.
- Split validation into two layers: stack bring-up health and mission-chain assertions.
  - Alternative considered: one monolithic end-to-end test only. Rejected because when the chain fails, the first question is whether the transport stack came up correctly or whether business logic failed after connection. Separate bring-up checks preserve that distinction.
- Use log- and artifact-based assertions for full-chain validation instead of trying to infer every mission state from raw MAVLink in the first pass.
  - Alternative considered: assert the entire mission exclusively from low-level MAVLink message capture. Rejected because Striker already emits the state transitions and milestone logs we need, and those logs are easier to align with SITL/MAVProxy evidence during debugging.
- Explicitly request `MISSION_CURRENT` and `MISSION_ITEM_REACHED` after link startup via `MAV_CMD_SET_MESSAGE_INTERVAL` so scan/enroute progression does not depend on whatever mission-progress streams the transport happens to emit by default.
  - Alternative considered: rely on the default MAVProxy/SITL stream set. Rejected because the R4 normal-path debug run showed the aircraft continued to fly the scan pattern while Striker never observed mission-sequence advancement, which stalled the FSM at `scan` even though the mission itself was progressing.
- Treat post-upload mission-progress values as untrusted until the attack mission sequence resets into the new mission range.
  - Alternative considered: transition to release immediately when `MISSION_CURRENT` remains greater than the attack target sequence after mission replacement. Rejected because the R4 artifact run proved that stale scan-sequence values can survive briefly across the attack mission upload, causing an immediate false release transition and an unsafe landing handoff while the aircraft is still far from the intended target path.
- Track `MISSION_CURRENT` separately from `MISSION_ITEM_REACHED` and use each signal only where it reflects the intended semantics.
  - Alternative considered: collapse both MAVLink messages into a single `mission_current_seq` field. Rejected because the R4 artifact runs showed `MISSION_ITEM_REACHED` from the previous mission can continue arriving after the attack mission is active, while `MISSION_CURRENT` correctly reflects the active attack sequence. Collapsing them corrupts attack-run state decisions.
- Keep the attack mission's exit waypoint in the landing handoff instead of forcing `MISSION_SET_CURRENT` directly to `DO_LAND_START`.
  - Alternative considered: jump straight to the landing sequence as soon as release is confirmed. Rejected because the R4 artifact run showed that skipping the exit leg drives the fixed-wing aircraft into an unstable, low-altitude ground-skimming turn and never reaches touchdown completion in a controlled way.
- Align the no-wind attack-run heading with the published landing corridor and keep the exit waypoint short of the derived landing-approach gate so the post-release AUTO mission does not overshoot and reverse before touchdown.
  - Alternative considered: keep using the configured fixed exit distance even when the derived landing approach sits closer than that distance. Rejected because the latest R4 artifact run showed the aircraft descending toward ~44m, then arcing away and flattening around ~49.5m roughly 294m from touchdown after release, which is consistent with the exit leg carrying the aircraft past the landing corridor and never letting the AUTO landing sequence settle into a real touchdown path.
- Treat persistent near-ground manual fallback as an explicit non-success handoff outcome.
  - Alternative considered: aim the attack run using the transient direct bearing from the scan endpoint and wait only for `relative_alt_m < 1.0` to declare completion. Rejected because the R4 artifacts showed that this geometry can exit away from the landing corridor, after which ArduPlane falls back into a near-ground MANUAL state without ever emitting the touchdown signal the validation was waiting for.
- Give the fallback attack target an explicit waypoint acceptance radius in the SITL field profile and mission item encoding.
  - Alternative considered: keep the target waypoint at ArduPlane's default acceptance radius and rely on geometric alignment alone. Rejected because the preserved fallback artifacts still pinned mission progress at target seq `2` while the aircraft passed the drop point and opened back out past ~236m, showing the mission never considered the target reached even after the no-wind heading was corrected.
- Aim no-wind attack runs at the derived landing-approach gate from the resolved drop point instead of assuming every target already sits on the published runway centerline.
  - Alternative considered: keep using the bare landing heading for every no-wind target once the exit leg is corridor-aligned. Rejected because the preserved fallback artifact showed the fallback midpoint landed well east of the runway corridor, and the aircraft then stalled at the target waypoint with mission sequence pinned at `2` while distance opened back out to ~249m, which means the fixed-wing geometry could not naturally carry the aircraft from that offset target into the release/exit chain.
- Isolate the integration harness vision socket per run instead of hard-coding port 9876.
  - Alternative considered: keep a single fixed TCP port for every validation run. Rejected because preserved fallback evidence showed a stale mock-vision client from an earlier run could reconnect to the next test's receiver and inject a real drop point into the supposed no-vision scenario, turning fallback coverage into the vision path nondeterministically.
- Keep the full-chain mission timeout budget in one harness constant and size it from preserved artifact evidence instead of duplicating shorter per-test overrides.
  - Alternative considered: leave the fixture default at 240s and raise only selected test-local waits to 480s. Rejected because the preserved normal-path runs now show the validated `sitl_default` chain taking roughly 402–484 seconds end-to-end, so the lower shared budget becomes a stale hidden cutoff that can still fail the harness even after the mission logic is correct.
- Persist each validation run into a dedicated output directory containing the full stack logs plus the flight recorder CSV.
  - Alternative considered: continue writing to fixed `/tmp/*.log` files and `flight_log.csv`. Rejected because repeated debug runs overwrite the evidence needed to compare regressions and repairs, which blocks the user’s stated debug-first workflow.
- Keep fallback-path and human-override checks inside the same stack harness once the normal path is runnable.
  - Alternative considered: defer fallback and override until after the normal path. Rejected because the current test file already treats them as first-class scenarios, and the harness cost is shared once the base stack is reproducible.
- Flush the per-run flight recorder on each sample so short override and teardown paths still preserve a readable CSV artifact before process shutdown.
  - Alternative considered: rely on close-time flushing only. Rejected because the override validation can terminate the run quickly after the handover log appears, and the preserved artifact requirement applies even when the mission ends before normal completion.

## Risks / Trade-offs

- [Full-chain SITL tests are slower and more fragile than unit tests] → Guard them behind clear prerequisite checks and preserve artifacts so failures are diagnosable instead of flaky noise.
- [Log text can drift and break assertions] → Assert on stable milestone substrings that already reflect real operator observability, not on incidental formatting.
- [Subprocess teardown can leak stale SITL/MAVProxy/Striker processes] → Use one harness with explicit PID ownership, ordered shutdown, and artifact flushing before cleanup.
- [Launch commands may diverge again between docs, scripts, and tests] → Reuse the same validated constants and update docs only after the harness proves the commands.
- [Native release-path validation may expose additional SITL edge cases] → Start with the currently validated release chain and keep dry-run/fallback diagnostics available as comparison paths.

## Migration Plan

1. Update the repo-local stack launcher and integration fixtures to use the validated ArduPlane, MAVProxy, home-position, and parameter-file configuration.
2. Add a reusable full-chain harness that starts the stack, routes logs into a per-run artifact directory, and tears everything down cleanly.
3. Replace the skipped full-mission integration placeholders with runnable guarded tests for the normal path, fallback path, and override path.
4. Run targeted integration validation from the project environment, inspect artifacts, and adjust launch/timeout details until the chain is stable.
5. Update the SITL docs and OpenSpec task status to reflect the validated workflow.

## Open Questions

- Whether the normal-path automated validation should default to native release behavior or keep a dry-run variant as the first required green path.
- Whether the per-run artifact directory should live under `artifacts/`, `tmp/`, or a test-output path ignored by git.
- Whether the override scenario should assert only state handover/logging, or also prove that outbound mission-control commands stop immediately after override detection.
