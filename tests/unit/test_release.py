"""Unit tests for release controllers."""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from striker.exceptions import CommsError
from striker.payload.models import ReleaseConfig


class TestMavlinkRelease:
    @pytest.mark.asyncio
    async def test_sends_do_set_servo(self) -> None:
        from striker.payload.mavlink_release import MavlinkRelease

        conn = MagicMock()
        mock_mav = MagicMock()
        conn._conn = MagicMock()
        conn._conn.mav = mock_mav
        # Make .mav property work
        type(conn).mav = property(lambda self: self._conn.mav)

        config = ReleaseConfig(method="mavlink", channel=6, pwm_open=2000, dry_run=True)
        release = MavlinkRelease(conn=conn, config=config)

        result = await release.release()
        assert result is True
        assert release.is_released

    @pytest.mark.asyncio
    async def test_dry_run_mode(self) -> None:
        from striker.payload.mavlink_release import MavlinkRelease

        conn = MagicMock()
        config = ReleaseConfig(dry_run=True)
        release = MavlinkRelease(conn=conn, config=config)

        await release.arm()
        assert release.is_armed

        result = await release.release()
        assert result is True
        assert release.is_released
    @pytest.mark.asyncio
    async def test_release_blocked_after_autonomy_relinquished(self) -> None:
        from striker.payload.mavlink_release import MavlinkRelease

        conn = MagicMock()
        conn.ensure_autonomy_allowed.side_effect = CommsError("Autonomy relinquished")
        config = ReleaseConfig(method="mavlink", channel=6, pwm_open=2000, dry_run=True)
        release = MavlinkRelease(conn=conn, config=config)

        with pytest.raises(CommsError, match="Autonomy relinquished"):
            await release.release()


class TestGpioRelease:
    @pytest.mark.asyncio
    async def test_gpio_release_dry_run(self) -> None:
        from striker.payload.gpio_release import GpioRelease

        config = ReleaseConfig(method="gpio", gpio_pin=17, dry_run=True)
        release = GpioRelease(config=config)

        await release.arm()
        assert release.is_armed

        result = await release.release()
        assert result is True
        assert release.is_released
