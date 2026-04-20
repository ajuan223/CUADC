## MODIFIED Requirements

### Requirement: Field editor planning workflow SHALL expose fallback drop point and attack preview
The field editor MUST allow operators to place `attack_run.fallback_drop_point` and see the derived attack approach/exit preview associated with that fallback point. The approach heading MUST be calculated using the bearing from the drop point toward the derived landing approach point (matching backend priority 2), falling back to the runway heading when the drop point is within 30m of the approach point (matching backend priority 3). The exit distance MUST be capped so it does not extend beyond the landing approach point, using the same formula as the backend `_calculate_exit_waypoint()`.

#### Scenario: Fallback drop point is visible and exportable
- **WHEN** an operator sets a fallback drop point in the field editor
- **THEN** the editor MUST display the point and derived attack-run preview
- **AND** the exported field profile MUST include the configured fallback drop point

#### Scenario: Approach heading uses bearing toward landing approach
- **WHEN** a fallback drop point is set more than 30m from the derived landing approach point
- **THEN** the approach line MUST be drawn along the bearing from the drop point toward the derived landing approach point
- **AND** the exit line MUST extend in the same heading direction

#### Scenario: Approach heading falls back to runway heading near approach point
- **WHEN** a fallback drop point is set within 30m of the derived landing approach point
- **THEN** the approach line MUST be drawn along the runway heading (reversed)
- **AND** the exit line MUST extend along the runway heading

#### Scenario: Exit distance is capped before landing approach
- **WHEN** the configured exit distance would extend beyond the landing approach point
- **THEN** the exit line MUST be shortened so the exit waypoint does not pass the landing approach point minus a minimum handoff leg of `max(30, min(approach_distance_m, runway_length_m))` meters
