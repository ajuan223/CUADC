#!/usr/bin/env bash
# setup_sitl.sh — Install ArduPilot SITL environment for integration testing.
#
# Prerequisites: git, python3, pip
# Usage: ./scripts/setup_sitl.sh [--skip-build]

set -euo pipefail

ARDUPILOT_DIR="${ARDUPILOT_DIR:-$HOME/ardupilot}"
SKIP_BUILD="${1:-}"

echo "==> Setting up ArduPilot SITL at ${ARDUPILOT_DIR}"

if [ ! -d "${ARDUPILOT_DIR}" ]; then
    echo "==> Cloning ArduPilot..."
    git clone --depth 1 https://github.com/ArduPilot/ardupilot.git "${ARDUPILOT_DIR}"
fi

cd "${ARDUPILOT_DIR}"

echo "==> Updating submodules..."
git submodule update --init --recursive

if [ "${SKIP_BUILD}" != "--skip-build" ]; then
    echo "==> Building ArduPlane SITL..."
    ./waf configure --board sitl
    ./waf build --target bin/arduplane
    echo "==> SITL build complete."
else
    echo "==> Skipping build (--skip-build)."
fi

echo "==> SITL setup done. Run: ./scripts/run_sitl.sh"
