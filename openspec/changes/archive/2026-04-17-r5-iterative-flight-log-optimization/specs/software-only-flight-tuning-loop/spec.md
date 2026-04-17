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

#### Scenario: Exit waypoint must leave a usable straight-in handoff before the landing approach gate
- **WHEN** preserved rerun evidence shows the aircraft reaching the landing sequence only after passing the landing approach waypoint from implausibly large distance or with too little exit-to-approach spacing to stabilize
- **THEN** the next bounded tuning step MUST be allowed to shorten or gate the temporary attack-mission exit leg so the landing approach waypoint still has a meaningful straight-in segment before `NAV_LAND`
- **AND** that spacing rule MUST remain inside repository-controlled mission geometry rather than FC parameter tuning

#### Scenario: Landing approach waypoint may require tighter acceptance than default waypoint transition behavior
- **WHEN** preserved rerun evidence still shows `DO_LAND_START` / approach `NAV_WAYPOINT` being accepted from implausibly large distance even after handoff spacing is shortened
- **THEN** the next bounded tuning step MUST be allowed to tighten the generated landing-approach waypoint acceptance behavior so the aircraft must converge materially closer to the approach gate before transitioning into `NAV_LAND`
- **AND** that acceptance change MUST remain inside repository-controlled mission-item generation rather than FC parameter tuning

#### Scenario: Release may need an explicit handoff into a landing-only mission
- **WHEN** preserved rerun evidence still shows `NAV_LAND` activating implausibly early even after waypoint spacing and approach acceptance are tightened
- **THEN** the next bounded tuning step MUST be allowed to decouple landing from the appended temporary attack mission and trigger a dedicated landing-only mission after release
- **AND** that handoff MUST remain inside repository-controlled mission upload / sequencing logic rather than FC parameter tuning

#### Scenario: Landing-only handoff must not activate `DO_LAND_START` so early that the approach gate is skipped in practice
- **WHEN** preserved rerun evidence shows a dedicated post-release landing-only mission still entering `LandStart` immediately and then passing the landing approach waypoint from implausibly large distance
- **THEN** the next bounded tuning step MUST be allowed to activate the approach waypoint directly, or otherwise keep `DO_LAND_START` from becoming the first effective post-release target, so the aircraft converges materially closer to the approach gate before `NAV_LAND`
- **AND** that sequencing change MUST remain inside repository-controlled mission upload / activation logic rather than FC parameter tuning

#### Scenario: Landing-only handoff may omit `DO_LAND_START` entirely if direct approach activation still fails to force convergence
- **WHEN** preserved rerun evidence shows that directly activating the landing approach waypoint still allows the aircraft to pass that waypoint from implausibly large distance while a leading `DO_LAND_START` remains in the dedicated landing-only mission
- **THEN** the next bounded tuning step MUST be allowed to remove `DO_LAND_START` from that post-release landing-only mission and rely on the approach waypoint plus `NAV_LAND` to force a materially closer final-approach handoff
- **AND** that sequencing change MUST remain inside repository-controlled mission upload / generation logic rather than FC parameter tuning

#### Scenario: Post-release landing-only tuning must revert marker removal if it regresses into a high-altitude `NAV_LAND` hang
- **WHEN** preserved rerun evidence shows that removing `DO_LAND_START` from the dedicated post-release landing-only mission still leaves the approach waypoint accepted from implausibly large distance and regresses into an above-ground `NAV_LAND` hang
- **THEN** the next bounded tuning step MUST be allowed to restore the prior landing-only mission shape and tighten the remaining repository-controlled post-release approach gating instead of continuing to remove landing markers
- **AND** that follow-up change MUST remain inside mission generation, upload, or state-machine logic owned by this repository

