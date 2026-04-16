### Requirement: SITL environment SHALL start with sim_vehicle.py
The dry-run SHALL use `sim_vehicle.py -v ArduPlane -L Zijingang -w` as the SITL startup command. This starts arduplane SITL with MAVProxy, which automatically creates UDP outputs at `127.0.0.1:14550` and `127.0.0.1:14551`. Striker connects to `udp:127.0.0.1:14550`.

#### Scenario: SITL starts and MAVProxy creates UDP outputs
- **WHEN** running `sim_vehicle.py -v ArduPlane -L Zijingang -w`
- **THEN** SITL process starts, MAVProxy process starts, UDP 14550 is reachable, pymavlink `wait_heartbeat()` succeeds

#### Scenario: Zijingang location available
- **WHEN** `$HOME/.config/ardupilot/locations.txt` contains `Zijingang=30.265,120.095,0,0`
- **THEN** SITL starts at those GPS coordinates and GLOBAL_POSITION_INT reports lat/lon within 0.001 degrees of 30.265, 120.095

### Requirement: MAVProxy SHALL be installed
MAVProxy SHALL be installed in the project `.venv` via `pip install MAVProxy`. It is required by sim_vehicle.py as the default GCS and creates the UDP outputs that striker connects to.

#### Scenario: MAVProxy installed and functional
- **WHEN** running `pip install MAVProxy` in the project `.venv`
- **THEN** `mavproxy.py --version` succeeds and sim_vehicle.py can use it

### Requirement: SITL binary SHALL be pre-built
`~/ardupilot/build/sitl/bin/arduplane` SHALL exist and be executable. If missing, build via `sim_vehicle.py -v ArduPlane --build`.

#### Scenario: Binary exists
- **WHEN** checking `test -x ~/ardupilot/build/sitl/bin/arduplane`
- **THEN** the check succeeds

### Requirement: conftest.py SHALL reference correct paths
`tests/integration/conftest.py` SHALL use correct parameter file paths and port checking logic for the chosen SITL startup method.

#### Scenario: conftest fixture starts SITL correctly
- **WHEN** running the sitl_process fixture
- **THEN** SITL starts without parameter file errors and the correct port (TCP 5760 for raw binary or UDP 14550 for sim_vehicle.py) becomes reachable

### Requirement: Striker SHALL connect to SITL via MAVProxy UDP output
The striker application SHALL connect using `STRIKER_MAVLINK_URL=udp:127.0.0.1:14550` and complete the connection handshake before entering PREFLIGHT state.

#### Scenario: Successful connection
- **WHEN** striker starts with MAVLink URL `udp:127.0.0.1:14550` and SITL+MAVProxy are running
- **THEN** the log shows "MAVLink connected" with target_system and target_component

#### Scenario: Connection timeout
- **WHEN** SITL or MAVProxy is not running
- **THEN** striker reports connection failure within `heartbeat_timeout_s`
