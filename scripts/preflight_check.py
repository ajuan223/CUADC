#!/usr/bin/env python3
"""Preflight check — standalone validation before flight."""

from __future__ import annotations

import sys

from striker.config.field_profile import load_field_profile
from striker.config.settings import StrikerSettings
from striker.exceptions import ConfigError


def main() -> int:
    settings = StrikerSettings()

    print(f"Field: {settings.field}")
    print(f"Dry run: {settings.dry_run}")
    print(f"Transport: {settings.transport}")
    print(f"Release method: {settings.release_method}")

    # Validate field profile
    print(f"\nValidating field profile '{settings.field}'...")
    try:
        profile = load_field_profile(settings.field)
        print(f"  Name: {profile.name}")
        print(f"  Scan altitude: {profile.scan.altitude_m}m, spacing: {profile.scan.spacing_m}m")
        print(f"  Boundary vertices: {len(profile.boundary.polygon)}")
        print(f"  Safety buffer: {profile.safety_buffer_m}m")
        print("  OK")
    except (ConfigError, Exception) as exc:
        print(f"  FAILED: {exc}")
        return 1

    print("\nAll checks passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
