"""Mission context — shared state container for all subsystems."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

import structlog

from striker.comms.telemetry import AttitudeData, BatteryData, GeoPosition, SpeedData, SystemStatus, WindData

if TYPE_CHECKING:
    from striker.comms.connection import MAVLinkConnection
    from striker.comms.heartbeat import HeartbeatMonitor
    from striker.config.field_profile import FieldProfile, GeoPoint
    from striker.config.settings import StrikerSettings
    from striker.flight.controller import FlightController
    from striker.payload.protocol import ReleaseController
    from striker.safety.monitor import SafetyMonitor
    from striker.telemetry.flight_recorder import FlightRecorder
    from striker.vision.protocol import VisionReceiver
    from striker.vision.tracker import DropPointTracker

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
        drop_point_tracker: DropPointTracker,
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
        self.drop_point_tracker = drop_point_tracker
        self.release_controller = release_controller
        self.flight_recorder = flight_recorder

        # Mutable mission state
        self.current_position: GeoPosition | None = None
        self.current_attitude: AttitudeData | None = None
        self.current_speed: SpeedData | None = None
        self.current_wind: WindData | None = None
        self.current_battery: BatteryData | None = None
        self.current_system_status: SystemStatus | None = None
        self.last_status_text: str = ""
        self.landing_sequence_start_index: int | None = None
        self.scan_end_seq: int | None = None
        self.attack_geometry: Any | None = None

        # Drop point state
        self.active_drop_point: tuple[float, float] | None = None
        self.drop_point_source: str = ""  # "vision" or "fallback_midpoint"
        self.mission_current_seq: int = 0
        self.mission_item_reached_seq: int = -1

    def update_position(self, pos: GeoPosition) -> None:
        """Update current position from telemetry."""
        self.current_position = pos

    def update_attitude(self, attitude: AttitudeData) -> None:
        """Update current attitude from telemetry."""
        self.current_attitude = attitude

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

    def update_status_text(self, text: str) -> None:
        """Update latest STATUSTEXT payload for state-level observability."""
        self.last_status_text = text

    def update_mission_current_seq(self, seq: int) -> None:
        """Update current active mission sequence from MISSION_CURRENT."""
        self.mission_current_seq = seq
        logger.debug("Mission current updated", seq=seq)

    def update_mission_item_reached_seq(self, seq: int) -> None:
        """Update last reached mission sequence from MISSION_ITEM_REACHED."""
        self.mission_item_reached_seq = seq
        logger.debug("Mission item reached updated", seq=seq)

    def set_drop_point(self, lat: float, lon: float, source: str) -> None:
        """Set the active drop point with its source annotation."""
        self.active_drop_point = (lat, lon)
        self.drop_point_source = source
        logger.info("Drop point set", lat=lat, lon=lon, source=source)

    @property
    def last_scan_waypoint(self) -> GeoPoint | None:
        """Return the last generated scan waypoint, or None."""
        from striker.config.field_profile import GeoPoint as GP
        from striker.flight.mission_geometry import generate_boustrophedon_scan

        scan_cfg = self.field_profile.scan
        boundary = self.field_profile.boundary.polygon
        if len(boundary) < 3:
            return None
        boundary_tuples = [(p.lat, p.lon) for p in boundary]
        wps = generate_boustrophedon_scan(
            boundary_polygon=boundary_tuples,
            scan_alt_m=scan_cfg.altitude_m,
            scan_spacing_m=scan_cfg.spacing_m,
            scan_heading_deg=scan_cfg.heading_deg,
        )
        if not wps:
            return None
        lat, lon, _ = wps[-1]
        return GP(lat=lat, lon=lon)
