## Context

R5 is an open-ended optimization loop, but the repository is not yet shaped for that loop on `zjg`. The current validated full-chain stack is pinned to `sitl_default`: both the launcher and pytest harness hard-code `data/fields/sitl_default/sitl_merged.param` plus the Zijingang-specific home string `30.2610,120.0950,0,180` in `scripts/run_sitl.sh:13-19,53-60` and `tests/integration/conftest.py:22-30,57-80`. Runtime field loading itself is generic (`src/striker/config/field_profile.py:184-201`, `src/striker/config/settings.py:34`), but SITL bring-up is not.

The second blocker is field data compatibility. `data/fields/zjg/field.json` currently declares `"coordinate_system": "GCJ-02"`, while runtime field handling assumes raw coordinates are already WGS84: the field-profile docs say all field coordinates are WGS84 (`data/fields/README.md:39-43`), the field loader does no runtime coordinate conversion (`src/striker/config/field_profile.py:184-201`), and field-editor export validation asserts `coordinate_system == "WGS84"` (`tests/unit/test_field_editor_export.py:18-21`). That means `zjg` is not yet a safe drop-in replacement for SITL mission geometry.

The third blocker is iterative artifact retention. The repo already preserves per-run logs for integration and manual SITL under `runtime_data/integration_runs/...` and `runtime_data/manual_sitl/...`, but there is no dedicated optimization-round structure for storing `log_1.csv`, `flight_log_analysis_1.md`, round-specific code conclusions, and rerun outputs side by side. Also, the current flight recorder only fills position/altitude columns even though the CSV header advertises richer telemetry (`src/striker/telemetry/flight_recorder.py:18-34,77-88`). That is enough to start geometric analysis, but not enough for robust tuning of unstable flight behavior.

## Goals / Non-Goals

**Goals:**
- Enable repeatable full closed-loop SITL runs on `--field zjg` without manual file surgery.
- Normalize `zjg` field data so runtime mission geometry uses the correct coordinate frame.
- Preserve every optimization round in a non-overwriting artifact layout that keeps raw logs, copied flight logs, analysis markdown, and any derived summaries together.
- Define a software-only tuning loop that analyzes preserved run evidence, applies bounded logic/config changes in Striker, reruns the full mission, and records whether behavior improved.
- Improve the recorder/analysis pipeline enough to evaluate takeoff, route tracking, strike handoff, and landing stability from preserved evidence.

**Non-Goals:**
- Tuning ArduPilot firmware parameters or relying on ad-hoc Mission Planner changes.
- Replacing the validated raw `arduplane -> MAVProxy -> Striker` stack with another simulator or launcher architecture.
- Solving all open-ended flight-quality issues in one patch; R5 is explicitly iterative.
- Introducing speculative dashboards or external storage systems before the local loop is useful.

## Decisions

- Derive R5 from the validated R4 stack instead of inventing a second optimization harness.
  - Alternative considered: separate one-off scripts for `zjg`. Rejected because the current repository already has a proven stack shape, and divergence would recreate the docs-vs-automation drift R4 just removed.
- Add first-class per-field SITL launch inputs for `zjg` rather than hard-coding `sitl_default` assumptions.
  - Alternative considered: keep editing shell commands manually between rounds. Rejected because iterative tuning requires many reruns, and manual home/param rewrites are too error-prone.
- Normalize `zjg` into runtime-compatible WGS84 field data before trusting any flight-log conclusions.
  - Alternative considered: feed `GCJ-02` directly into runtime geometry and "see how it flies." Rejected because any path/landing instability would be confounded by coordinate-frame error rather than actual flight-logic behavior.
- Store optimization evidence under a dedicated round-based subtree in `runtime_data/` (for example `runtime_data/optimization_runs/zjg/round_001/`).
  - Alternative considered: reuse the raw integration path names only. Rejected because R5 needs stable human-oriented filenames like `log_1.csv` and `flight_log_analysis_1.md` alongside the raw stack artifacts from the same round.
- Treat flight-log analysis as a persisted artifact, not just terminal output.
  - Alternative considered: summarize findings only in chat. Rejected because the user explicitly wants a durable round-by-round history that survives across iterations.
- Expand recorder usefulness incrementally, starting with preserved geometry/altitude traces and only then adding richer fields that are already available in `MissionContext` telemetry.
  - Alternative considered: design a perfect telemetry warehouse before the first R5 run. Rejected because the loop should start with the smallest artifact set that can expose dangerous takeoff, route, and landing behavior.
- Treat field profile landing geometry as validated runtime input, not editor-only metadata.
  - Alternative considered: let invalid derived approach geometry fail only in preflight mission generation. Rejected because R5 needs `zjg` round failures to reflect flight behavior, not avoidable field-data shape errors.
