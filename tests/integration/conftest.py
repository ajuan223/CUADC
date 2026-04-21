"""SITL integration test fixtures — validated raw SITL + MAVProxy stack."""

from __future__ import annotations

import asyncio
import os
import re
import signal
import socket
import subprocess
import time
from dataclasses import dataclass
from pathlib import Path
from typing import TextIO

import pytest

from striker.config.field_profile import load_field_profile, sitl_home_string, sitl_params_path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
ARDUPILOT_DIR = Path(os.environ.get("ARDUPILOT_DIR", Path.home() / "ardupilot"))
SITL_BIN = ARDUPILOT_DIR / "build" / "sitl" / "bin" / "arduplane"
MAVPROXY_BIN = PROJECT_ROOT / ".venv" / "bin" / "mavproxy.py"
PROJECT_PYTHON = PROJECT_ROOT / ".venv" / "bin" / "python"
FIELDS_DIR = PROJECT_ROOT / "data" / "fields"
PLANE_PARAM = ARDUPILOT_DIR / "Tools" / "autotest" / "models" / "plane.parm"
SITL_TCP_PORT = 5760
MAVPROXY_SITL_PORT = 5501
MAVPROXY_OUT_PORT = 14550
MAVPROXY_GCS_PORT = 14551
STARTUP_TIMEOUT_S = 45.0
FULLCHAIN_TIMEOUT_S = 540.0
ARTIFACT_ROOT = PROJECT_ROOT / "runtime_data" / "integration_runs"
TEST_FIELD_ENV_VAR = "STRIKER_TEST_FIELD"


@dataclass
class ManagedProcess:
    name: str
    proc: subprocess.Popen[bytes]
    log_path: Path
    stream: TextIO
    keep_stdin_open: bool = False


