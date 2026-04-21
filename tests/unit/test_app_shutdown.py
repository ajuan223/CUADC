"""Unit tests for app shutdown orchestration."""

from __future__ import annotations

import asyncio
from unittest.mock import AsyncMock, MagicMock

import pytest

from striker.app import _shutdown_app, _shutdown_watcher


class TestAppShutdown:
    @pytest.mark.asyncio
    async def test_shutdown_app_stops_all_subsystems_once(self) -> None:
        cleanup_started = asyncio.Event()
        fsm = MagicMock()
        heartbeat_monitor = MagicMock()
        safety_monitor = MagicMock()
        connection = MagicMock()
        recorder = MagicMock()

        await _shutdown_app(
            cleanup_started=cleanup_started,
            fsm=fsm,
            heartbeat_monitor=heartbeat_monitor,
            safety_monitor=safety_monitor,
            connection=connection,
            recorder=recorder,
        )

        assert cleanup_started.is_set()
        fsm.stop.assert_called_once_with()
        heartbeat_monitor.stop.assert_called_once_with()
        safety_monitor.stop.assert_called_once_with()
        recorder.stop.assert_called_once_with()
        connection.disconnect.assert_called_once_with()

    @pytest.mark.asyncio
    async def test_shutdown_app_is_idempotent(self) -> None:
        cleanup_started = asyncio.Event()
        cleanup_started.set()
        fsm = MagicMock()
        heartbeat_monitor = MagicMock()
        safety_monitor = MagicMock()
        connection = MagicMock()
        recorder = MagicMock()

        await _shutdown_app(
            cleanup_started=cleanup_started,
            fsm=fsm,
            heartbeat_monitor=heartbeat_monitor,
            safety_monitor=safety_monitor,
            connection=connection,
            recorder=recorder,
        )

        fsm.stop.assert_not_called()
        heartbeat_monitor.stop.assert_not_called()
        safety_monitor.stop.assert_not_called()
        recorder.stop.assert_not_called()
        connection.disconnect.assert_not_called()

    @pytest.mark.asyncio
    async def test_shutdown_watcher_stops_all_subsystems_after_event(self) -> None:
        shutdown_event = asyncio.Event()
        cleanup_started = asyncio.Event()
        fsm = MagicMock()
        heartbeat_monitor = MagicMock()
        safety_monitor = MagicMock()
        connection = MagicMock()
        recorder = MagicMock()

        task = asyncio.create_task(
            _shutdown_watcher(
                event=shutdown_event,
                cleanup_started=cleanup_started,
                fsm=fsm,
                heartbeat_monitor=heartbeat_monitor,
                safety_monitor=safety_monitor,
                connection=connection,
                recorder=recorder,
            ),
        )

        await asyncio.sleep(0)
        shutdown_event.set()
        await task

        assert cleanup_started.is_set()
        fsm.stop.assert_called_once_with()
        heartbeat_monitor.stop.assert_called_once_with()
        safety_monitor.stop.assert_called_once_with()
        recorder.stop.assert_called_once_with()
        connection.disconnect.assert_called_once_with()
