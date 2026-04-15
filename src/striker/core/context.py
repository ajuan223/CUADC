"""Mission context — shared state container for all subsystems."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

import structlog

from striker.comms.telemetry import BatteryData, GeoPosition, SpeedData, SystemStatus, WindData

if TYPE_CHECKING:
    from striker.comms.connection import MAVLinkConnection
    from striker.comms.heartbeat import HeartbeatMonitor
    from striker.config.field_profile import FieldProfile
    from striker.config.settings import StrikerSettings
    from striker.flight.controller import FlightController
    from striker.payload.ballistics import BallisticCalculator
    from striker.payload.protocol import ReleaseController
    from striker.safety.monitor import SafetyMonitor
    from striker.telemetry.flight_recorder import FlightRecorder
    from striker.vision.protocol import VisionReceiver
    from striker.vision.tracker import TargetTracker

logger = structlog.get_logger(__name__)


class MissionContext:
    """Shared state container holding references to all subsystems.

    Created once during app startup and passed to all states.
    """

    def __init__(
        self,
        settings: StrikerSettings,
        field_profile: FieldProfile,
        connection: MAVLinkConnection,
        heartbeat_monitor: HeartbeatMonitor,
        flight_controller: FlightController,
        safety_monitor: SafetyMonitor,
        vision_receiver: VisionReceiver,
        target_tracker: TargetTracker,
        ballistic_calculator: BallisticCalculator,
        release_controller: ReleaseController,
        flight_recorder: FlightRecorder,
    ) -> None:
        self.settings = settings
        self.field_profile = field_profile
        self.connection = connection
        self.heartbeat_monitor = heartbeat_monitor
        self.flight_controller = flight_controller
        self.safety_monitor = safety_monitor
        self.vision_receiver = vision_receiver
        self.target_tracker = target_tracker
        self.ballistic_calculator = ballistic_calculator
        self.release_controller = release_controller
        self.flight_recorder = flight_recorder

        # Mutable mission state
        self.current_position: GeoPosition | None = None
        self.current_speed: SpeedData | None = None
        self.current_wind: WindData | None = None
        self.current_battery: BatteryData | None = None
        self.current_system_status: SystemStatus | None = None
        self.scan_cycle_count: int = 0
        self.landing_sequence_start_index: int | None = None
        self.last_target: Any = None

    def update_position(self, pos: GeoPosition) -> None:
        """Update current position from telemetry."""
        self.current_position = pos

    def update_speed(self, speed: SpeedData) -> None:
        """Update current speed from telemetry."""
        self.current_speed = speed

    def update_wind(self, wind: WindData) -> None:
        """Update current wind from telemetry."""
        self.current_wind = wind

    def update_battery(self, battery: BatteryData) -> None:
        """Update current battery from telemetry."""
        self.current_battery = battery

    def update_system_status(self, status: SystemStatus) -> None:
        """Update current system status from telemetry."""
        self.current_system_status = status

    def update_target(self, target: Any) -> None:
        """Update latest target from vision system."""
        self.last_target = target
        logger.info("Target updated", target=str(target))
