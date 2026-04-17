"""Three-layer configuration system for Striker.

Priority (lowest → highest): code defaults → config.json → environment variables.
Environment variable prefix: ``STRIKER_`` (e.g. ``STRIKER_SERIAL_PORT``).
"""

from pydantic_settings import BaseSettings, JsonConfigSettingsSource, PydanticBaseSettingsSource, SettingsConfigDict

from striker.config.validators import _positive_int


class StrikerSettings(BaseSettings):
    """Global configuration model — three-layer priority."""

    model_config = SettingsConfigDict(
        env_prefix="STRIKER_",
        json_file="config.json",
        json_file_encoding="utf-8",
    )

    # ── Serial / MAVLink ─────────────────────────────────────────
    serial_port: str = "/dev/TTYAMA0"
    serial_baud: int = 921600
    transport: str = "serial"  # "serial" or "udp"
    mavlink_url: str = ""  # override: e.g. "udp:127.0.0.1:14550"

    # ── Safety thresholds ─────────────────────────────────────────
    battery_min_v: float = 11.1
    stall_speed_mps: float = 10.0
    heartbeat_timeout_s: float = 3.0
    safety_check_interval_s: float = 1.0

    # ── Mission behaviour ─────────────────────────────────────────
    field: str = "zjg"
    dry_run: bool = False
    arm_force_bypass: bool = False

    # ── Release config ────────────────────────────────────────────
    release_method: str = "mavlink"  # "mavlink" or "gpio"
    release_channel: int = 6
    release_pwm_open: int = 2000
    release_pwm_close: int = 1000
    release_gpio_pin: int = 17
    release_gpio_active_high: bool = True

    # ── Vision config ─────────────────────────────────────────────
    vision_receiver_type: str = "tcp"  # "tcp" or "udp"
    vision_host: str = "0.0.0.0"
    vision_port: int = 9876

    # ── Flight recorder ───────────────────────────────────────────
    recorder_output_path: str = "flight_log.csv"
    recorder_sample_rate_hz: float = 1.0

    # ── Logging ───────────────────────────────────────────────────
    log_level: str = "INFO"

    # ── Validators ────────────────────────────────────────────────
    _ = _positive_int("serial_baud")

    @classmethod
    def settings_customise_sources(
        cls,
        settings_cls: type[BaseSettings],
        init_settings: PydanticBaseSettingsSource,
        env_settings: PydanticBaseSettingsSource,
        dotenv_settings: PydanticBaseSettingsSource,
        file_secret_settings: PydanticBaseSettingsSource,
    ) -> tuple[PydanticBaseSettingsSource, ...]:
        """Enforce three-layer priority: init defaults < JSON file < environment variables.

        In pydantic-settings, sources listed later in the tuple override earlier ones.
        With this order, the effective priority is init < json < env.
        """
        return (
            init_settings,
            env_settings,
            JsonConfigSettingsSource(settings_cls),
            file_secret_settings,
        )
