## ADDED Requirements

### Requirement: MAVLink routing topology documentation
The system SHALL provide deployment documentation describing the MAVLink routing topology that allows MissionPlanner (GCS) and the striker companion computer to simultaneously connect to the flight controller.

#### Scenario: SITL routing topology documented
- **WHEN** a developer reads the deployment documentation
- **THEN** the SITL topology is described: `arduplane (TCP:5760) → MAVProxy → UDP:14550 (striker) + UDP:14551 (MissionPlanner/GCS)`

#### Scenario: Real deployment routing topology documented
- **WHEN** a developer reads the deployment documentation
- **THEN** the real deployment topology is described: `flight controller (serial) → MAVProxy/mavlink-routerd → UDP:14550 (striker) + UDP:14551 (MissionPlanner via telemetry/WiFi)`

---

### Requirement: MAVProxy startup commands documented
The system SHALL provide copy-paste-ready MAVProxy and mavlink-routerd startup commands for both SITL and real deployment scenarios in the deployment documentation.

#### Scenario: SITL MAVProxy startup
- **WHEN** a developer follows the SITL setup guide
- **THEN** the documented command starts MAVProxy bridging TCP:5760 to UDP:14550 and UDP:14551

#### Scenario: Real deployment MAVProxy startup
- **WHEN** an operator follows the real deployment guide
- **THEN** the documented command starts MAVProxy bridging `/dev/serial0` to UDP:14550 and UDP:14551 with correct baud rate
