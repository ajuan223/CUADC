"""SITL full mission integration tests."""

from __future__ import annotations

import asyncio
from pathlib import Path

import pytest

from striker.config.field_profile import GeoPoint
from striker.flight.mission_geometry import generate_mission_geometry
from striker.utils.fallback_drop_point import compute_fallback_drop_point


async def _wait_for_and_assert_flight_log(sitl_process, *, timeout: float = 30.0) -> None:  # type: ignore
    await sitl_process.wait_for_artifact(sitl_process.flight_log_path, timeout=timeout)
    content = sitl_process.read_text(sitl_process.flight_log_path)
    assert "timestamp,lat,lon,alt_m,relative_alt_m" in content
    assert len(content.splitlines()) > 1, sitl_process.log_tail(sitl_process.flight_log_path)


class TestSITLFullMission:
    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_normal_path_vision(self, sitl_process) -> None:  # type: ignore
        """Normal path with vision: ARM→TAKEOFF→SCAN→ENROUTE→RELEASE→LANDING→COMPLETED."""
        sitl_process.start_striker(dry_run=False)
        await sitl_process.wait_for_striker_patterns([
            "MAVLink connected",
            "Vision receiver started",
        ], timeout=60.0)
        field_geometry = generate_mission_geometry(sitl_process.field_profile)
        vision_drop_point = (
            field_geometry.landing_approach[0],
            field_geometry.landing_approach[1],
        )
        sitl_process.start_mock_vision(drop_point=vision_drop_point)

        await sitl_process.wait_for_striker_patterns(
            [
                "Preflight: mission uploaded",
                "Target altitude reached",
                "Scan complete",
                "Using vision drop point",
                "Attack mission uploaded",
                "Attack run initiated",
                "Payload released (native DO_SET_SERVO)",
                "Landing detected",
                "Mission completed successfully!",
            ],
        )
        await _wait_for_and_assert_flight_log(sitl_process)

    @pytest.mark.asyncio
    @pytest.mark.integration
    @pytest.mark.field("zjg")
    async def test_zjg_normal_path_vision(self, sitl_process) -> None:  # type: ignore
        """ZJG vision path: use a field-local vision target so attack geometry stays inside the field."""
        sitl_process.start_striker(dry_run=False)
        await sitl_process.wait_for_striker_patterns([
            "MAVLink connected",
            "Vision receiver started",
        ], timeout=60.0)
        field_geometry = generate_mission_geometry(sitl_process.field_profile)
        scan_end = GeoPoint(
            lat=field_geometry.scan_waypoints[-1][0],
            lon=field_geometry.scan_waypoints[-1][1],
        )
        landing_ref = sitl_process.field_profile.landing.touchdown_point
        vision_drop_point = compute_fallback_drop_point(scan_end, landing_ref)
        sitl_process.start_mock_vision(drop_point=vision_drop_point)

        await sitl_process.wait_for_striker_patterns(
            [
                "Preflight: mission uploaded",
                "Target altitude reached",
                "Scan complete",
                "Using vision drop point",
                "Attack mission uploaded",
                "Attack run initiated",
                "Payload released (native DO_SET_SERVO)",
                "Landing detected",
                "Mission completed successfully!",
            ],
        )
        await _wait_for_and_assert_flight_log(sitl_process)

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_normal_path_fallback(self, sitl_process) -> None:  # type: ignore
        """Fallback path: no vision → SCAN→fallback midpoint→ENROUTE→RELEASE→LANDING→COMPLETED."""
        sitl_process.start_striker(dry_run=False)
        await sitl_process.wait_for_striker_patterns([
            "MAVLink connected",
            "Vision receiver started",
        ], timeout=60.0)
        sitl_process.start_mock_vision(no_drop_point=True)

        await sitl_process.wait_for_striker_patterns(
            [
                "Preflight: mission uploaded",
                "Target altitude reached",
                "Scan complete",
                "Using fallback midpoint drop point",
                "Attack mission uploaded",
                "Attack run initiated",
                "Payload released (native DO_SET_SERVO)",
                "Landing detected",
                "Mission completed successfully!",
            ],
        )
        await _wait_for_and_assert_flight_log(sitl_process)

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_human_override(self, sitl_process) -> None:  # type: ignore
        """Human override: manual mode switch → OVERRIDE detection."""
        sitl_process.start_striker(dry_run=False)
        await sitl_process.wait_for_striker_patterns([
            "MAVLink connected",
            "Vision receiver started",
            "Preflight: mission uploaded",
            "Target altitude reached",
        ], timeout=120.0)

        await sitl_process.inject_manual_override()
        await sitl_process.wait_for_striker_patterns(
            [
                "Autonomy relinquished",
                "Human override",
            ],
            timeout=30.0,
            ordered=False,
        )
        await _wait_for_and_assert_flight_log(sitl_process)

        await asyncio.sleep(5.0)
        striker_log = sitl_process.read_text(sitl_process.striker_log)
        assert "Mission completed successfully!" not in striker_log, (
            sitl_process.log_tail(sitl_process.striker_log)
        )
        assert "Payload released (native DO_SET_SERVO)" not in striker_log, (
            sitl_process.log_tail(sitl_process.striker_log)
        )

    @pytest.mark.asyncio
    @pytest.mark.integration
    @pytest.mark.field("zjg")
    async def test_field_profile_loading(self, sitl_process) -> None:  # type: ignore
        """Field profile loading at startup."""
        from striker.config.field_profile import load_field_profile

        profile = load_field_profile("zjg")
        assert profile.name == "zjg"
        assert Path(sitl_process.artifact_dir).exists()
        assert "zjg" in str(sitl_process.artifact_dir)
