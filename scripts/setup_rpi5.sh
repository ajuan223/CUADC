#!/usr/bin/env bash
# setup_rpi5.sh — Deploy Striker to Raspberry Pi 5.
set -euo pipefail

echo "==> Setting up Striker on RPi5"

# Install system dependencies
sudo apt-get update
sudo apt-get install -y python3.13 python3.13-venv python3-pip git

# Install uv
curl -LsSf https://astral.sh/uv/install.sh | sh

# Clone and install
cd /opt/striker
uv sync

# Configure systemd service
cat <<EOF | sudo tee /etc/systemd/system/striker.service
[Unit]
Description=Striker Autonomous Flight Control
After=network.target

[Service]
Type=simple
User=striker
WorkingDirectory=/opt/striker
ExecStart=/home/striker/.local/bin/uv run python -m striker
Restart=on-failure
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl daemon-reload
sudo systemctl enable striker
echo "==> RPi5 setup complete. Start with: sudo systemctl start striker"
