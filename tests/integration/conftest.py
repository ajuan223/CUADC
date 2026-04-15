"""SITL integration test fixtures — auto start/stop ArduPilot SITL."""

from __future__ import annotations

import os
import signal
import subprocess
import time
from pathlib import Path

import pytest


ARDUPILOT_DIR = Path(os.environ.get("ARDUPILOT_DIR", Path.home() / "ardupilot"))
SITL_BIN = ARDUPILOT_DIR / "build" / "sitl" / "bin" / "arduplane"
SITL_PORT = int(os.environ.get("SITL_PORT", "14550"))
SITL_STARTUP_TIMEOUT = 30  # seconds


def _wait_for_udp_port(port: int, timeout: int = SITL_STARTUP_TIMEOUT) -> bool:
    """Wait until a UDP port is reachable."""
    import socket

    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            sock.settimeout(1)
            sock.sendto(b"\x00", ("127.0.0.1", port))
            sock.close()
            return True
        except OSError:
            time.sleep(0.5)
    return False


@pytest.fixture(scope="session")
def sitl_process():
    """Start ArduPlane SITL for the test session, yield PID, then kill."""
    if not SITL_BIN.exists():
        pytest.skip(f"SITL binary not found: {SITL_BIN}. Run scripts/setup_sitl.sh first.")

    cmd = [
        str(SITL_BIN),
        "-S",
        "--model", "plane",
        "--speedup", "1",
        "--instance", "0",
        "--defaults", str(ARDUPILOT_DIR / "Tools" / "autotest" / "default_params" / "plane.parm"),
        "-I", "0",
    ]

    proc = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )

    if not _wait_for_udp_port(SITL_PORT):
        proc.kill()
        pytest.skip(f"SITL failed to start on UDP port {SITL_PORT}")

    yield proc

    # Teardown
    try:
        proc.send_signal(signal.SIGTERM)
        proc.wait(timeout=10)
    except subprocess.TimeoutExpired:
        proc.kill()
