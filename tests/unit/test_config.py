"""Unit tests — Striker configuration system."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest
from pydantic import ValidationError

from striker.config.settings import StrikerSettings

# ── Helpers ───────────────────────────────────────────────────────


def _write_config(tmp_path: Path, data: dict[str, Any]) -> Path:
    """Write *data* as JSON config to *tmp_path*/config.json and return path."""
    cfg = tmp_path / "config.json"
    cfg.write_text(json.dumps(data), encoding="utf-8")
    return cfg


# ── Three-layer priority ──────────────────────────────────────────


class TestThreeLayerPriority:
    """Layer 1 (defaults) < Layer 2 (JSON file) < Layer 3 (env vars)."""

    def test_defaults_used_when_no_overrides(self) -> None:
        settings = StrikerSettings()
        assert settings.serial_port == "/dev/serial0"
        assert settings.serial_baud == 921600
        assert settings.dry_run is False
        assert settings.field == "sitl_default"
        assert settings.log_level == "INFO"

    def test_json_overrides_defaults(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        _write_config(tmp_path, {"serial_port": "/dev/ttyUSB0", "dry_run": True})
        monkeypatch.chdir(tmp_path)
        settings = StrikerSettings()
        assert settings.serial_port == "/dev/ttyUSB0"
        assert settings.dry_run is True

    def test_env_overrides_json(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        _write_config(tmp_path, {"serial_port": "/dev/ttyUSB0"})
        monkeypatch.chdir(tmp_path)
        monkeypatch.setenv("STRIKER_SERIAL_PORT", "/dev/ttyACM0")
        settings = StrikerSettings()
        assert settings.serial_port == "/dev/ttyACM0"

    def test_env_prefix_striker(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("STRIKER_DRY_RUN", "true")
        settings = StrikerSettings()
        assert settings.dry_run is True

    def test_field_env_override(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("STRIKER_FIELD", "zijingang")
        settings = StrikerSettings()
        assert settings.field == "zijingang"

    def test_missing_config_file_ok(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.chdir(tmp_path)
        settings = StrikerSettings()
        assert settings.serial_port == "/dev/serial0"


# ── Physical quantity validators ──────────────────────────────────


class TestValidators:
    def test_zero_baud_rejected(self) -> None:
        with pytest.raises(ValidationError):
            StrikerSettings(serial_baud=0)

    def test_negative_baud_rejected(self) -> None:
        with pytest.raises(ValidationError):
            StrikerSettings(serial_baud=-1)

    def test_zero_loiter_radius_rejected(self) -> None:
        with pytest.raises(ValidationError):
            StrikerSettings(loiter_radius_m=0.0)

    def test_negative_loiter_timeout_rejected(self) -> None:
        with pytest.raises(ValidationError):
            StrikerSettings(loiter_timeout_s=-5.0)
