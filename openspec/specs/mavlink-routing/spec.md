## ADDED Requirements

### Requirement: MAVLink routing topology documentation
The project SHALL document a MAVLink routing topology that allows Striker, MAVProxy or mavlink-routerd, and operator tooling to coexist without fighting over the same serial endpoint.

#### Scenario: Document SITL routing topology
- **WHEN** operators read the attack-run dryrun report for SITL
- **THEN** it describes the validated MAVProxy-based topology and the UDP endpoints used by Striker and operator clients

#### Scenario: Document real-flight routing topology
- **WHEN** operators prepare for real deployment
- **THEN** the documentation describes a serial-to-router topology suitable for companion-computer plus ground-station coexistence

### Requirement: MAVProxy startup commands documented
The project SHALL document the concrete startup commands required for the validated routing topologies.

#### Scenario: SITL MAVProxy command is available
- **WHEN** an operator needs to reproduce the validated SITL stack
- **THEN** the documentation includes the exact MAVProxy startup command with the expected `--master` and `--out` endpoints

#### Scenario: Real deployment router command is available
- **WHEN** an operator needs to reproduce the validated real-flight routing setup
- **THEN** the documentation includes the exact router startup command or configuration needed to share the FC link safely
