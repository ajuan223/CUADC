## ADDED Requirements

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