#### Scenario: Landing-only reroute may insert a bounded final-approach gate before `NAV_LAND`
- **WHEN** preserved rerun evidence shows the restored landing-only mission still needs a materially closer final-approach handoff without removing `DO_LAND_START`
- **THEN** the next bounded tuning step MUST be allowed to insert an additional geofence-bounded `NAV_WAYPOINT` between the landing approach waypoint and `NAV_LAND` so the aircraft keeps a usable descending straight-in segment after the first approach gate
- **AND** that follow-up change MUST remain inside mission generation or upload logic owned by this repository rather than FC parameter tuning

#### Scenario: Landing-only handoff may activate the closest effective post-release landing waypoint
- **WHEN** preserved rerun evidence shows the restored landing-only mission still enters `LandStart` first and the earlier landing approach waypoint is accepted from implausibly large distance even after a bounded final-approach gate is inserted
- **THEN** the next bounded tuning step MUST be allowed to keep `DO_LAND_START` in the uploaded mission while activating the closest effective post-release landing waypoint instead of the marker itself, preferring the inserted final-approach gate when present
- **AND** that activation change MUST remain inside repository-controlled mission upload or landing-state logic rather than FC parameter tuning

#### Scenario: `DO_LAND_START` marker semantics must not be treated as the required post-release flown target
- **WHEN** current public ArduPilot behavior still documents `DO_LAND_START` as a landing-sequence marker while the flown autoland geometry begins from subsequent navigation waypoints
- **THEN** the optimization loop MUST be allowed to target the first feasible post-marker landing waypoint instead of forcing post-release activation to the marker itself
- **AND** follow-up tuning MAY preserve both a pre-approach and final-approach waypoint after the marker when preserved evidence shows ArduPlane needs settled entry geometry before `NAV_LAND`

#### Scenario: Successful round 15 landing activation becomes the default post-release baseline until new evidence regresses
- **WHEN** preserved `zjg` evidence shows that activating the inserted post-release final-approach waypoint yields `Landing detected`, mission completion, throttle disarm, and auto disarm in a full closed-loop rerun
- **THEN** that activation rule MUST remain the default repository-controlled landing-only handoff baseline for later rounds
- **AND** later tuning MUST treat touchdown distance, flare quality, or other preserved safety signals as separate optimization targets rather than reverting the validated activation rule without new contrary evidence

#### Scenario: Activated landing-only final-approach gate must not inherit broad default waypoint acceptance
- **WHEN** preserved rerun evidence shows the inserted post-release final-approach gate becoming the activated landing handoff baseline while `NAV_LAND` still begins from implausibly large distance or yields materially poor touchdown offset
- **THEN** the next bounded tuning step MUST be allowed to give that inserted final-approach waypoint an explicit close-in acceptance radius so the aircraft converges materially closer before transitioning into `NAV_LAND`
- **AND** that acceptance change MUST remain inside repository-controlled mission-item generation rather than FC parameter tuning

#### Scenario: Explicit final-approach acceptance tightening must be reverted if it regresses into another above-ground landing hang
- **WHEN** preserved rerun evidence shows that tightening the activated post-release final-approach waypoint acceptance radius still leaves the waypoint accepted from implausibly large distance or regresses the full rerun into a long above-ground `NAV_LAND` hang without `Landing detected`
- **THEN** the next bounded tuning step MUST be allowed to revert that acceptance tightening and preserve the validated round 15 activation baseline while a different repository-controlled landing improvement is investigated
- **AND** the decision MUST be justified from preserved rerun telemetry and mission-phase logs rather than keeping the tighter acceptance rule by default

### Requirement: Software-only flight tuning loop SHALL normalize `zjg` runtime prerequisites before optimization conclusions are trusted
The optimization loop MUST not treat `zjg` runs as valid tuning evidence until the field data and SITL launch inputs are runtime-compatible.

#### Scenario: `zjg` closed-loop runs require runtime-compatible field data
- **WHEN** the optimization workflow selects `--field zjg`
- **THEN** the field coordinates used by runtime mission generation MUST be in the coordinate frame expected by the field loader
- **AND** the SITL launcher/harness MUST use field-appropriate home and params instead of remaining pinned to `sitl_default`
