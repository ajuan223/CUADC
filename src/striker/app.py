"""Striker main application — async mission orchestration.

Initializes all subsystems, creates the mission context and state machine,
then runs the full mission loop via asyncio TaskGroup.
"""

from __future__ import annotations

import argparse
import asyncio
import contextlib
import signal
import sys
from typing import Any, Protocol, cast

import structlog

from striker.comms.connection import MAVLinkConnection
from striker.comms.heartbeat import HeartbeatMonitor
from striker.comms.messages import (
    HEARTBEAT,
    MAV_CMD_SET_MESSAGE_INTERVAL,
    MAVLINK_MSG_ID_MISSION_CURRENT,
    MAVLINK_MSG_ID_MISSION_ITEM_REACHED,
    MISSION_CURRENT,
    MISSION_ITEM_REACHED,
    STATUSTEXT,
)
from striker.comms.telemetry import AttitudeData, BatteryData, GeoPosition, SpeedData, SystemStatus, WindData
from striker.config.field_profile import load_field_profile
from striker.config.settings import StrikerSettings
from striker.core.context import MissionContext
from striker.core.events import SystemEvent
from striker.core.machine import MissionStateMachine
from striker.core.states.completed import CompletedState
from striker.core.states.emergency import EmergencyState
from striker.core.states.guided_strike import GuidedStrikeState
from striker.core.states.init import InitState
from striker.core.states.landing_monitor import LandingMonitorState
from striker.core.states.override import OverrideState
from striker.core.states.release_monitor import ReleaseMonitorState
from striker.core.states.scan_monitor import ScanMonitorState
from striker.core.states.standby import StandbyState
from striker.exceptions import ConfigError
from striker.flight.controller import FlightController
from striker.payload.models import ReleaseConfig
from striker.safety.geofence import Geofence
from striker.safety.monitor import SafetyMonitor
from striker.telemetry.flight_recorder import FlightRecorder
from striker.telemetry.logger import configure_logging

logger = structlog.get_logger(__name__)


class _MissionSeqMessage(Protocol):
    seq: int


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    """Parse CLI arguments."""
    parser = argparse.ArgumentParser(description="Striker autonomous flight control")
    parser.add_argument("--field", default=None, help="Field profile name (overrides config)")
    parser.add_argument("--dry-run", action="store_true", default=None, help="Dry run mode")
    parser.add_argument("--list-fields", action="store_true", help="List available field profiles")
    return parser.parse_args(argv)


