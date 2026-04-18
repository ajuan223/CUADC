## Purpose

Define the repository-controlled closed-loop tuning workflow for repeated SITL reruns, artifact preservation, and bounded software-side flight-behavior changes.
## Requirements
### Requirement: Software-only flight tuning loop SHALL follow the current `zjg2` debug workflow
The software-only tuning loop MUST describe and evaluate iterations using the current `zjg2` local debug workflow and its emitted run artifacts, rather than an older split-launch or `zjg`-only procedure.

#### Scenario: Tuning loop references the active field workflow
- **WHEN** the tuning-loop documentation or Skill is used to drive a rerun
- **THEN** it MUST reference the current field and launcher workflow used by the repository
- **AND** it MUST NOT prescribe an obsolete launch sequence that disagrees with the active local tooling

### Requirement: Software-only flight tuning loop SHALL preserve per-round evidence from emitted artifacts
Each tuning round MUST analyze the current run's emitted artifact directory and log targets, then record the round delta before another bounded software-side change is attempted.

#### Scenario: Tuning round uses current artifact chain
- **WHEN** a tuning round concludes and the next round is planned
- **THEN** the workflow MUST derive evidence from the emitted run artifacts and per-round changelog
- **AND** it MUST keep the debug loop grounded in the current launcher outputs

## ADDED Requirements

### Requirement: Software-only flight tuning loop SHALL operate on `zjg` with bounded Striker-side changes
The optimization loop MUST run the full closed-loop mission on `zjg`, analyze the preserved evidence, apply a bounded software-side tuning change, and rerun without modifying flight-controller firmware parameters.

#### Scenario: A tuning round applies only Striker-side behavior changes
- **WHEN** a round identifies an unsafe or unstable behavior during the `zjg` mission
- **THEN** the next change MUST be limited to Striker software logic, field profile data, or repository-controlled runtime defaults
- **AND** it MUST NOT require ad-hoc FC parameter tuning to continue the loop

#### Scenario: Every tuning change is validated by another full rerun
- **WHEN** a bounded software-side tuning change is made
- **THEN** the workflow MUST rerun the full `zjg` closed-loop mission before judging the change successful
- **AND** it MUST preserve the new round's artifacts and analysis before proceeding again

#### Scenario: Attack-run handoff can reduce landing-window energy with software-side altitude shaping
- **WHEN** preserved round analysis shows the aircraft entering the landing sequence with excess late-phase energy
- **THEN** the next bounded tuning step MAY lower the attack-run / exit-leg mission altitude toward the derived landing-approach altitude instead of inheriting scan altitude unchanged
- **AND** that change MUST remain within repository-controlled mission geometry or upload logic rather than FC parameter tuning

#### Scenario: Landing completion must not trigger from transient hit-ground status while still airborne
- **WHEN** preserved round analysis shows `SIM Hit ground` or similar landing status text arriving while the aircraft still has materially positive relative altitude or unstable terminal attitude
- **THEN** the next bounded tuning step MUST tighten Striker-side landing completion logic so mission completion is not declared from that status text alone
- **AND** the loop MUST continue using repository-controlled state/telemetry logic rather than FC parameter tuning to validate true touchdown

#### Scenario: Attack-run altitude shaping must remain bounded by successful landing-sequence behavior
- **WHEN** a software-side attack-run altitude reduction reaches the landing sequence but preserved rerun evidence shows the aircraft stuck materially above ground instead of converging through `NAV_LAND`
- **THEN** the next bounded tuning step MUST relax, gate, or revert that altitude shaping rather than treating a green test artifact alone as sufficient evidence
- **AND** the decision MUST be justified from preserved round telemetry and mission-phase logs
- **AND** a follow-up implementation MAY keep the temporary attack mission a small bounded buffer above the derived landing-approach altitude instead of forcing them equal, so the handoff into `DO_LAND_START` / `NAV_LAND` remains descending rather than flat

#### Scenario: Landing-sequence regressions may require handoff waypoint changes instead of further altitude-only tuning
- **WHEN** successive preserved reruns show the aircraft reaching `DO_LAND_START` / `NAV_LAND` but then hanging materially above ground or entering an implausible landing solution
- **THEN** the next bounded tuning step MUST be allowed to inspect and adjust temporary-mission sequencing or waypoint placement, not only attack-leg altitude
- **AND** the decision MUST still remain inside repository-controlled mission geometry or state logic rather than FC parameter tuning

### Requirement: Software-only flight tuning loop SHALL normalize `zjg` runtime prerequisites before optimization conclusions are trusted
The optimization loop MUST not treat `zjg` runs as valid tuning evidence until the field data and SITL launch inputs are runtime-compatible.

#### Scenario: `zjg` closed-loop runs require runtime-compatible field data
- **WHEN** the optimization workflow selects `--field zjg`
- **THEN** the field coordinates used by runtime mission generation MUST be in the coordinate frame expected by the field loader
- **AND** the SITL launcher/harness MUST use field-appropriate home and params instead of remaining pinned to `sitl_default`