class SITLStack:
    def __init__(self, artifact_dir: Path, *, field: str = "sitl_default") -> None:
        self.artifact_dir = artifact_dir
        self.field = field
        self.field_profile = load_field_profile(field, base_dir=FIELDS_DIR)
        self.field_home = sitl_home_string(self.field_profile)
        self.field_param = sitl_params_path(field, base_dir=FIELDS_DIR)
        self.expected_home_log = _expected_home_log_line(self.field_home)
        self.sitl_log = artifact_dir / "sitl.log"
        self.mavproxy_log = artifact_dir / "mavproxy.log"
        self.striker_log = artifact_dir / "striker.log"
        self.vision_log = artifact_dir / "vision.log"
        self.flight_log_path = artifact_dir / "flight_log.csv"
        self.vision_port = _pick_free_tcp_port()
        self._processes: list[ManagedProcess] = []
        self._sitl: ManagedProcess | None = None
        self._mavproxy: ManagedProcess | None = None
        self._striker: ManagedProcess | None = None
        self._vision: ManagedProcess | None = None

    def start(self) -> None:
        _wait_for_tcp_port_closed(SITL_TCP_PORT, timeout=15.0)
        self._sitl = self._start_process(
            name="sitl",
            cmd=[
                str(SITL_BIN),
                "-w",
                "--model",
                "plane",
                "--speedup",
                "1",
                "-I",
                "0",
                "--home",
                self.field_home,
                "--defaults",
                str(self.field_param),
                "--defaults",
                str(PLANE_PARAM),
                "--sim-address=127.0.0.1",
            ],
            log_path=self.sitl_log,
        )
        if not _wait_for_tcp_port(SITL_TCP_PORT, timeout=STARTUP_TIMEOUT_S):
            raise AssertionError(f"SITL TCP port {SITL_TCP_PORT} did not open\n{self.log_tail(self.sitl_log)}")
        _wait_for_log_sync(
            self.sitl_log,
            [self.expected_home_log],
            timeout=STARTUP_TIMEOUT_S,
            process=self._sitl.proc,
        )

        self._mavproxy = self._start_process(
            name="mavproxy",
            cmd=[
                str(MAVPROXY_BIN),
                "--master",
                f"tcp:127.0.0.1:{SITL_TCP_PORT}",
                "--sitl",
                f"127.0.0.1:{MAVPROXY_SITL_PORT}",
                "--out",
                f"udp:127.0.0.1:{MAVPROXY_OUT_PORT}",
                "--out",
                f"udp:127.0.0.1:{MAVPROXY_GCS_PORT}",
                "--daemon",
            ],
            log_path=self.mavproxy_log,
            keep_stdin_open=True,
        )
        _wait_for_log_sync(
            self.mavproxy_log,
            ["Waiting for heartbeat from tcp:127.0.0.1:5760"],
            timeout=10.0,
            process=self._mavproxy.proc,
        )
        if self._mavproxy.proc.stdin is not None:
            self._mavproxy.proc.stdin.write(b"\n")
            self._mavproxy.proc.stdin.flush()
        _wait_for_log_sync(
            self.sitl_log,
            ["Loaded defaults from /home/xbp/ardupilot/Tools/autotest/models/plane.parm"],
            timeout=STARTUP_TIMEOUT_S,
            process=self._sitl.proc,
        )

    def start_striker(self, *, dry_run: bool = False, field: str | None = None) -> None:
        if self._striker is not None:
            raise RuntimeError("Striker already started")
        cmd = [str(PROJECT_PYTHON), "-u", "-m", "striker", "--field", field or self.field]
        if dry_run:
            cmd.append("--dry-run")
        env = {
            "PYTHONUNBUFFERED": "1",
            "STRIKER_TRANSPORT": "udp",
            "STRIKER_ARM_FORCE_BYPASS": "1",
            "STRIKER_RECORDER_OUTPUT_PATH": str(self.flight_log_path),
            "STRIKER_VISION_PORT": str(self.vision_port),
        }
        self._striker = self._start_process(
            name="striker",
            cmd=cmd,
            log_path=self.striker_log,
            env=env,
        )
        _wait_for_log_sync(
            self.striker_log,
            ["Striker starting"],
            timeout=20.0,
            process=self._striker.proc,
        )

    def start_mock_vision(
        self,
        *,
        no_drop_point: bool = False,
        drop_point: tuple[float, float] | None = None,
    ) -> None:
        if self._vision is not None:
            raise RuntimeError("Mock vision already started")
        cmd = [
            str(PROJECT_PYTHON),
            "-u",
            str(PROJECT_ROOT / "scripts" / "mock_vision_server.py"),
            "--host",
            "127.0.0.1",
            "--port",
            str(self.vision_port),
            "--interval",
            "1.0",
        ]
        if drop_point is not None:
            cmd.extend(["--lat", str(drop_point[0]), "--lon", str(drop_point[1])])
        if no_drop_point:
            cmd.append("--no-drop-point")
        self._vision = self._start_process(
            name="vision",
            cmd=cmd,
            log_path=self.vision_log,
            env={"PYTHONUNBUFFERED": "1"},
        )
        _wait_for_log_sync(
            self.vision_log,
            ["Connected to striker vision receiver"],
            timeout=20.0,
            process=self._vision.proc,
        )

    async def wait_for_striker_patterns(
        self,
        patterns: list[str],
        *,
        timeout: float = FULLCHAIN_TIMEOUT_S,
        ordered: bool = True,
    ) -> str:
        if self._striker is None:
            raise RuntimeError("Striker not started")
        return await _wait_for_log_async(
            self.striker_log,
            patterns,
            timeout=timeout,
            ordered=ordered,
            process=self._striker.proc,
        )

    async def wait_for_artifact(self, path: Path, *, timeout: float = 30.0) -> None:
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            if path.exists() and path.stat().st_size > 0:
                return
            if self._striker and self._striker.proc.poll() is not None:
                break
            await asyncio.sleep(1.0)
        raise AssertionError(f"Expected artifact not written: {path}\n{self.log_tail(self.striker_log)}")

    async def inject_manual_override(self) -> None:
        from striker.comms.connection import MAVLinkConnection
        from striker.flight.controller import FlightController
        from striker.flight.modes import ArduPlaneMode

        conn = MAVLinkConnection(url=f"udp:127.0.0.1:{MAVPROXY_GCS_PORT}")
        try:
            await conn.connect()
            controller = FlightController(conn)
            await controller.set_mode(ArduPlaneMode.MANUAL)
        finally:
            conn.disconnect()

    def read_text(self, path: Path) -> str:
        if not path.exists():
            return ""
        return path.read_text(encoding="utf-8", errors="ignore")

    def log_tail(self, path: Path, *, lines: int = 80) -> str:
        text = self.read_text(path)
        tail = "\n".join(text.splitlines()[-lines:])
        return f"Artifact dir: {self.artifact_dir}\n{tail}"

    def stop(self) -> None:
        self._stop_process(self._vision, sig=signal.SIGTERM)
        self._stop_process(self._striker, sig=signal.SIGINT)
        self._stop_process(self._mavproxy, sig=signal.SIGTERM)
        self._stop_process(self._sitl, sig=signal.SIGTERM)

    def _start_process(
        self,
        *,
        name: str,
        cmd: list[str],
        log_path: Path,
        env: dict[str, str] | None = None,
        keep_stdin_open: bool = False,
    ) -> ManagedProcess:
        log_path.parent.mkdir(parents=True, exist_ok=True)
        stream = log_path.open("w", encoding="utf-8")
        proc = subprocess.Popen(
            cmd,
            cwd=str(PROJECT_ROOT),
            env={**os.environ, **(env or {})},
            stdout=stream,
            stderr=subprocess.STDOUT,
            stdin=subprocess.PIPE if keep_stdin_open else subprocess.DEVNULL,
        )
        managed = ManagedProcess(
            name=name,
            proc=proc,
            log_path=log_path,
            stream=stream,
            keep_stdin_open=keep_stdin_open,
        )
        self._processes.append(managed)
        return managed

    def _stop_process(self, managed: ManagedProcess | None, *, sig: int) -> None:
        if managed is None:
            return
        try:
            if managed.proc.poll() is None:
                managed.proc.send_signal(sig)
                try:
                    managed.proc.wait(timeout=15)
                except subprocess.TimeoutExpired:
                    managed.proc.kill()
                    managed.proc.wait(timeout=5)
        finally:
            managed.stream.close()