- Use `approach_alt_m` + `glide_slope_deg` as the primary landing-geometry controls instead of a universal fixed 200m minimum approach distance.
  - Alternative considered: keep the hardcoded 200m gate. Rejected because current ArduPlane automatic-landing guidance does not prescribe a universal minimum final-approach distance, and the fixed threshold blocks small-field `zjg` tuning before aircraft-performance or geofence constraints are actually evaluated.
- For the current `zjg` loop, continue treating the field profile itself as the bounded software-side tuning surface when runway facts imply an impossible approach inside the geofence.
  - Alternative considered: add automatic clipping or silent geometry deformation in mission generation. Rejected because that would hide operator-authored landing intent and make round-to-round evidence harder to interpret.
- Keep software-side tuning bounded to Striker logic/config defaults that shape mission geometry, sequencing, acceptance, and command timing.
  - Alternative considered: changing FC params for faster wins. Rejected because the user explicitly excluded FC param tuning.
- When the terminal landing window shows the aircraft still carrying excess energy into `DO_LAND_START` / `NAV_LAND`, allow the temporary attack mission altitude to converge toward the derived landing-approach altitude instead of always inheriting `scan.altitude_m`.
  - Alternative considered: keep the attack mission at scan altitude and rely only on the FC landing controller to shed the extra energy. Rejected because preserved round-5 evidence shows the aircraft entering the late landing window around 40m AGL with ~8.6–9.2 m/s while the attack mission still hard-codes `scan.altitude_m`; bringing the attack/exit leg closer to the already-derived landing gate is a bounded repository-side change that directly targets the handoff geometry without touching FC params.
- Treat `SIM Hit ground` / similar landing status text as insufficient by itself for mission completion when preserved telemetry still shows the aircraft materially airborne or unstable.
  - Alternative considered: keep accepting any landing-related status text as immediate completion. Rejected because preserved round-6 evidence shows `LandingState` completed at roughly 36m AGL with terminal-window roll peaks around 70° after a transient `SIM Hit ground` message; requiring corroborating low-altitude or settled-flight evidence is a bounded Striker-side state-machine change that prevents false-positive mission success without touching FC params.
- Keep attack-mission altitude shaping reversible and evidence-driven rather than assuming the first green rerun proves the new handoff is safe.
  - Alternative considered: permanently keep the temporary attack mission pinned to the derived landing-approach altitude after round 6. Rejected because preserved round-7 evidence, once false-positive landing completion was removed, shows the aircraft entering `Mission: 7 Land` and then remaining stuck around 35–38m AGL while still armed and in AUTO; the shaping therefore needs to be relaxed, gated, or reverted based on real landing-sequence behavior rather than on the previously masked success artifact.
- When reducing late landing energy, prefer a bounded handoff buffer above the derived landing-approach altitude instead of forcing the temporary attack mission exactly onto the landing-approach altitude.
  - Alternative considered: make attack / target / exit legs exactly equal to `geometry.landing_approach[2]`. Rejected because current ArduPilot guidance still makes the waypoint before `NAV_LAND` materially important, and preserved round-7 evidence shows that an equal-altitude handoff can leave the aircraft established in `Mission: 7 Land` around 35–38m AGL without converging; keeping a small altitude margin preserves a descending handoff while still reducing excess energy versus the old scan-altitude coupling.
- If multiple preserved reruns still reach `DO_LAND_START` / `NAV_LAND` but end in a stuck above-ground state, stop iterating on altitude-only changes and inspect the handoff waypoint sequencing / placement itself.
  - Alternative considered: continue sweeping only attack-leg altitude. Rejected because preserved round-7 and round-8 evidence both reach the landing sequence yet fail in different above-ground hold states; that pattern suggests the failure surface is now the interaction between temporary attack-mission waypoints and the landing sequence, not just the chosen attack altitude.
- When the resolved attack target is already at or extremely near the derived landing-approach gate, fall back to the published landing corridor heading instead of aiming a zero-length no-wind attack leg directly at the same coordinate.
  - Alternative considered: treat `target == landing_approach` as acceptable and keep aiming the pre-release leg at the same point. Rejected because the preserved round-4 evidence showed the mission only completed by luck after a long shallow continuation, while current ArduPlane landing docs still describe `NAV_LAND` as beginning once the preceding waypoint is reached; keeping distinct forward-moving pre-release and post-release legs is the more stable software-side handoff.
- When the temporary exit waypoint would leave only a very short leg into the derived landing-approach waypoint, cap that exit leg so the landing handoff retains a meaningful straight-in segment before `NAV_LAND`.
  - Alternative considered: keep only the existing "do not fly beyond the landing approach" cap. Rejected because preserved round-8 evidence shows `Mission: 6 WP` being passed from roughly 145m away after only ~67m of exit-to-approach spacing, which implies the handoff corridor is too short for ArduPlane to converge cleanly before `NAV_LAND`; shortening the temporary exit leg is a bounded repository-side waypoint-placement change that directly targets the observed sequencing failure without touching FC params.
