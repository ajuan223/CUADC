## ADDED Requirements

### Requirement: Mock vision server SHALL send drop point coordinates
A `scripts/mock_vision_server.py` script SHALL listen on TCP port 9876 (configurable) and periodically send mock drop point coordinates as JSON `{"lat": <float>, "lon": <float>}` messages. The drop point SHALL be inside the `sitl_default` geofence boundary.

#### Scenario: Mock server sends valid drop point
- **WHEN** mock_vision_server.py is running and a client connects to TCP 9876
- **THEN** the server sends a JSON message containing lat/lon coordinates within the test field boundary (lat 30.2600-30.2700, lon 120.0900-120.1000)

#### Scenario: Mock server sends at configurable interval
- **WHEN** mock_vision_server.py runs with `--interval 2.0`
- **THEN** a new drop point message is sent every 2.0 seconds

#### Scenario: Mock server supports no-drop-point mode
- **WHEN** mock_vision_server.py runs with `--no-drop-point`
- **THEN** no drop point message is sent, simulating the "vision did not provide a point" scenario

### Requirement: Scan waypoints SHALL be loaded from field profile
The `data/fields/sitl_default/field.json` scan waypoints SHALL be used as the mock scan pattern. These waypoints are already defined and validated against the geofence boundary. No additional mock is needed.

#### Scenario: Field profile scan waypoints load correctly
- **WHEN** `load_field_profile("sitl_default")` is called
- **THEN** the returned profile contains 8 scan waypoints, all inside the geofence, at altitude 80m

### Requirement: Mock drop point SHALL be configurable
The mock vision server SHALL accept CLI arguments to control the drop point location: `--lat`, `--lon` for fixed coordinates, or `--random` for a random point inside the geofence.

#### Scenario: Fixed drop point
- **WHEN** mock_vision_server.py runs with `--lat 30.2660 --lon 120.0950`
- **THEN** every sent message contains exactly these coordinates

#### Scenario: Random drop point inside geofence
- **WHEN** mock_vision_server.py runs with `--random`
- **THEN** each sent message contains coordinates validated to be inside the field boundary polygon

### Requirement: Mock server SHALL log all sent messages
The mock vision server SHALL log each sent drop point message with timestamp and coordinates using structlog, enabling correlation with striker logs.

#### Scenario: Sent messages are logged
- **WHEN** the mock server sends a drop point
- **THEN** a log line appears with the sent coordinates and timestamp