async def main(argv: list[str] | None = None) -> None:
    """Main async entry point."""
    args = parse_args(argv)

    # Load settings
    settings = StrikerSettings()
    if args.field:
        settings.field = args.field
    if args.dry_run:
        settings.dry_run = True

    # Configure logging
    configure_logging(settings.log_level)
    logger.info("Striker starting", version="0.1.0", field=settings.field, dry_run=settings.dry_run)

    # Load field profile
    try:
        field_profile = load_field_profile(settings.field)
    except (ConfigError, Exception) as exc:
        logger.critical("Field profile validation failed", error=str(exc))
        sys.exit(1)

    logger.info("Field profile loaded", name=field_profile.name)

    # Determine MAVLink URL
    url = settings.mavlink_url or (
        "udp:127.0.0.1:14550" if settings.transport == "udp" else settings.serial_port
    )

    # Initialize subsystems
    connection = MAVLinkConnection(
        url=url,
        baud=settings.serial_baud,
        heartbeat_timeout_s=settings.heartbeat_timeout_s,
    )
    heartbeat_monitor = HeartbeatMonitor(
        conn=connection,
        receive_timeout_s=settings.heartbeat_timeout_s,
    )
    flight_controller = FlightController(connection)

    # Geofence from field profile
    geofence = Geofence(field_profile.boundary.polygon)

    # Safety monitor
    safety_monitor = SafetyMonitor(
        geofence=geofence,
        check_interval_s=settings.safety_check_interval_s,
        battery_min_v=settings.battery_min_v,
        stall_speed_mps=settings.stall_speed_mps,
        buffer_m=field_profile.safety_buffer_m,
    )
    safety_monitor.set_heartbeat_check(lambda: heartbeat_monitor.is_healthy)


    # Release controller
    release_config = ReleaseConfig(
        method=settings.release_method,
        channel=settings.release_channel,
        pwm_open=settings.release_pwm_open,
        pwm_close=settings.release_pwm_close,
        gpio_pin=settings.release_gpio_pin,
        gpio_active_high=settings.release_gpio_active_high,
        dry_run=settings.dry_run,
    )
    release_controller = _create_release_controller(release_config, connection)

    # Flight recorder
    flight_recorder = FlightRecorder(
        output_path=settings.recorder_output_path,
        sample_rate_hz=settings.recorder_sample_rate_hz,
    )

    # Mission context
    context = MissionContext(
        settings=settings,
        field_profile=field_profile,
        connection=connection,
        heartbeat_monitor=heartbeat_monitor,
        flight_controller=flight_controller,
        safety_monitor=safety_monitor,
        release_controller=release_controller,
        flight_recorder=flight_recorder,
    )

    # State machine
    fsm = MissionStateMachine(rtc=False)
    fsm.register_state_instance("init", InitState())
    fsm.register_state_instance("standby", StandbyState())
    fsm.register_state_instance("scan_monitor", ScanMonitorState())
    fsm.register_state_instance("guided_strike", GuidedStrikeState())
    fsm.register_state_instance("release_monitor", ReleaseMonitorState())
    fsm.register_state_instance("landing_monitor", LandingMonitorState())
    fsm.register_state_instance("completed", CompletedState())
    fsm.register_state_instance("override", OverrideState())
    fsm.register_state_instance("emergency", EmergencyState())

    # Connect safety events to FSM (F-03)
    def _dispatch_safety_event(event: Any) -> None:
        fsm.create_background_task(fsm.process_event(event))

    safety_monitor.set_event_callback(_dispatch_safety_event)

    connection.register_message_callback(
        lambda message: _handle_connection_message(context, heartbeat_monitor, fsm, message),
    )

    # Run
    shutdown_event = asyncio.Event()
    cleanup_started = asyncio.Event()
    _install_signal_handlers(shutdown_event)

    logger.info("Connecting to MAVLink...")
    try:
        connect_task = asyncio.create_task(connection.connect())
        shutdown_task = asyncio.create_task(shutdown_event.wait())
        done, pending = await asyncio.wait(
            {connect_task, shutdown_task},
            return_when=asyncio.FIRST_COMPLETED,
        )

        for task in pending:
            task.cancel()
        for task in pending:
            with contextlib.suppress(asyncio.CancelledError):
                await task

        if shutdown_task in done and shutdown_event.is_set():
            if not connect_task.done():
                connect_task.cancel()
                with contextlib.suppress(asyncio.CancelledError):
                    await connect_task
            return

        await connect_task
        heartbeat_monitor.seed_healthy()
        _request_mission_progress_streams(connection)

        async with asyncio.TaskGroup() as tg:
            tg.create_task(connection.run())
            tg.create_task(heartbeat_monitor.run())
            tg.create_task(safety_monitor.run(context))
            tg.create_task(flight_recorder.run(context))
            tg.create_task(fsm.run(context))
            tg.create_task(
                _shutdown_watcher(
                    event=shutdown_event,
                    cleanup_started=cleanup_started,
                    fsm=fsm,
                    heartbeat_monitor=heartbeat_monitor,
                    safety_monitor=safety_monitor,
                    connection=connection,
                    recorder=flight_recorder,
                ),
            )
    except* Exception:
        logger.exception("Unhandled exception in task group")
    finally:
        await _shutdown_app(
            cleanup_started=cleanup_started,
            fsm=fsm,
            heartbeat_monitor=heartbeat_monitor,
            safety_monitor=safety_monitor,
            connection=connection,
            recorder=flight_recorder,
        )
        logger.info("Striker shutdown complete")





