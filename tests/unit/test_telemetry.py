"""Unit tests for telemetry parser."""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from striker.comms.telemetry import (
    AttitudeData,
    BatteryData,
    GeoPosition,
    SpeedData,
    SystemStatus,
    TelemetryParser,
    WindData,
)


def _mock_msg(msg_type: str, **fields: object) -> MagicMock:
    """Create a mock pymavlink message."""
    msg = MagicMock()
    msg.get_type.return_value = msg_type
    for k, v in fields.items():
        setattr(msg, k, v)
    return msg


class TestGeoPosition:
    def test_global_position_int_scale(self) -> None:
        parser = TelemetryParser()
        msg = _mock_msg(
            "GLOBAL_POSITION_INT",
            lat=30_0000000,  # 30.0 deg * 1e7
            lon=120_0000000,  # 120.0 deg * 1e7
            alt=100_000,  # 100m * 1e3
            relative_alt=50_000,  # 50m * 1e3
        )
        result = parser.parse(msg)
        assert isinstance(result, GeoPosition)
        assert result.lat == pytest.approx(30.0)
        assert result.lon == pytest.approx(120.0)
        assert result.alt_m == pytest.approx(100.0)
        assert result.relative_alt_m == pytest.approx(50.0)


class TestAttitudeData:
    def test_attitude_conversion(self) -> None:
        parser = TelemetryParser()
        msg = _mock_msg(
            "ATTITUDE",
            roll=0.1,
            pitch=-0.05,
            yaw=1.57,
        )
        result = parser.parse(msg)
        assert isinstance(result, AttitudeData)
        assert result.roll_rad == pytest.approx(0.1)
        assert result.pitch_rad == pytest.approx(-0.05)
        assert result.yaw_rad == pytest.approx(1.57)


class TestSpeedData:
    def test_vfr_hud_conversion(self) -> None:
        parser = TelemetryParser()
        msg = _mock_msg(
            "VFR_HUD",
            airspeed=15.5,
            groundspeed=14.2,
        )
        result = parser.parse(msg)
        assert isinstance(result, SpeedData)
        assert result.airspeed_mps == pytest.approx(15.5)
        assert result.groundspeed_mps == pytest.approx(14.2)


class TestWindData:
    def test_wind_conversion(self) -> None:
        parser = TelemetryParser()
        msg = _mock_msg(
            "WIND",
            direction=180.0,
            speed=5.5,
        )
        result = parser.parse(msg)
        assert isinstance(result, WindData)
        assert result.direction_deg == pytest.approx(180.0)
        assert result.speed_mps == pytest.approx(5.5)


class TestBatteryData:
    def test_sys_status_conversion(self) -> None:
        parser = TelemetryParser()
        msg = _mock_msg(
            "SYS_STATUS",
            voltage_battery=12_600,  # 12.6V * 1e3
            current_battery=5_00,  # 5.0A * 1e2
            battery_remaining=85,
        )
        result = parser.parse(msg)
        assert isinstance(result, BatteryData)
        assert result.voltage_v == pytest.approx(12.6)
        assert result.current_a == pytest.approx(5.0)
        assert result.remaining_pct == 85

    def test_sys_status_no_current(self) -> None:
        """Current -1 means no data — should default to 0."""
        parser = TelemetryParser()
        msg = _mock_msg(
            "SYS_STATUS",
            voltage_battery=11_100,
            current_battery=-1,
            battery_remaining=50,
        )
        result = parser.parse(msg)
        assert isinstance(result, BatteryData)
        assert result.current_a == pytest.approx(0.0)


class TestSystemStatus:
    def test_heartbeat_conversion(self) -> None:
        parser = TelemetryParser()
        # MAV_MODE_FLAG_SAFETY_ARMED = 128
        msg = _mock_msg(
            "HEARTBEAT",
            custom_mode=3,
            base_mode=217,  # 128 (ARMED) + 89 (other flags)
            system_status=4,
        )
        with pytest.MonkeyPatch.context() as mp:
            mock_mavutil = MagicMock()
            mock_mavutil.mavlink.MAV_MODE_FLAG_SAFETY_ARMED = 128
            mp.setitem(__import__("sys").modules, "pymavlink", MagicMock())
            mp.setitem(__import__("sys").modules, "pymavlink.mavutil", mock_mavutil)

            result = parser.parse(msg)
            assert isinstance(result, SystemStatus)
            assert result.mode == "3"
            assert result.armed is True
            assert result.system_status == 4


class TestUnknownMessage:
    def test_unknown_type_returns_none(self) -> None:
        parser = TelemetryParser()
        msg = _mock_msg("UNKNOWN_TYPE")
        assert parser.parse(msg) is None

    def test_malformed_message_returns_none(self) -> None:
        parser = TelemetryParser()
        msg = _mock_msg("GLOBAL_POSITION_INT")
        del msg.lat  # remove required attribute
        # Should not raise, return None
        assert parser.parse(msg) is None
