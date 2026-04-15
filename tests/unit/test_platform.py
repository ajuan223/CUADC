"""Unit tests — Platform detection."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

import pytest

from striker.config.platform import Platform, detect_platform


class TestDetectPlatform:
    def test_sitl_via_mavlink_env(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.delenv("STRIKER_PLATFORM", raising=False)
        monkeypatch.setenv("MAVLINK_SITL", "1")
        assert detect_platform() == Platform.SITL

    def test_rpi5_via_proc_model(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.delenv("STRIKER_PLATFORM", raising=False)
        monkeypatch.delenv("MAVLINK_SITL", raising=False)

        def mock_read_text(self: Path, encoding: str = "utf-8") -> str:
            return "Raspberry Pi 5 Model B Rev 1.0\x00"

        with patch.object(Path, "read_text", mock_read_text), patch.object(Path, "exists", return_value=True):
            assert detect_platform() == Platform.RPi5

    def test_orin_via_nv_tegra(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Orin is detected when /etc/nv_tegra_release exists and RPi check fails."""
        monkeypatch.delenv("STRIKER_PLATFORM", raising=False)
        monkeypatch.delenv("MAVLINK_SITL", raising=False)

        def selective_exists(self: Path) -> bool:
            path_str = str(self)
            if "nv_tegra" in path_str:
                return True
            if "device-tree" in path_str:
                return False
            return False

        with (
            patch.object(Path, "read_text", side_effect=FileNotFoundError),
            patch.object(Path, "exists", selective_exists),
        ):
            assert detect_platform() == Platform.Orin

    def test_unknown_fallback(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.delenv("STRIKER_PLATFORM", raising=False)
        monkeypatch.delenv("MAVLINK_SITL", raising=False)

        with (
            patch("striker.config.platform.Path") as mock_path_cls,
        ):
            instance = mock_path_cls.return_value
            instance.read_text.side_effect = FileNotFoundError
            instance.exists.return_value = False

            mock_path_cls.side_effect = lambda *a, **kw: instance
            assert detect_platform() == Platform.Unknown

    def test_striker_platform_override(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("STRIKER_PLATFORM", "sitl")
        assert detect_platform() == Platform.SITL

    def test_striker_platform_override_rpi5(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("STRIKER_PLATFORM", "rpi5")
        assert detect_platform() == Platform.RPi5

    def test_striker_platform_override_unknown_value(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("STRIKER_PLATFORM", "invalid")
        assert detect_platform() == Platform.Unknown
