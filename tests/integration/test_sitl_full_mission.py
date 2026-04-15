"""SITL full mission integration tests."""

from __future__ import annotations

import pytest

import asyncio


class TestSITLFullMission:
    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_normal_path(self, sitl_process) -> None:
        """Normal path: ARM→TAKEOFF→SCAN→LOITER→ENROUTE→APPROACH→RELEASE(dry)→LANDING→COMPLETED."""
        # This test requires full SITL setup — stub for now
        pytest.skip("Full mission SITL test requires ArduPilot SITL setup")

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_degradation_path(self, sitl_process) -> None:
        """Degradation: 3x LOITER timeout → FORCED_STRIKE → LANDING → COMPLETED."""
        pytest.skip("Degradation path test requires ArduPilot SITL setup")

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_human_override(self, sitl_process) -> None:
        """Human override: manual mode switch → OVERRIDE detection."""
        pytest.skip("Override test requires ArduPilot SITL setup")

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_field_profile_loading(self, sitl_process) -> None:
        """Field profile loading at startup."""
        from striker.config.field_profile import load_field_profile

        profile = load_field_profile("sitl_default")
        assert profile.name is not None
