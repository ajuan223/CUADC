"""Unit conversion utilities."""

from __future__ import annotations

import math


def deg_to_rad(deg: float) -> float:
    return math.radians(deg)


def rad_to_deg(rad: float) -> float:
    return math.degrees(rad)


def mps_to_kmh(mps: float) -> float:
    return mps * 3.6


def kmh_to_mps(kmh: float) -> float:
    return kmh / 3.6


def meters_to_feet(m: float) -> float:
    return m * 3.28084


def feet_to_meters(ft: float) -> float:
    return ft / 3.28084