@pytest.fixture()
def sitl_process(request: pytest.FixtureRequest) -> SITLStack:  # type: ignore
    field = _requested_test_field(request)
    missing = _missing_prerequisites(field)
    if missing:
        pytest.skip("SITL prerequisites missing: " + "; ".join(missing))

    ARTIFACT_ROOT.mkdir(parents=True, exist_ok=True)
    name = _sanitize_node_name(request.node.nodeid)
    artifact_dir = ARTIFACT_ROOT / field / f"{name}-{int(time.time() * 1000)}"
    stack = SITLStack(artifact_dir, field=field)
    stack.start()
    try:
        yield stack
    finally:
        stack.stop()


def _missing_prerequisites(field: str) -> list[str]:
    missing: list[str] = []
    if not SITL_BIN.exists():
        missing.append(f"missing SITL binary: {SITL_BIN}")
    field_param = sitl_params_path(field, base_dir=FIELDS_DIR)
    if not field_param.exists():
        missing.append(f"missing field params for {field}: {field_param}")
    if not PLANE_PARAM.exists():
        missing.append(f"missing plane params: {PLANE_PARAM}")
    if not MAVPROXY_BIN.exists():
        missing.append(f"missing repo-local MAVProxy: {MAVPROXY_BIN}")
    if not PROJECT_PYTHON.exists():
        missing.append(f"missing project python: {PROJECT_PYTHON}")
    return missing


def _sanitize_node_name(nodeid: str) -> str:
    return re.sub(r"[^A-Za-z0-9._-]+", "-", nodeid).strip("-") or "sitl-run"


def _requested_test_field(request: pytest.FixtureRequest) -> str:
    marker = request.node.get_closest_marker("field")
    if marker is not None:
        if not marker.args or not isinstance(marker.args[0], str) or not marker.args[0].strip():
            raise ValueError("@pytest.mark.field requires a non-empty field name")
        return str(marker.args[0]).strip()
    return os.environ.get(TEST_FIELD_ENV_VAR, "sitl_default")


def _expected_home_log_line(field_home: str) -> str:
    lat, lon, *_ = field_home.split(",")
    return f"Home: {float(lat):.6f} {float(lon):.6f}"


def _wait_for_tcp_port(port: int, *, timeout: float) -> bool:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.settimeout(1.0)
            if sock.connect_ex(("127.0.0.1", port)) == 0:
                return True
        time.sleep(0.5)
    return False


def _pick_free_tcp_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("127.0.0.1", 0))
        return int(sock.getsockname()[1])


def _wait_for_tcp_port_closed(port: int, *, timeout: float) -> None:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.settimeout(1.0)
            if sock.connect_ex(("127.0.0.1", port)) != 0:
                return
        time.sleep(0.5)
    raise AssertionError(f"TCP port {port} remained busy before SITL startup")


def _patterns_present(content: str, patterns: list[str], *, ordered: bool) -> bool:
    if ordered:
        cursor = 0
        for pattern in patterns:
            idx = content.find(pattern, cursor)
            if idx < 0:
                return False
            cursor = idx + len(pattern)
        return True
    return all(pattern in content for pattern in patterns)


def _read_text(path: Path) -> str:
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8", errors="ignore")


def _tail_text(path: Path, *, lines: int = 80) -> str:
    return "\n".join(_read_text(path).splitlines()[-lines:])


def _process_failed(process: subprocess.Popen[bytes] | None) -> bool:
    return process is not None and process.poll() not in (None, 0)


def _wait_for_log_sync(
    path: Path,
    patterns: list[str],
    *,
    timeout: float,
    ordered: bool = True,
    process: subprocess.Popen[bytes] | None = None,
) -> str:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        content = _read_text(path)
        if _patterns_present(content, patterns, ordered=ordered):
            return content
        if _process_failed(process):
            break
        time.sleep(0.5)
    raise AssertionError(f"Timed out waiting for {patterns} in {path}\n{_tail_text(path)}")


async def _wait_for_log_async(
    path: Path,
    patterns: list[str],
    *,
    timeout: float,
    ordered: bool = True,
    process: subprocess.Popen[bytes] | None = None,
) -> str:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        content = _read_text(path)
        if _patterns_present(content, patterns, ordered=ordered):
            return content
        if _process_failed(process):
            break
        await asyncio.sleep(1.0)
    raise AssertionError(f"Timed out waiting for {patterns} in {path}\n{_tail_text(path)}")
