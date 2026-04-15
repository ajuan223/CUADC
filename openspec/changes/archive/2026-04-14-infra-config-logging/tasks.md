## 1. Package Structure

- [x] 1.1 Create `src/striker/config/__init__.py` package init (re-export StrikerSettings, Platform, detect_platform)
- [x] 1.2 Create `src/striker/telemetry/__init__.py` package init (re-export configure_logging)

## 2. Exception Hierarchy Extension

- [x] 2.1 Add `FieldValidationError(StrikerError)` to `src/striker/exceptions.py` — carries field_name, reason, and composite message

## 3. Configuration System (StrikerSettings)

- [x] 3.1 Create `src/striker/config/settings.py` — `StrikerSettings(BaseSettings)` with all fields (serial_port, serial_baud, loiter_radius_m, loiter_timeout_s, max_scan_cycles, forced_strike_enabled, field, dry_run, log_level) and code defaults
- [x] 3.2 Implement `settings_customise_sources()` — enforce three-layer priority: init_settings → env_settings → JsonConfigSettingsSource → file_secret_settings
- [x] 3.3 Create `src/striker/config/validators.py` — pydantic validators for physical quantity ranges (serial_baud > 0, loiter_radius_m > 0, loiter_timeout_s > 0)

## 4. Platform Detection

- [x] 4.1 Create `src/striker/config/platform.py` — `Platform` enum (RPi5, Orin, SITL, Unknown) and `detect_platform()` function checking STRIKER_PLATFORM env → MAVLINK_SITL env → /proc/device-tree/model → /etc/nv_tegra_release

## 5. Logging Framework

- [x] 5.1 Create `src/striker/telemetry/logger.py` — `configure_logging(level)` with fixed processor chain (merge_contextvars → add_log_level → TimeStamper(iso, utc) → format_exc_info → dict_tracebacks), TTY-aware renderer selection, `make_filtering_bound_logger`, `cache_logger_on_first_use=True`

## 6. Field Profile Data Model

- [x] 6.1 Create `src/striker/config/field_profile.py` — nested pydantic models: `GeoPoint`, `BoundaryConfig`, `ApproachWaypoint`, `TouchdownPoint`, `LandingConfig`, `ScanWaypointsConfig`, `LoiterPointConfig`, `FieldProfile(BaseModel)`
- [x] 6.2 Implement polygon auto-close logic — if first != last vertex, append first vertex
- [x] 6.3 Implement `point_in_polygon(lat, lon, polygon)` — ray casting algorithm
- [x] 6.4 Implement `validate_waypoints_in_geofence()` — validate scan_waypoints, landing points, and loiter point are inside boundary polygon, raise `FieldValidationError` on violation
- [x] 6.5 Implement `load_field_profile(name, base_dir)` — load from `data/fields/{name}/field.json`, return validated `FieldProfile`, raise `ConfigError` on file not found

## 7. Config Template Update

- [x] 7.1 Update `config.example.json` — add all Phase 2 fields with descriptive comment in `$schema`

## 8. Unit Tests

- [x] 8.1 Create `tests/unit/test_config.py` — test three-layer priority (default < json < env), STRIKER_ prefix, missing config file graceful handling, physical quantity validation errors
- [x] 8.2 Create `tests/unit/test_platform.py` — test SITL detection via MAVLINK_SITL, RPi5 detection mock, Orin detection mock, Unknown fallback, STRIKER_PLATFORM override
- [x] 8.3 Create `tests/unit/test_field_profile.py` — test valid field load, missing file error, invalid JSON error, polygon auto-close, point_in_polygon, waypoint outside fence rejection, landing outside fence rejection, loiter outside fence rejection, safety_buffer_m validation

## 9. Verification

- [x] 9.1 Run `ruff check src/striker/config/ src/striker/telemetry/ src/striker/exceptions.py` — zero errors
- [x] 9.2 Run `mypy --strict src/striker/config/ src/striker/telemetry/ src/striker/exceptions.py` — zero errors
- [x] 9.3 Run `pytest tests/unit/` — all tests pass
