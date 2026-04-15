# SITL Setup Guide

## Overview

The Software-In-The-Loop (SITL) environment allows running the full Striker
mission stack against a simulated ArduPlane instance — no hardware required.

## Prerequisites

- Linux (Ubuntu 22.04+ recommended)
- Python 3.13+
- `git`, `make`, `gcc`, `g++`

## Setup

```bash
# 1. Install ArduPilot SITL
./scripts/setup_sitl.sh

# 2. Run SITL
./scripts/run_sitl.sh
```

## Running Integration Tests

Integration tests automatically start/stop SITL via the `sitl_fixture`
in `tests/integration/conftest.py`.

```bash
# Run all integration tests
uv run pytest tests/integration/ -v

# Run specific SITL test
uv run pytest tests/integration/test_sitl_connection.py -v
```

## Environment Variables

| Variable | Default | Description |
|---|---|---|
| `ARDUPILOT_DIR` | `~/ardupilot` | Path to ArduPilot checkout |
| `SITL_PORT` | `14550` | UDP port for MAVLink |

## Troubleshooting

- **"arduplane not found"**: Run `./scripts/setup_sitl.sh` first.
- **"Address already in use"**: Kill existing SITL: `pkill -f arduplane`.
- **Heartbeat timeout**: SITL may need a few seconds to start. The fixture waits up to 30s.