def _request_mission_progress_streams(connection: MAVLinkConnection) -> None:
    """Request mission-progress messages explicitly after link startup."""
    mav = connection.mav
    for message_id, name in (
        (MAVLINK_MSG_ID_MISSION_CURRENT, MISSION_CURRENT),
        (MAVLINK_MSG_ID_MISSION_ITEM_REACHED, MISSION_ITEM_REACHED),
    ):
        connection.command_long_send(
            mav.target_system,
            mav.target_component,
            MAV_CMD_SET_MESSAGE_INTERVAL,
            0,
            float(message_id),
            500_000.0,
            0,
            0,
            0,
            0,
            0,
        )
        logger.info("Requested mission progress stream", message_type=name, message_id=message_id, interval_us=500000)


def _handle_connection_message(
    context: MissionContext,
    heartbeat_monitor: HeartbeatMonitor,
    fsm: MissionStateMachine,
    message: object,
) -> None:
    """Update mission context and liveness state from received MAVLink traffic."""
    if hasattr(message, "get_type") and message.get_type() == HEARTBEAT:
        heartbeat_monitor.notify_heartbeat_received()
        if fsm.current_state_name == "init":
            fsm.create_background_task(fsm.process_event(SystemEvent.INIT_COMPLETE))
        return

    # Mission progress: raw MAVLink messages for MISSION_CURRENT and MISSION_ITEM_REACHED
    if hasattr(message, "get_type"):
        msg_type = message.get_type()
        if msg_type == MISSION_CURRENT:
            context.update_mission_current_seq(cast(_MissionSeqMessage, message).seq)
            return
        if msg_type == MISSION_ITEM_REACHED:
            context.update_mission_item_reached_seq(cast(_MissionSeqMessage, message).seq)
            return
        if msg_type == STATUSTEXT:
            context.update_status_text(getattr(message, "text", ""))
            return

    if isinstance(message, GeoPosition):
        context.update_position(message)
    elif isinstance(message, AttitudeData):
        context.update_attitude(message)
    elif isinstance(message, SpeedData):
        context.update_speed(message)
    elif isinstance(message, WindData):
        context.update_wind(message)
    elif isinstance(message, BatteryData):
        context.update_battery(message)
    elif isinstance(message, SystemStatus):
        context.update_system_status(message)


def _install_signal_handlers(event: asyncio.Event) -> None:
    """Register process signal handlers that trigger shutdown."""

    def _signal_handler(sig: int, frame: Any) -> None:
        logger.info("Shutdown signal received", signal=sig)
        event.set()

    signal.signal(signal.SIGINT, _signal_handler)
    signal.signal(signal.SIGTERM, _signal_handler)


async def _shutdown_watcher(
    event: asyncio.Event,
    cleanup_started: asyncio.Event,
    fsm: MissionStateMachine,
    heartbeat_monitor: HeartbeatMonitor,
    safety_monitor: SafetyMonitor,
    connection: MAVLinkConnection,
    recorder: FlightRecorder,
) -> None:
    """Watch for shutdown signal and stop all subsystems."""
    await event.wait()
    logger.info("Initiating graceful shutdown")
    await _shutdown_app(
        cleanup_started=cleanup_started,
        fsm=fsm,
        heartbeat_monitor=heartbeat_monitor,
        safety_monitor=safety_monitor,
        connection=connection,
        recorder=recorder,
    )


async def _shutdown_app(
    cleanup_started: asyncio.Event,
    fsm: MissionStateMachine,
    heartbeat_monitor: HeartbeatMonitor,
    safety_monitor: SafetyMonitor,
    connection: MAVLinkConnection,
    recorder: FlightRecorder,
) -> None:
    """Stop started subsystems and release owned resources exactly once."""
    if cleanup_started.is_set():
        return
    cleanup_started.set()

    fsm.stop()
    heartbeat_monitor.stop()
    safety_monitor.stop()
    recorder.stop()

    connection.disconnect()





def _create_release_controller(config: ReleaseConfig, conn: MAVLinkConnection) -> Any:
    """Create release controller from config."""
    if config.method == "mavlink":
        from striker.payload.mavlink_release import MavlinkRelease

        return MavlinkRelease(conn=conn, config=config)
    elif config.method == "gpio":
        from striker.payload.gpio_release import GpioRelease

        return GpioRelease(config=config)
    else:
        msg = f"Unknown release method: {config.method}"
        raise ValueError(msg)


def run(argv: list[str] | None = None) -> None:
    """Synchronous entry point."""
    asyncio.run(main(argv))
