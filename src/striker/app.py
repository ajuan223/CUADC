"""Striker main application — async mission orchestration.

Initializes all subsystems, creates the mission context and state machine,
then runs the full mission loop via asyncio TaskGroup.
"""

from __future__ import annotations

import argparse
import asyncio
import signal
import sys
from pathlib import Path
from typing import Any

import structlog

from striker.comms.connection import MAVLinkConnection
from striker.comms.heartbeat import HeartbeatMonitor
from striker.config.field_profile import load_field_profile
from striker.config.settings import StrikerSettings
from striker.core.context import MissionContext
from striker.core.machine import MissionStateMachine
from striker.core.states.approach import ApproachState
from striker.core.states.completed import CompletedState
from striker.core.states.emergency import EmergencyState
from striker.core.states.enroute import EnrouteState
from striker.core.states.forced_strike import ForcedStrikeState
from striker.core.states.init import InitState
from striker.core.states.landing import LandingState
from striker.core.states.loiter import LoiterState
from striker.core.states.override import OverrideState
from striker.core.states.preflight import PreflightState
from striker.core.states.release import ReleaseState
from striker.core.states.scan import ScanState
from striker.core.states.takeoff import TakeoffState
from striker.exceptions import ConfigError
from striker.flight.controller import FlightController
from striker.payload.ballistics import BallisticCalculator
from striker.payload.models import ReleaseConfig
from striker.safety.geofence import Geofence
from striker.safety.monitor import SafetyMonitor
from striker.telemetry.flight_recorder import FlightRecorder
from striker.telemetry.logger import configure_logging
from striker.vision.tracker import TargetTracker

logger = structlog.get_logger(__name__)


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
        f"udp:127.0.0.1:14550" if settings.transport == "udp" else settings.serial_port
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
    ballistic_calculator = BallisticCalculator()

    # Geofence from field profile
    geofence = Geofence(field_profile.boundary.polygon)

    # Safety monitor
    safety_monitor = SafetyMonitor(
        geofence=geofence,
        check_interval_s=settings.safety_check_interval_s,
        battery_min_v=settings.battery_min_v,
        stall_speed_m=settings.stall_speed_mps,
    )
    safety_monitor.set_heartbeat_check(lambda: heartbeat_monitor.is_healthy)

    # Vision (placeholder — actual receiver created by factory)
    target_tracker = TargetTracker()
    vision_receiver = _create_vision_receiver_stub(settings)

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
        vision_receiver=vision_receiver,
        target_tracker=target_tracker,
        ballistic_calculator=ballistic_calculator,
        release_controller=release_controller,
        flight_recorder=flight_recorder,
    )

    # State machine
    fsm = MissionStateMachine(rtc=False)
    fsm.register_state_instance("init", InitState())
    fsm.register_state_instance("preflight", PreflightState())
    fsm.register_state_instance("takeoff", TakeoffState())
    fsm.register_state_instance("scan", ScanState())
    fsm.register_state_instance("loiter", LoiterState())
    fsm.register_state_instance("enroute", EnrouteState())
    fsm.register_state_instance("approach", ApproachState())
    fsm.register_state_instance("release", ReleaseState())
    fsm.register_state_instance("landing", LandingState())
    fsm.register_state_instance("completed", CompletedState())
    fsm.register_state_instance("override", OverrideState())
    fsm.register_state_instance("emergency", EmergencyState())
    fsm.register_state_instance("forced_strike", ForcedStrikeState())

    # Run
    shutdown_event = asyncio.Event()

    def _signal_handler(sig: int, frame: Any) -> None:
        logger.info("Shutdown signal received", signal=sig)
        shutdown_event.set()

    signal.signal(signal.SIGINT, _signal_handler)
    signal.signal(signal.SIGTERM, _signal_handler)

    logger.info("Connecting to MAVLink...")
    await connection.connect()

    try:
        async with asyncio.TaskGroup() as tg:
            tg.create_task(connection.run())
            tg.create_task(heartbeat_monitor.run())
            tg.create_task(safety_monitor.run(context))
            tg.create_task(flight_recorder.run(context))
            tg.create_task(fsm.run(context))
            tg.create_task(_shutdown_watcher(shutdown_event, fsm, connection, flight_recorder))
    except* Exception:
        logger.exception("Unhandled exception in task group")
    finally:
        connection.disconnect()
        logger.info("Striker shutdown complete")


async def _shutdown_watcher(
    event: asyncio.Event,
    fsm: MissionStateMachine,
    connection: MAVLinkConnection,
    recorder: FlightRecorder,
) -> None:
    """Watch for shutdown signal and stop all subsystems."""
    await event.wait()
    logger.info("Initiating graceful shutdown")
    fsm.stop()
    recorder.stop()
    connection.disconnect()


def _create_vision_receiver_stub(settings: StrikerSettings) -> Any:
    """Create vision receiver (stub for now)."""
    from striker.vision.tcp_receiver import TcpReceiver

    return TcpReceiver(host=settings.vision_host, port=settings.vision_port)


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
