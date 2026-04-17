## MODIFIED Requirements

### Requirement: Strike full-chain validation SHALL cover iterative optimization rounds on the selected field profile
The project MUST provide runnable validation for the full SITL mission chain from startup through mission completion, and it MUST support repeated optimization rounds on the selected field profile rather than only a one-off `sitl_default` validation.

#### Scenario: Normal strike path completes end-to-end on the optimization field
- **WHEN** the validated SITL stack is available and a full-chain optimization validation runs for `zjg`
- **THEN** the run MUST assert successful startup and mission upload
- **AND** it MUST verify the ordered mission progression through `preflight`, `takeoff`, `scan`, `enroute`, `release`, and `landing`
- **AND** it MUST verify that the run reaches its intended terminal outcome with preserved artifacts for later round-to-round comparison
- **AND** the temporary attack mission used for the strike handoff MUST be allowed to use a software-controlled altitude that better matches the derived landing approach when the optimization loop is explicitly reducing landing-window energy

#### Scenario: Missing optimization-field SITL prerequisites stop the round with an actionable reason
- **WHEN** the required local SITL stack prerequisites for the selected optimization field are unavailable or incompatible in a development environment
- **THEN** the full-chain optimization validation MUST stop rather than fail ambiguously
- **AND** it MUST report which prerequisite prevented a meaningful `zjg` run, such as missing merged params, mismatched home configuration, or incompatible field-coordinate data
