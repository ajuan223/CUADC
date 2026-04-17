#!/usr/bin/env bash
# run_sitl.sh — validated raw ArduPlane SITL + repo-local MAVProxy launcher.
#
# Usage: ./scripts/run_sitl.sh [field_name]
# Environment: ARDUPILOT_DIR — path to ArduPilot checkout (default: ~/ardupilot)

set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
ARDUPILOT_DIR="${ARDUPILOT_DIR:-$HOME/ardupilot}"
FIELD="${1:-sitl_default}"
RUN_STAMP_FULL="$(date +%Y%m%d_%H%M%S)"
RUN_STAMP_SHORT="$(date +%y%m%d_%H%M%S)"
SITL_BIN="${ARDUPILOT_DIR}/build/sitl/bin/arduplane"
PLANE_PARAM="${ARDUPILOT_DIR}/Tools/autotest/models/plane.parm"
MAVPROXY_BIN="${PROJECT_ROOT}/.venv/bin/mavproxy.py"
ARTIFACT_DIR="${PROJECT_ROOT}/runtime_data/manual_sitl/${FIELD}/${RUN_STAMP_FULL}"
FLIGHT_LOG_DIR="${PROJECT_ROOT}/runtime_data/flight_logs/${FIELD}"
FLIGHT_LOG="${FLIGHT_LOG_DIR}/flight_log_${RUN_STAMP_SHORT}.csv"
SITL_LOG="${ARTIFACT_DIR}/sitl.log"
MAVPROXY_LOG="${ARTIFACT_DIR}/mavproxy.log"
STRIKER_LOG="${ARTIFACT_DIR}/striker.log"
readarray -t FIELD_RUNTIME <<<"$(FIELD="${FIELD}" PROJECT_ROOT="${PROJECT_ROOT}" python3 - <<'PY'
from pathlib import Path
import os
import sys

sys.path.insert(0, os.environ["PROJECT_ROOT"] + "/src")
from striker.config.field_profile import load_field_profile, sitl_home_string, sitl_params_path

field = os.environ["FIELD"]
base_dir = Path(os.environ["PROJECT_ROOT"]) / "data" / "fields"
profile = load_field_profile(field, base_dir=base_dir)
print(sitl_home_string(profile))
print(sitl_params_path(field, base_dir=base_dir))
PY
)"
FIELD_HOME="${FIELD_RUNTIME[0]}"
FIELD_PARAM="${FIELD_RUNTIME[1]}"

mkdir -p "${ARTIFACT_DIR}" "${FLIGHT_LOG_DIR}"

if [[ ! -x "${SITL_BIN}" ]]; then
  echo "Missing SITL binary: ${SITL_BIN}" >&2
  exit 1
fi
if [[ ! -f "${PLANE_PARAM}" ]]; then
  echo "Missing plane params: ${PLANE_PARAM}" >&2
  exit 1
fi
if [[ ! -f "${FIELD_PARAM}" ]]; then
  echo "Missing field params: ${FIELD_PARAM}" >&2
  exit 1
fi
if [[ ! -x "${MAVPROXY_BIN}" ]]; then
  echo "Missing repo-local MAVProxy: ${MAVPROXY_BIN}" >&2
  exit 1
fi
if ! command -v uv >/dev/null 2>&1; then
  echo "Missing uv in PATH" >&2
  exit 1
fi

cleanup() {
  local code=$?
  if [[ -n "${STRIKER_PID:-}" ]] && kill -0 "${STRIKER_PID}" 2>/dev/null; then
    kill "${STRIKER_PID}" 2>/dev/null || true
    wait "${STRIKER_PID}" 2>/dev/null || true
  fi
  if [[ -n "${MAVPROXY_PID:-}" ]] && kill -0 "${MAVPROXY_PID}" 2>/dev/null; then
    kill "${MAVPROXY_PID}" 2>/dev/null || true
    wait "${MAVPROXY_PID}" 2>/dev/null || true
  fi
  if [[ -n "${SITL_PID:-}" ]] && kill -0 "${SITL_PID}" 2>/dev/null; then
    kill "${SITL_PID}" 2>/dev/null || true
    wait "${SITL_PID}" 2>/dev/null || true
  fi
  exit "${code}"
}
trap cleanup EXIT INT TERM

echo "==> Launching ArduPlane SITL"
"${SITL_BIN}" \
  -w --model plane --speedup 1 -I 0 \
  --home "${FIELD_HOME}" \
  --defaults "${FIELD_PARAM}" \
  --defaults "${PLANE_PARAM}" \
  --sim-address=127.0.0.1 \
  >"${SITL_LOG}" 2>&1 &
SITL_PID=$!

EXPECTED_HOME="$(FIELD_HOME="${FIELD_HOME}" python3 - <<'PY'
import os
lat, lon, alt, heading = os.environ["FIELD_HOME"].split(",")
print(f"Home: {float(lat):.6f} {float(lon):.6f}")
PY
)"

echo "==> Waiting for SITL TCP 5760"
for _ in $(seq 1 60); do
  if python3 - <<'PY'
import socket
sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
sock.settimeout(0.5)
try:
    raise SystemExit(0 if sock.connect_ex(("127.0.0.1", 5760)) == 0 else 1)
finally:
    sock.close()
PY
  then
    break
  fi
  sleep 1
done

grep -a "${EXPECTED_HOME}" "${SITL_LOG}" >/dev/null || {
  echo "SITL did not report the validated field home (${EXPECTED_HOME})" >&2
  exit 1
}

echo "==> Launching MAVProxy from project .venv"
"${MAVPROXY_BIN}" \
  --master tcp:127.0.0.1:5760 \
  --sitl 127.0.0.1:5501 \
  --out udp:127.0.0.1:14550 \
  --out udp:127.0.0.1:14551 \
  --daemon \
  >"${MAVPROXY_LOG}" 2>&1 &
MAVPROXY_PID=$!

echo "==> Waiting for MAVProxy ready signal"
for _ in $(seq 1 60); do
  if grep -a "AP: ArduPilot Ready" "${MAVPROXY_LOG}" >/dev/null 2>&1; then
    break
  fi
  sleep 1
done

echo "==> Launching Striker"
(
  cd "${PROJECT_ROOT}"
  STRIKER_TRANSPORT=udp \
  STRIKER_RECORDER_OUTPUT_PATH="${FLIGHT_LOG}" \
  uv run python -m striker --field "${FIELD}"
) >"${STRIKER_LOG}" 2>&1 &
STRIKER_PID=$!

echo "==> Stack ready"
echo "    SITL log: ${SITL_LOG}"
echo "    MAVProxy log: ${MAVPROXY_LOG}"
echo "    Striker log: ${STRIKER_LOG}"
echo "    Flight log: ${FLIGHT_LOG}"
echo "    Artifact dir: ${ARTIFACT_DIR}"

wait "${STRIKER_PID}"
