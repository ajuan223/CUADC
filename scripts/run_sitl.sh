#!/usr/bin/env bash
# run_sitl.sh — One-click SITL + MAVProxy launch for ArduPlane.
#
# Usage: ./scripts/run_sitl.sh [field_name]
# Environment: ARDUPILOT_DIR — path to ArduPilot checkout (default: ~/ardupilot)

set -euo pipefail

ARDUPILOT_DIR="${ARDUPILOT_DIR:-$HOME/ardupilot}"
SITL_PORT="${SITL_PORT:-14550}"
FIELD="${1:-sitl_default}"

echo "==> Launching ArduPlane SITL on UDP:${SITL_PORT}"

cd "${ARDUPILOT_DIR}"

# Launch SITL in background
"${ARDUPILOT_DIR}/build/sitl/bin/arduplane" \
    -S \
    --model plane \
    --speedup 1 \
    --instance 0 \
    --defaults "${ARDUPILOT_DIR}/Tools/autotest/default_params/plane.parm" \
    -I 0 \
    --uart0 tcp:0 \
    &>/tmp/arduplane_sitl.log &

SITL_PID=$!
echo "==> SITL PID: ${SITL_PID}"
echo "==> Waiting for SITL to start..."
sleep 5

echo "==> SITL running. MAVLink on udp:127.0.0.1:${SITL_PORT}"
echo "==> To stop: kill ${SITL_PID}"
echo "==> Log: /tmp/arduplane_sitl.log"

# Wait for SITL to exit
wait "${SITL_PID}" 2>/dev/null || true