- If shortening the exit leg still leaves the landing-approach waypoint accepted from implausibly large distance, tighten the generated landing-approach waypoint acceptance radius instead of relying on ArduPlane's default waypoint-transition behavior.
  - Alternative considered: keep using the approach waypoint with the default acceptance settings and continue adjusting only geometry. Rejected because preserved round-9 evidence still shows `Mission: 6 WP` passed from about 151m away even after restoring ~98m of exit-to-approach spacing, while ArduPilot guidance says smaller waypoint radii force the plane to fly much closer to a waypoint before transitioning; tightening the generated approach-gate acceptance is therefore the next bounded repository-side lever that directly targets the still-loose handoff without changing FC params.
- If the appended attack mission still transitions into `NAV_LAND` implausibly early after spacing and acceptance tightening, upload and activate a dedicated landing-only mission after release instead of leaving landing items appended behind the temporary attack mission.
  - Alternative considered: keep iterating only on the appended mission's waypoint geometry. Rejected because preserved round-10 evidence still shows `Mission: 6 WP` passed from about 160m away despite a 10m approach acceptance radius, which suggests the failure surface is now the sequencing model itself rather than just waypoint shape; ArduPilot docs also allow `DO_LAND_START` to be triggered directly, so an explicit post-release landing handoff is a bounded repository-side sequencing change worth trying before any FC-param tuning.
- If a dedicated landing-only mission still starts by activating `DO_LAND_START` and preserved evidence shows the approach waypoint being passed loosely before `NAV_LAND`, activate the approach waypoint directly instead of making `DO_LAND_START` the first effective post-release target.
- If activating the landing approach waypoint directly still leaves the approach gate being passed loosely while a leading `DO_LAND_START` remains in the landing-only mission, omit `DO_LAND_START` from that dedicated post-release mission and rely on a normal approach-waypoint → `NAV_LAND` handoff instead.
- If omitting `DO_LAND_START` from the dedicated post-release landing-only mission regresses into a high-altitude `NAV_LAND` hang while the approach waypoint is still being passed loosely, restore the round-12 mission shape and tighten the remaining repository-controlled post-release approach gating instead of continuing to remove landing markers.
  - Alternative considered: keep the landing-only mission structure but continue setting mission current to the leading `DO_LAND_START` marker. Rejected because preserved round-11 evidence shows `Mission: 1 LandStart` followed by `Mission: 2 WP` being passed from about 164m away, while current ArduPilot docs describe `DO_LAND_START` primarily as a marker / trigger and typical generated landings place the approach builder before the effective landing trigger; starting the handoff at the approach gate is therefore the next bounded repository-side sequencing lever to try before touching FC params.

## Risks / Trade-offs

- [ZJG SITL prerequisites are incomplete today] → First close field/home/param compatibility before interpreting any optimization run as meaningful.
- [Recorder data is currently sparse] → Use log + CSV + mission milestone correlation initially, and extend recorder coverage only where analysis proves blind spots.
- [Iterative tuning can regress previously green chains] → Preserve every round and rerun the full closed loop after each bounded change.
- [Round history can become messy or overwritten] → Define one canonical artifact tree and monotonically increasing round IDs.
- [Open-ended optimization can sprawl] → Keep each round scoped to one or two observed behaviors, with a written hypothesis and explicit post-run judgment.

## Migration Plan

1. Add the missing R5 OpenSpec specs/tasks covering ZJG readiness, artifact retention, analysis persistence, and the software-only tuning loop.
2. Make `zjg` runtime-compatible for SITL use (coordinate normalization plus per-field launch inputs/home/params).
3. Introduce a dedicated optimization artifact layout under `runtime_data/` that copies/preserves round outputs as `log_N.csv`, `flight_log_analysis_N.md`, and associated raw logs.
4. Validate landing geometry as part of field-profile loading so invalid `zjg` runway/approach combinations fail before preflight mission generation.
5. Run the first full closed-loop `zjg` round, capture artifacts, and write `flight_log_analysis_1.md`.
6. Apply one bounded software-side tuning change, rerun, and continue the round-based optimization loop.

## Open Questions

- Whether `zjg` should get its own checked-in `sitl_merged.param`, or whether the repo should generate per-field merged params from a common recipe.
- Whether round numbering should be global for all R5 runs or scoped under each field name.
- Which additional recorder fields should be promoted first after position/altitude: mode/armed, speed, attitude, or all currently available telemetry in one pass.
